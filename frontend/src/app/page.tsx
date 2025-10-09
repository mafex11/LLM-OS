"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Send, Bot, User, Loader2, Play, Settings, Monitor, ChevronRight, Cpu, CheckCircle, XCircle, RefreshCw, Lightbulb, Mic, Plus, MessageSquare, Trash2, Menu, X, MoreVertical, Edit2 } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  workflowSteps?: WorkflowStep[]
}

interface WorkflowStep {
  type: "thinking" | "reasoning" | "tool_use" | "tool_result" | "status"
  message: string
  timestamp: Date
  status?: string
  actionName?: string
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
}

interface SystemStatus {
  agent_ready: boolean
  running_programs: Array<{ name: string; title: string; id: string }>
  memory_stats: any
  performance_stats: any
}

export default function Home() {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([
    {
      id: "1",
      title: "New Chat",
      messages: [],
      createdAt: new Date()
    }
  ])
  const [currentSessionId, setCurrentSessionId] = useState("1")
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowStep[]>([])
  const [showSidebar, setShowSidebar] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null)
  const [newChatTitle, setNewChatTitle] = useState("")
  const workflowRef = useRef<WorkflowStep[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const currentSession = chatSessions.find(s => s.id === currentSessionId)
  const messages = currentSession?.messages || []

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, currentWorkflow])

  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/status")
      if (response.ok) {
        const data = await response.json()
        setSystemStatus(data)
      }
    } catch (error) {
      console.error("Failed to fetch system status:", error)
    }
  }

  const updateSessionMessages = (sessionId: string, newMessages: Message[]) => {
    setChatSessions(prev => prev.map(session => 
      session.id === sessionId 
        ? { 
            ...session, 
            messages: newMessages,
            title: newMessages.length > 0 && session.title === "New Chat" 
              ? newMessages[0].content.slice(0, 30) + (newMessages[0].content.length > 30 ? "..." : "")
              : session.title
          }
        : session
    ))
  }

  const createNewChat = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [],
      createdAt: new Date()
    }
    setChatSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newSession.id)
  }

  const deleteChat = (sessionId: string) => {
    if (chatSessions.length === 1) return // Don't delete the last chat
    setChatSessions(prev => prev.filter(s => s.id !== sessionId))
    if (currentSessionId === sessionId) {
      setCurrentSessionId(chatSessions[0].id === sessionId ? chatSessions[1].id : chatSessions[0].id)
    }
  }

  const openRenameDialog = (sessionId: string) => {
    const session = chatSessions.find(s => s.id === sessionId)
    if (session) {
      setRenamingSessionId(sessionId)
      setNewChatTitle(session.title)
      setRenameDialogOpen(true)
    }
  }

  const renameChat = () => {
    if (renamingSessionId && newChatTitle.trim()) {
      setChatSessions(prev => prev.map(session => 
        session.id === renamingSessionId 
          ? { ...session, title: newChatTitle.trim() }
          : session
      ))
      setRenameDialogOpen(false)
      setRenamingSessionId(null)
      setNewChatTitle("")
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    const newMessages = [...messages, userMessage]
    updateSessionMessages(currentSessionId, newMessages)
    setInput("")
    setIsLoading(true)
    setCurrentWorkflow([])
    workflowRef.current = []

    try {
      const response = await fetch("http://localhost:8000/api/query/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: userMessage.content,
          use_vision: false,
        }),
      })

      if (!response.ok) throw new Error("Failed to send query")

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error("No reader available")

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === "thinking" || data.type === "reasoning" || data.type === "tool_use" || data.type === "tool_result" || data.type === "status") {
                const step: WorkflowStep = {
                  type: data.type,
                  message: data.data.message,
                  timestamp: new Date(data.timestamp),
                  status: data.data.status,
                  actionName: data.data.action_name
                }
                workflowRef.current = [...workflowRef.current, step]
                setCurrentWorkflow((prev) => [...prev, step])
              } else if (data.type === "response") {
                const responseMessage: Message = {
                  role: "assistant",
                  content: data.data.message,
                  timestamp: new Date(data.timestamp),
                  workflowSteps: [...workflowRef.current]
                }
                updateSessionMessages(currentSessionId, [...newMessages, responseMessage])
                setCurrentWorkflow([])
                workflowRef.current = []
              } else if (data.type === "error") {
                const errorMessage: Message = {
                  role: "assistant",
                  content: `Error: ${data.data.message}`,
                  timestamp: new Date(data.timestamp),
                  workflowSteps: [...workflowRef.current]
                }
                updateSessionMessages(currentSessionId, [...newMessages, errorMessage])
                setCurrentWorkflow([])
                workflowRef.current = []
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e)
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMsg: Message = {
        role: "assistant",
        content: "Failed to process query. Please make sure the API server is running.",
        timestamp: new Date(),
      }
      updateSessionMessages(currentSessionId, [...newMessages, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className={`${showSidebar ? 'w-64' : 'w-0'} transition-all duration-300 border-r bg-muted/30 flex flex-col overflow-hidden`}>
        {showSidebar && (
          <>
            {/* Sidebar Header */}
            <div className="p-4 border-b">
              <Button onClick={createNewChat} className="w-full justify-start gap-2" variant="outline">
                <Plus className="h-4 w-4" />
                New Chat
              </Button>
            </div>

            {/* Chat History */}
            <ScrollArea className="flex-1 px-2 py-2">
              <div className="space-y-1">
                {chatSessions.map((session) => (
                  <div
                    key={session.id}
                    className={`group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                      currentSessionId === session.id
                        ? "bg-muted"
                        : "hover:bg-muted/50"
                    }`}
                  >
                    <MessageSquare className="h-4 w-4 flex-shrink-0" />
                    <div 
                      className="flex-1 truncate cursor-pointer"
                      onClick={() => setCurrentSessionId(session.id)}
                    >
                      {session.title}
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openRenameDialog(session.id)}>
                          <Edit2 className="h-3 w-3 mr-2" />
                          Rename
                        </DropdownMenuItem>
                        {chatSessions.length > 1 && (
                          <DropdownMenuItem 
                            onClick={() => deleteChat(session.id)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-3 w-3 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Sidebar Footer */}
            <div className="border-t p-2">
              <Button
                variant="ghost"
                className="w-full justify-start gap-2"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="h-4 w-4" />
                Settings
              </Button>
              {systemStatus && (
                <div className="px-3 py-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <div className={`h-2 w-2 rounded-full ${systemStatus.agent_ready ? 'bg-green-500' : 'bg-red-500'}`} />
                    {systemStatus.agent_ready ? 'Agent Ready' : 'Agent Not Ready'}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b px-4 py-3 flex items-center justify-between bg-background">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <div className="flex items-center gap-2">
              <Bot className="h-6 w-6" />
              <h1 className="text-lg font-semibold">Windows-Use AI Agent</h1>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="border-b bg-muted/30 p-4">
            <div className="max-w-3xl mx-auto space-y-3">
              <h3 className="font-semibold flex items-center gap-2">
                <Monitor className="h-4 w-4" />
                System Status
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">API Server:</span>
                  <p className="font-medium">http://localhost:8000</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Running Programs:</span>
                  <p className="font-medium">{systemStatus?.running_programs?.length || 0}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Chat Area */}
        <ScrollArea className="flex-1 px-4" ref={scrollRef}>
          <div className="max-w-3xl mx-auto py-8">
            {messages.length === 0 && !isLoading && (
              <div className="text-center py-12">
                <Bot className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
                <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
                <p className="text-muted-foreground">
                  Ask me to automate Windows tasks, open applications, or control your system.
                </p>
              </div>
            )}

            <div className="space-y-6">
              {messages.map((message, index) => (
                <div key={index} className="group">
                  <div className={`flex gap-4 ${message.role === "user" ? "" : "bg-muted/30 -mx-4 px-4 py-6"}`}>
                    <div className="flex-shrink-0 mt-1">
                      {message.role === "user" ? (
                        <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                          <User className="h-5 w-5 text-primary-foreground" />
                        </div>
                      ) : (
                        <div className="h-8 w-8 rounded-full bg-purple-500 flex items-center justify-center">
                          <Bot className="h-5 w-5 text-white" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 space-y-2 min-w-0">
                      <div className="prose dark:prose-invert max-w-none">
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                      </div>

                      {message.role === "assistant" && message.workflowSteps && message.workflowSteps.length > 0 && (
                        <Collapsible defaultOpen={false}>
                          <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors mt-2">
                            <ChevronRight className="h-3 w-3 transition-transform data-[state=open]:rotate-90" />
                            <Cpu className="h-3 w-3" />
                            <span>View {message.workflowSteps.length} workflow steps</span>
                          </CollapsibleTrigger>
                          <CollapsibleContent className="mt-3">
                            <div className="space-y-2 pl-4 border-l-2 border-muted">
                              {message.workflowSteps.map((step, stepIndex) => (
                                <div key={stepIndex} className="flex items-start gap-2 text-xs">
                                  <div className="flex-shrink-0 mt-0.5">
                                    {step.type === "thinking" && <Loader2 className="h-3 w-3 text-blue-500" />}
                                    {step.type === "reasoning" && <Lightbulb className="h-3 w-3 text-yellow-500" />}
                                    {step.type === "tool_use" && <Play className="h-3 w-3 text-green-500" />}
                                    {step.type === "tool_result" && step.status === "Completed" && (
                                      <CheckCircle className="h-3 w-3 text-green-500" />
                                    )}
                                    {step.type === "tool_result" && step.status === "Failed" && (
                                      <XCircle className="h-3 w-3 text-red-500" />
                                    )}
                                    {step.type === "status" && <RefreshCw className="h-3 w-3 text-gray-500" />}
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-muted-foreground">{step.message}</p>
                                    {step.actionName && (
                                      <Badge variant="outline" className="mt-1 text-xs">
                                        {step.actionName}
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="bg-muted/30 -mx-4 px-4 py-6">
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 mt-1">
                      <div className="h-8 w-8 rounded-full bg-purple-500 flex items-center justify-center">
                        <Bot className="h-5 w-5 text-white" />
                      </div>
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="font-medium">Thinking...</span>
                      </div>
                      {currentWorkflow.length > 0 && (() => {
                        const latestStep = currentWorkflow[currentWorkflow.length - 1]
                        return (
                          <div className="flex items-start gap-2 text-xs pl-6">
                            <Loader2 className="h-3 w-3 animate-spin text-purple-500 mt-0.5" />
                            <p className="text-muted-foreground">{latestStep.message}</p>
                          </div>
                        )
                      })()}
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t bg-background p-4">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-center gap-2">
              <Input
                placeholder="Message Windows-Use AI Agent..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                disabled={isLoading}
                className="pr-24"
              />
              <div className="absolute right-2 flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  disabled={isLoading}
                  title="Voice input (coming soon)"
                >
                  <Mic className="h-4 w-4" />
                </Button>
                <Button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  size="sm"
                  className="h-8 w-8 p-0"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Chat</DialogTitle>
            <DialogDescription>
              Enter a new name for this chat session.
            </DialogDescription>
          </DialogHeader>
          <Input
            value={newChatTitle}
            onChange={(e) => setNewChatTitle(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && renameChat()}
            placeholder="Chat name"
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={renameChat}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
