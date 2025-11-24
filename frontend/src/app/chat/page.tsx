"use client"

import React, { useState, useEffect, useRef, Suspense, useMemo, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { 
  Navigation03Icon, 
  BotIcon, 
  UserIcon, 
  Loading01Icon, 
  PlayIcon, 
  Settings01Icon, 
  ArrowRight01Icon, 
  CpuIcon, 
  CheckmarkCircle01Icon, 
  CancelCircleIcon, 
  Loading02Icon, 
  BulbIcon, 
  VoiceIcon, 
  PlusSignIcon, 
  MessageMultiple02Icon,
  Delete02Icon, 
  SidebarLeft01Icon, 
  SidebarRight01Icon, 
  MoreVerticalIcon, 
  PencilEdit02Icon,
  Home01Icon,
  Cancel01Icon,
  AiBrain01Icon,
  TimeScheduleIcon,
  ComputerIcon
} from "hugeicons-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useRouter, useSearchParams } from "next/navigation"
import { useApiKeys } from "@/contexts/ApiKeyContext"
import { motion, AnimatePresence } from "framer-motion"
import { AppSidebar } from "@/components/layout/Sidebar"
// Avoid next/image in packaged Electron static export; use plain <img>
import { TextGenerateEffect } from "@/components/ui/text-generate-effect"
import { useToast } from "@/hooks/use-toast"
import { getApiUrlSync } from "@/lib/api"

interface Message {
  id?: string
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

interface ChatInputProps {
  isListening: boolean
  isSpeaking: boolean
  isLoading: boolean
  input: string
  setInput: (value: string) => void
  sendMessage: () => void
  handleMicClick: () => void
  inputRef: React.RefObject<HTMLInputElement>
  currentRequestId: string | null
  stopRequested: boolean
  setStopRequested: (value: boolean) => void
}

function ChatInput({ isListening, isSpeaking, isLoading, input, setInput, sendMessage, handleMicClick, inputRef, currentRequestId, stopRequested, setStopRequested }: ChatInputProps) {
  return (
    <div className="flex items-center gap-3">
      <AnimatePresence mode="wait">
        {!isListening ? (
          <motion.div key="normal-input" initial={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.8 }} transition={{ duration: 0.3, ease: "easeInOut" }} className="flex items-center gap-3 w-full">
            <motion.div initial={{ opacity: 1, scale: 1 }} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.2 }}>
              <Button variant="ghost" size="sm" className={`h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border hover:shadow-lg hover:shadow-red-500/20 transition-shadow duration-300 ease-in-out ${isListening ? 'border-red-500/50 bg-red-500/10' : isSpeaking ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/20 hover:border-white/30'}`} disabled={isLoading} title={isListening ? "Stop voice mode" : "Start voice mode (say 'yuki' + command)"} onClick={handleMicClick}>
                {isListening ? (<motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 1, repeat: Infinity }}><VoiceIcon size={24} className="text-red-500" /></motion.div>) : isSpeaking ? (<motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 0.8, repeat: Infinity }}><VoiceIcon size={24} className="text-blue-500" /></motion.div>) : (<VoiceIcon size={24} className="text-white" />)}
              </Button>
            </motion.div>
            <motion.div className="flex-1 relative" initial={{ opacity: 1, x: 0 }} exit={{ opacity: 0, scale: 0.8 }} transition={{ duration: 0.3, ease: "easeInOut" }}>
              <Input ref={inputRef} placeholder="What can I do for you?" value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()} disabled={isLoading} className="w-full text-base sm:text-lg bg-black/30 border border-white/20 text-gray-100 placeholder:text-gray-500 rounded-3xl shadow-lg focus-visible:ring-0 focus-visible:ring-offset-0 focus:outline-none focus:ring-0 h-12 sm:h-14 backdrop-blur-sm hover:border-white/30 hover:shadow-lg hover:shadow-red-500/20 transition-shadow duration-300 ease-in-out" />
            </motion.div>
            <motion.div initial={{ opacity: 1, x: 0 }} exit={{ opacity: 0, scale: 0.8 }} transition={{ duration: 0.3, ease: "easeInOut" }}>
              {isLoading ? (
                <Button onClick={() => { if (!stopRequested && currentRequestId) { fetch(getApiUrlSync("/api/query/stop"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: currentRequestId }) }).catch(console.error); setStopRequested(true) } }} variant="ghost" size="sm" className="h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border border-red-500/50"><span className="flex items-center justify-center w-full h-full text-red-500"><Cancel01Icon size={28} /></span></Button>
              ) : (
                <Button onClick={sendMessage} disabled={!input.trim()} variant="ghost" size="sm" className="h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border border-white/20 hover:border-white/30 hover:shadow-lg hover:shadow-red-500/20 transition-shadow duration-300 ease-in-out"><span className="flex items-center justify-center w-full h-full"><Navigation03Icon size={36} /></span></Button>
              )}
            </motion.div>
          </motion.div>
        ) : (
          <motion.div key="listening-input" className="flex-1 relative" initial={{ width: "48px", opacity: 0 }} animate={{ width: "100%", opacity: 1 }} exit={{ opacity: 0, scale: 0.8 }} transition={{ duration: 0.3, ease: "easeInOut" }}>
            <motion.div className="w-full text-base sm:text-lg bg-black/30 border border-white/20 text-gray-100 rounded-full shadow-lg h-12 sm:h-14 backdrop-blur-sm flex items-center justify-between px-4" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.2 }}>
              <motion.div className="flex items-center" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3, delay: 0.4 }}>
                <motion.div className="flex items-center justify-center w-8 h-8 bg-red-500/20 rounded-lg  mr-2" animate={{ scale: [1, 1.1, 1], opacity: [0.8, 1, 0.8] }} transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}>
                  <VoiceIcon size={20} className="text-red-500" />
                </motion.div>
                <span className="text-gray-100 font-medium">Say &quot;yuki&quot; followed by your command...</span>
              </motion.div>
              <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3, delay: 0.5 }}>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-full backdrop-blur-sm border border-white/20 hover:bg-black/20 hover:border-white/30" onClick={handleMicClick} title="Stop listening">
                  <Cancel01Icon size={16} className="text-white" />
                </Button>
              </motion.div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function WorkflowSteps({ workflowSteps }: { workflowSteps: WorkflowStep[] }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setIsOpen(!isOpen)} className="flex items-center gap-2 text-xs text-white hover:text-white transition-colors">
        <motion.div animate={{ rotate: isOpen ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ArrowRight01Icon size={12} className="text-white" />
        </motion.div>
        <CpuIcon size={12} className="text-white" />
        <span className="text-white">View {workflowSteps.length} workflow steps</span>
      </button>
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: "easeInOut", opacity: { duration: 0.2 } }} className="mt-3 overflow-hidden">
            <div className="space-y-2 p-2 pl-4 border-l-2 border-muted max-h-72 overflow-y-auto">
              <AnimatePresence mode="popLayout">
                {workflowSteps.map((step, stepIndex) => (
                  <motion.div key={stepIndex} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2, delay: stepIndex * 0.05, ease: "easeOut" }} className="flex items-start gap-2 text-xs">
                    <div className="flex-shrink-0 mt-0.5">
                      {step.type === "thinking" && <Loading01Icon size={12} className="text-white" />}
                      {step.type === "reasoning" && <BulbIcon size={12} className="text-white" />}
                      {step.type === "tool_use" && <PlayIcon size={12} className="text-white" />}
                      {step.type === "tool_result" && step.status === "Completed" && (<CheckmarkCircle01Icon size={12} className="text-white" />)}
                      {step.type === "tool_result" && step.status === "Failed" && (<CancelCircleIcon size={12} className="text-white" />)}
                      {step.type === "status" && <Loading02Icon size={12} className="text-white" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-white">{step.message}</p>
                      {step.actionName && (<Badge variant="outline" className="mt-1 text-xs">{step.actionName}</Badge>)}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ChatContent() {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const router = useRouter()
  const searchParams = useSearchParams()
  const { getApiKey } = useApiKeys()
  const { toast } = useToast()
  const [currentSessionId, setCurrentSessionId] = useState("")
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null)
  const [stopRequested, setStopRequested] = useState(false)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowStep[]>([])
  const [showSidebar, setShowSidebar] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("sidebarOpen")
      return saved === "true"
    }
    return false
  })
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  
  // Save sidebar state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sidebarOpen", String(showSidebar))
    }
  }, [showSidebar])
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null)
  const [newChatTitle, setNewChatTitle] = useState("")
  const [taskExecuted, setTaskExecuted] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [voiceMode, setVoiceMode] = useState(false)
  const [showVoiceInstructions, setShowVoiceInstructions] = useState(false)
  const [newlyGeneratedMessageIds, setNewlyGeneratedMessageIds] = useState<Set<string>>(new Set())
  const [scheduledCount, setScheduledCount] = useState<number>(0)
  const [scheduledFlag, setScheduledFlag] = useState<boolean>(false)
  const [mounted, setMounted] = useState(false)
  const [didCreateOnLoad, setDidCreateOnLoad] = useState(false)
  const workflowRef = useRef<WorkflowStep[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const queryStartSoundRef = useRef<HTMLAudioElement | null>(null)
  const taskCompleteSoundRef = useRef<HTMLAudioElement | null>(null)
  const previousIsLoadingRef = useRef(false)

  const generateUniqueSessionId = () => {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${performance.now()}`
  }

  const currentSession = chatSessions.find(s => s.id === currentSessionId)
  const messages = useMemo(() => currentSession?.messages || [], [currentSession?.messages])

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return
    queryStartSoundRef.current = new Audio("/noti1.mp3")
    queryStartSoundRef.current.preload = "auto"
    taskCompleteSoundRef.current = new Audio("/noti2.mp3")
    taskCompleteSoundRef.current.preload = "auto"
    return () => {
      queryStartSoundRef.current = null
      taskCompleteSoundRef.current = null
    }
  }, [])

  useEffect(() => {
    const wasLoading = previousIsLoadingRef.current
    // Check if notification sounds are enabled
    const soundsEnabled = typeof window !== "undefined" 
      ? localStorage.getItem("notificationSoundsEnabled") !== "false"
      : true
    
    if (isLoading && !wasLoading) {
      const sound = queryStartSoundRef.current
      if (sound && soundsEnabled) {
        sound.currentTime = 0
        sound.play().catch(() => {})
      }
    } else if (!isLoading && wasLoading) {
      const sound = taskCompleteSoundRef.current
      if (sound && soundsEnabled) {
        sound.currentTime = 0
        sound.play().catch(() => {})
      }
    }
    previousIsLoadingRef.current = isLoading
  }, [isLoading])

  useEffect(() => {
    const initializeChat = async () => {
      try {
        const sessionId = 'default'
    const saved = localStorage.getItem('chatSessions')
        let existingSessions: ChatSession[] = []
    if (saved) {
          const parsed = JSON.parse(saved)
          existingSessions = parsed.map((session: any, index: number) => ({
            ...session,
            id: session.id || `${Date.now()}-${index}-${Math.random().toString(36).substr(2, 9)}`,
            createdAt: new Date(session.createdAt),
            messages: session.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
              workflowSteps: msg.workflowSteps?.map((step: any) => ({
                ...step,
                timestamp: new Date(step.timestamp)
              }))
        }))
      }))
    }
        const existingSession = existingSessions.find(s => s.id === sessionId)
        if (existingSession) {
          setChatSessions(existingSessions)
          setCurrentSessionId(sessionId)
        } else {
          const newSession: ChatSession = {
            id: sessionId,
            title: "New Chat",
            messages: [],
            createdAt: new Date()
          }
          try {
            const response = await fetch(`http://127.0.0.1:8000/api/conversation/${sessionId}`)
            if (response.ok) {
              const data = await response.json()
              if (data.conversation && data.conversation.length > 0) {
                const serverMessages = data.conversation.map((msg: any) => {
                  try {
                    return {
                      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                      role: msg.role,
                      content: msg.content || '',
                      timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
                      workflowSteps: msg.workflowSteps?.map((step: any) => ({
                        ...step,
                        timestamp: step.timestamp ? new Date(step.timestamp) : new Date()
                      }))
                    }
                  } catch (e) {
                    console.error('Error parsing message:', e, msg)
                    return {
                      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                      role: msg.role || 'user',
                      content: msg.content || '',
                      timestamp: new Date(),
                      workflowSteps: undefined
                    }
                  }
                })
                newSession.messages = serverMessages
                newSession.title = serverMessages.length > 0 
                  ? serverMessages[0].content.slice(0, 30) + (serverMessages[0].content.length > 30 ? "..." : "")
                  : "New Chat"
              }
            } else {
              console.warn('Failed to fetch conversation:', response.status, response.statusText)
            }
          } catch (error) {
            console.error('Error fetching conversation:', error)
          }
          const updatedSessions = [newSession, ...existingSessions]
          setChatSessions(updatedSessions)
          setCurrentSessionId(sessionId)
          localStorage.setItem('chatSessions', JSON.stringify(updatedSessions))
        }
        setTimeout(() => { inputRef.current?.focus() }, 100)
      } catch (error) {
        console.error('Error initializing chat:', error)
        const sessionId = 'default'
        const initialSession: ChatSession = { id: sessionId, title: "New Chat", messages: [], createdAt: new Date() }
        setChatSessions([initialSession])
        setCurrentSessionId(sessionId)
        setTimeout(() => { inputRef.current?.focus() }, 100)
  }
    }
    if (!isInitialized) {
      initializeChat()
      setIsInitialized(true)
    }
  }, [isInitialized])

  const stopVoiceMode = useCallback(async () => {
    console.log('[Voice Mode] stopVoiceMode called')
    try {
      console.log('[Voice Mode] Sending stop request to backend...')
      const response = await fetch("http://127.0.0.1:8000/api/voice/stop", { method: "POST" })
      console.log('[Voice Mode] Stop response status:', response.status, response.ok)
      const data = await response.json().catch(() => ({}))
      console.log('[Voice Mode] Stop response data:', data)
      setIsListening(false)
      setIsSpeaking(false)
      setShowVoiceInstructions(false)
      setIsLoading(false)
      setCurrentWorkflow([])
      workflowRef.current = []
      console.log('[Voice Mode] State updated: listening=false, speaking=false, instructions=false, loading=false')
    } catch (error) {
      console.error('[Voice Mode] Error stopping voice mode:', error)
    }
  }, [])

  // Stop all running tasks (query and voice mode) when switching chats
  const stopAllRunningTasks = useCallback(async () => {
    // Stop current query if running
    if (currentRequestId && !stopRequested) {
      setStopRequested(true)
      try {
        await fetch(getApiUrlSync("/api/query/stop"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ request_id: currentRequestId })
        })
      } catch (error) {
        console.error("Error stopping query:", error)
      }
    }
    
    // Stop voice mode if active
    if (voiceMode) {
      try {
        await stopVoiceMode()
        setVoiceMode(false)
      } catch (error) {
        console.error("Error stopping voice mode:", error)
      }
    }
    
    // Reset loading and workflow states
    setIsLoading(false)
    setCurrentWorkflow([])
    workflowRef.current = []
    setCurrentRequestId(null)
    setStopRequested(false)
  }, [currentRequestId, stopRequested, voiceMode, stopVoiceMode])

  const createNewChat = useCallback(async () => {
    // Stop all running tasks before creating new chat
    await stopAllRunningTasks()
    
    const newSessionId = generateUniqueSessionId()
    const newSession: ChatSession = { id: newSessionId, title: "New Chat", messages: [], createdAt: new Date() }
    setChatSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newSessionId)
    try { const s = [newSession, ...chatSessions].filter(s => s.messages.length > 0); localStorage.setItem('chatSessions', JSON.stringify(s)) } catch {}
  }, [stopAllRunningTasks, chatSessions])

  // On first load only, create a fresh empty chat session
  useEffect(() => {
    if (isInitialized && !didCreateOnLoad) {
      setDidCreateOnLoad(true)
      const newSessionId = generateUniqueSessionId()
      const newSession: ChatSession = { id: newSessionId, title: "New Chat", messages: [], createdAt: new Date() }
      setChatSessions(prev => [newSession, ...prev])
      setCurrentSessionId(newSessionId)
    }
  }, [isInitialized, didCreateOnLoad])

  useEffect(() => {
    if (isInitialized && chatSessions.length > 0) {
      const hasMessages = chatSessions.some(session => session.messages.length > 0)
      if (hasMessages) {
        saveSessionsToStorage(chatSessions)
      } else {
        try { localStorage.removeItem('chatSessions') } catch {}
      }
    }
  }, [chatSessions, isInitialized])

  // Only auto-scroll when messages change to avoid ref churn in ScrollArea during workflow streaming
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    if (newlyGeneratedMessageIds.size > 0) {
      const timer = setTimeout(() => { setNewlyGeneratedMessageIds(new Set()) }, 3000)
      return () => clearTimeout(timer)
    }
  }, [newlyGeneratedMessageIds])

  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const [voiceModeStarting, setVoiceModeStarting] = useState(false)
  const [inputPosition, setInputPosition] = useState<'centered' | 'bottom'>('centered')
  useEffect(() => { setInputPosition(messages.length === 0 ? 'centered' : 'bottom') }, [currentSessionId, messages.length])
  
  // Hero subtitle phrases; pick one randomly each page load
  const heroPhrases = useMemo(() => [
    "How can I help you today?",
    "Tell me your goal for today",
    "What's gonna be today?",
    "Let's acheive some productivity!",
    "Let me handle your repetitive works!",
    "What task is on your mind right now?",
    "Ready to make progress? Tell me where to start.",
    "What's the first thing we should tackle today?",
    "I'm here to turn your ideas into actions.",
    "Let’s smash some goals together!",
    "What do you want to focus on next?",
    "Tell me what’s slowing you down, and I’ll handle it.",
    "What can we make easier today?",
    "Got a mission? I'm ready to assist.",
    "Let’s turn your to-dos into ta-das.",
    "Need a boost? I’ve got your back.",
    "Point me in the right direction, and I’ll take it from there.",
    "Let’s get you closer to your dreams today.",
    "What's the next milestone we’re chasing?",
  ], [])
  const [heroText, setHeroText] = useState(heroPhrases[0])
  useEffect(() => {
    const idx = Math.floor(Math.random() * heroPhrases.length)
    setHeroText(heroPhrases[idx])
  }, [heroPhrases])

  const updateSessionMessages = useCallback((sessionId: string, newMessages: Message[]) => {
    setChatSessions(prev => prev.map(session => session.id === sessionId ? { ...session, messages: newMessages, title: newMessages.length > 0 && session.title === "New Chat" ? newMessages[0].content.slice(0, 30) + (newMessages[0].content.length > 30 ? "..." : "") : session.title } : session))
    saveConversationToServer(sessionId, newMessages)
  }, [])

  const executeTask = useCallback(async (taskContent: string) => {
    if (!taskContent.trim() || isLoading) return
    setInputPosition('bottom')
    const userMessage: Message = { id: `${Date.now()}-user-${Math.random().toString(36).substr(2, 9)}`, role: "user", content: taskContent, timestamp: new Date() }
    const newMessages = [...messages, userMessage]
    updateSessionMessages(currentSessionId, newMessages)
    setInput("")
    setIsLoading(true)
    setCurrentWorkflow([])
    workflowRef.current = []
    setStopRequested(false)
    setCurrentRequestId(null)
    try {
      const conversationHistory = messages.map(msg => ({ role: msg.role, content: msg.content, timestamp: msg.timestamp.toISOString() }))
      const response = await fetch(getApiUrlSync("/api/query/stream"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: userMessage.content, use_vision: false, conversation_history: conversationHistory, api_key: getApiKey('google_api_key') }) })
      if (!response.ok) {
        let errorText = ""
        try {
          errorText = await response.text()
        } catch {}
        const normalized = errorText.toLowerCase()
        if (response.status === 429 || normalized.includes("quota") || normalized.includes("rate limit")) {
          throw new Error("QUOTA_EXCEEDED")
        }
        throw new Error(errorText || "Failed to send query")
      }
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error("No reader available")
      while (true) {
        const { done, value } = await reader.read(); if (done) break
        const lines = new TextDecoder().decode(value).split("\n")
        for (const line of lines) {
          if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6))
              if (data.type === "start") { const rid = data?.data?.request_id as string | undefined; if (rid) setCurrentRequestId(rid) }
            if (["thinking","reasoning","tool_use","tool_result","status"].includes(data.type)) {
                const step: WorkflowStep = { type: data.type, message: data.data.message, timestamp: new Date(data.timestamp), status: data.data.status, actionName: data.data.action_name }
              workflowRef.current = [...workflowRef.current, step]
              setCurrentWorkflow(prev => [...prev, step])
              if (data.type === 'tool_use' && (data.data?.tool_name || '').toLowerCase().includes('schedule')) {
                setScheduledFlag(true)
              }
              } else if (data.type === "response") {
                const messageId = `${Date.now()}-assistant-${Math.random().toString(36).substr(2, 9)}`
                const responseMessage: Message = { id: messageId, role: "assistant", content: data.data.message, timestamp: new Date(data.timestamp), workflowSteps: [...workflowRef.current] }
                setNewlyGeneratedMessageIds(prev => new Set([...prev, messageId]))
                updateSessionMessages(currentSessionId, [...newMessages, responseMessage])
                setCurrentWorkflow([])
                workflowRef.current = []
              } else if (data.type === "error") {
                const messageId = `${Date.now()}-error-${Math.random().toString(36).substr(2, 9)}`
                const rawMessage: string = data?.data?.message || ""
                const isUserStop = (rawMessage || "").toLowerCase() === "execution stopped by user"
                const normalized = rawMessage.toLowerCase()
                const isQuotaError = normalized.includes("quota") || normalized.includes("rate limit") || normalized.includes("resourceexhausted")
                const errorContent = isUserStop
                  ? "Execution stopped by user"
                  : isQuotaError
                    ? "Quota exhausted for the Gemini API. Please wait and try again, or upgrade your plan."
                    : `Error: ${rawMessage}`
                const errorMessage: Message = { id: messageId, role: "assistant", content: errorContent, timestamp: new Date(data.timestamp), workflowSteps: [...workflowRef.current] }
                setNewlyGeneratedMessageIds(prev => new Set([...prev, messageId]))
                updateSessionMessages(currentSessionId, [...newMessages, errorMessage])
                setCurrentWorkflow([])
                workflowRef.current = []
            }
          } catch {}
        }
        }
      }
    } catch (error) {
      const messageId = `${Date.now()}-error-${Math.random().toString(36).substr(2, 9)}`
      let content = "Failed to process query. Please make sure the API server is running."
      if (error instanceof Error) {
        const normalized = error.message.toLowerCase()
        if (normalized === "quota_exceeded" || normalized.includes("quota") || normalized.includes("rate limit")) {
          content = "Quota exhausted for the Gemini API. Please wait a bit and try again."
        }
      }
      const errorMsg: Message = { id: messageId, role: "assistant", content, timestamp: new Date() }
      setNewlyGeneratedMessageIds(prev => new Set([...prev, messageId]))
      updateSessionMessages(currentSessionId, [...newMessages, errorMsg])
    } finally {
      setIsLoading(false)
      setCurrentRequestId(null)
      setStopRequested(false)
    }
  }, [isLoading, currentSessionId, messages, updateSessionMessages, getApiKey])

  useEffect(() => {
    if (!voiceMode) return
    const pollVoiceStatus = async () => { try { const r = await fetch("http://127.0.0.1:8000/api/voice/status"); if (r.ok) { const s = await r.json(); setIsListening(s.is_listening); setIsSpeaking(s.is_speaking) } } catch {} }
    const pollVoiceConversation = async () => { try { const r = await fetch("http://127.0.0.1:8000/api/voice/conversation"); if (r.ok) { const d = await r.json(); if (d.conversation && d.conversation.length > 0) { const voiceMessages = d.conversation.map((m: any) => ({ role: m.role, content: m.content, timestamp: new Date(m.timestamp * 1000), workflowSteps: m.workflowSteps ? m.workflowSteps.map((s: any) => ({ type: s.type, message: s.message, timestamp: new Date(s.timestamp * 1000), status: s.status, actionName: s.actionName })) : undefined })); const latestPlaceholder = [...voiceMessages].reverse().find((m: any) => m.role === 'assistant' && (!m.content || m.content.trim() === '') && m.workflowSteps && m.workflowSteps.length > 0); if (latestPlaceholder) { const steps: WorkflowStep[] = latestPlaceholder.workflowSteps.map((s: any) => ({ type: s.type, message: s.message, timestamp: new Date(s.timestamp), status: s.status, actionName: s.actionName })); setCurrentWorkflow(steps); setIsLoading(true) } const filtered = voiceMessages.filter((m: any) => !(m.role === 'assistant' && (!m.content || m.content.trim() === ''))); const newMsgs = filtered.filter((vm: any) => !messages.some(em => (em.role === vm.role && em.content === vm.content))); if (newMsgs.length > 0) { updateSessionMessages(currentSessionId, [...messages, ...newMsgs]); if (newMsgs.some((m: any) => m.role === 'assistant' && m.content && m.content.trim() !== '')) { setCurrentWorkflow([]); setIsLoading(false) } } } } } catch {} }
    const sInt = setInterval(pollVoiceStatus, 1000)
    const cInt = setInterval(pollVoiceConversation, 2000)
    return () => { clearInterval(sInt); clearInterval(cInt) }
  }, [voiceMode, currentSessionId, messages, updateSessionMessages])

  useEffect(() => {
    const task = searchParams.get('task')
    if (task && !taskExecuted && !isLoading && isInitialized && currentSessionId) {
      setTaskExecuted(true)
      setInput(task)
      setTimeout(() => { executeTask(task) }, 100)
    }
  }, [searchParams, taskExecuted, isLoading, isInitialized, currentSessionId, executeTask])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && event.key === 'V') { event.preventDefault(); if (!voiceMode && !voiceModeStarting) { setVoiceMode(true) } else if (voiceMode) { setVoiceMode(false) } }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => { document.removeEventListener('keydown', handleKeyDown) }
  }, [voiceMode, voiceModeStarting, toast])

  // Poll scheduled tasks to show count in header icon
  useEffect(() => {
    const poll = async () => { try { const r = await fetch('http://127.0.0.1:8000/api/scheduled-tasks'); if (r.ok) { const list = await r.json(); const upcoming = (list || []).filter((t: any) => ['scheduled','running'].includes((t.status||'').toLowerCase())); setScheduledCount(upcoming.length) } } catch {} }
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [])

  const fetchSystemStatus = async () => {
    try { const r = await fetch("http://127.0.0.1:8000/api/status"); if (r.ok) setSystemStatus(await r.json()) } catch {}
  }

  const saveSessionsToStorage = (sessions: ChatSession[]) => { try { const s = sessions.filter(session => session.messages.length > 0); localStorage.setItem('chatSessions', JSON.stringify(s)) } catch {} }

  const saveConversationToServer = async (sessionId: string, messages: Message[]) => {
    try {
      const conversation = messages.map(msg => ({ role: msg.role, content: msg.content, timestamp: msg.timestamp.toISOString(), workflowSteps: msg.workflowSteps?.map(step => ({ ...step, timestamp: step.timestamp.toISOString() })) }))
      await fetch(getApiUrlSync(`/api/conversation/${sessionId}`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(conversation) })
    } catch {}
  }

  

  const deleteChat = async (sessionId: string) => {
    try { await fetch(getApiUrlSync(`/api/conversation/${sessionId}`), { method: 'DELETE' }) } catch {}
    const updatedSessions = chatSessions.filter(s => s.id !== sessionId)
    setChatSessions(updatedSessions)
    try { saveSessionsToStorage(updatedSessions) } catch {}
    if (updatedSessions.length > 0) {
      if (currentSessionId === sessionId) { setCurrentSessionId(updatedSessions[0].id) }
    } else {
      createNewChat()
    }
  }

  const openRenameDialog = (sessionId: string) => { const session = chatSessions.find(s => s.id === sessionId); if (session) { setRenamingSessionId(sessionId); setNewChatTitle(session.title); setRenameDialogOpen(true) } }
  const renameChat = () => { if (renamingSessionId && newChatTitle.trim()) { const updated = (prev => prev.map(session => session.id === renamingSessionId ? { ...session, title: newChatTitle.trim() } : session))(chatSessions); setChatSessions(updated); try { saveSessionsToStorage(updated) } catch {}; setRenameDialogOpen(false); setRenamingSessionId(null); setNewChatTitle("") } }
  const sendMessage = async () => { if (!input.trim() || isLoading) return; executeTask(input) }

  const startVoiceMode = useCallback(async () => {
    console.log('[Voice Mode] startVoiceMode called, voiceModeStarting:', voiceModeStarting)
    if (voiceModeStarting) {
      console.log('[Voice Mode] Already starting, returning early')
      return
    }
    setVoiceModeStarting(true)
    console.log('[Voice Mode] Set voiceModeStarting to true')
    try {
      const apiKey = getApiKey('google_api_key')
      console.log('[Voice Mode] API key retrieved:', apiKey ? 'present' : 'missing')
      const requestBody = { api_key: apiKey }
      console.log('[Voice Mode] Sending start request to backend:', { url: getApiUrlSync('/api/voice/start'), method: 'POST', body: requestBody })
      const response = await fetch(getApiUrlSync("/api/voice/start"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(requestBody) })
      console.log('[Voice Mode] Start response status:', response.status, response.ok)
      const responseData = await response.json().catch(() => ({}))
      console.log('[Voice Mode] Start response data:', responseData)
      if (response.ok) {
        console.log('[Voice Mode] Response OK, setting state: listening=true, instructions=true')
        setIsListening(true)
        setShowVoiceInstructions(true)
        toast({ title: "Voice Mode Started", description: "Say 'yuki' followed by your command (e.g., 'yuki, open my calendar')" })
        console.log('[Voice Mode] Toast notification shown')
      } else {
        const errorMsg = responseData.detail || responseData.message || "Failed to start voice mode"
        console.error('[Voice Mode] Response not OK:', errorMsg)
        throw new Error(errorMsg)
      }
    } catch (error) {
      console.error('[Voice Mode] Error in startVoiceMode:', error)
      const errorMessage = error instanceof Error ? error.message : "Could not connect to voice system. Please check your API keys."
      console.log('[Voice Mode] Showing error toast:', errorMessage)
      toast({ title: "Error Starting Voice Mode", description: errorMessage, variant: "destructive" })
      setVoiceMode(false)
      console.log('[Voice Mode] Set voiceMode to false due to error')
    } finally {
      setVoiceModeStarting(false)
      console.log('[Voice Mode] Set voiceModeStarting to false in finally block')
    }
  }, [getApiKey, toast, voiceModeStarting])

  const stopSpeaking = async () => { try { await fetch(getApiUrlSync("/api/tts/stop"), { method: "POST" }) } catch {} }
  const stopCurrentQuery = async () => { if (!currentRequestId || stopRequested) return; setStopRequested(true); try { await fetch(getApiUrlSync("/api/query/stop"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: currentRequestId }) }) } catch {} }
  
  const handleMicClick = async () => {
    console.log('[Voice Mode] handleMicClick called, current state:', { voiceMode, voiceModeStarting, isListening, isSpeaking })
    if (voiceModeStarting) {
      console.log('[Voice Mode] Click ignored - voice mode is already starting')
      return
    }
    try {
      if (!voiceMode) {
        console.log('[Voice Mode] Voice mode is OFF, starting voice mode...')
        await startVoiceMode()
        console.log('[Voice Mode] startVoiceMode completed, setting voiceMode to true')
        setVoiceMode(true)
        console.log('[Voice Mode] voiceMode state set to true')
      } else {
        console.log('[Voice Mode] Voice mode is ON, stopping voice mode...')
        await stopVoiceMode()
        console.log('[Voice Mode] stopVoiceMode completed, setting voiceMode to false')
        setVoiceMode(false)
        console.log('[Voice Mode] voiceMode state set to false')
      }
    } catch (error) {
      console.error('[Voice Mode] Error in handleMicClick:', error)
    }
  }

  return (
    // Gate rendering to avoid Presence/layout effects during hydration
    !mounted ? (
      <div className="flex h-screen w-full bg-black"></div>
    ) : (
    <div className="flex h-screen relative">
      {/* <div
        className="pointer-events-none absolute bottom-0 left-1/2 -translate-x-1/2 rounded-full blur-3xl opacity-80"
        style={{
          width: "100rem",
          height: "100rem",
          background: "radial-gradient(circle, rgba(250,50,50,0.5) 0%, rgba(250,50,50,0.15) 45%, rgba(0,0,0,0) 75%)",
        }}
      /> */}
      {/* <div className="absolute inset-0 z-0" style={{ background: "radial-gradient(125% 25% at 60% 100%, #000000 60%, #2b0707 200%)" }} /> */}
      <div className="relative z-10 w-full h-full">
        <AppSidebar
          isOpen={showSidebar}
          collapsedContent={(
            <>
              <div className="flex items-center justify-center mt-0">
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-transparent" onClick={() => router.push('/chat')} title="Chat">
                  <img src="/logo.svg" alt="Logo" width={36} height={36} className="rounded-full" />
                </Button>
              </div>
              <Button onClick={createNewChat} variant="ghost" size="icon" className="group h-12 w-12 mx-auto mt-4 hover:bg-black/20 border border-white/20 hover:border-white/30 rounded-full">
                <PlusSignIcon size={20} className="group-hover:animate-[spin_3s_linear_infinite]" />
              </Button>
              <div className="flex-1" />
              <div className="mt-auto flex flex-col items-center gap-1 w-full">
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5" onClick={() => router.push("/")}>
                  <Home01Icon size={16} />
                </Button>
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5" onClick={() => router.push('/chat')}>
                  <MessageMultiple02Icon size={16} />
                </Button>
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5" onClick={() => router.push("/activity")}>
                  <ComputerIcon size={16} />
                </Button>
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5" onClick={() => router.push("/scheduled")}>
                  <TimeScheduleIcon size={16} />
                </Button>
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5" onClick={() => router.push("/settings")}>
                  <Settings01Icon size={16} />
                </Button>
              </div>
            </>
          )}
        >
          <div className="p-2 py-4 border-b border-white/10 mx-2 space-y-4">
            <div className="flex items-center gap-3 px-2  cursor-pointer transition-colors" onClick={() => router.push('/chat')}>
              <img src="/logo.svg" alt="Logo" width={44} height={44} className="flex-shrink-0 rounded-full" />
              <span className="text-lg font-semibold">Yuki AI</span>
            </div>
            <Button onClick={createNewChat} className="group w-full justify-start gap-2 hover:bg-black/20 backdrop-blur-sm border border-white/20 hover:border-white/30 rounded-full py-6" variant="ghost">
              <PlusSignIcon size={20} className="group-hover:animate-[spin_3s_linear_infinite]" />
              New Chat
            </Button>
          </div>
          <div className="flex-1 px-4 py-2 overflow-auto">
            <div className="space-y-1">
              {chatSessions.map((session, index) => (
                <motion.div 
                  key={session.id} 
                  initial={{ opacity: 0, x: -20 }} 
                  animate={{ opacity: 1, x: 0 }} 
                  transition={{ duration: 0.2, delay: index * 0.05 }} 
                  className={`group relative overflow-hidden flex items-center gap-2 rounded-full px-3 py-3 text-md transition-colors w-full cursor-pointer ${currentSessionId === session.id ? "bg-black/60" : "hover:bg-zinc-950/50 hover:shadow-xl hover:shadow-white/20 hover:border-white/30 hover:border"}`}
                  onClick={async () => { 
                    // Stop all running tasks when switching chats
                    await stopAllRunningTasks()
                    setCurrentSessionId(session.id)
                    setNewlyGeneratedMessageIds(new Set())
                  }}
                >
                  {currentSessionId === session.id && (
                    <div className="pointer-events-none absolute inset-0 border-1 border-black/20">
                      <motion.div className="absolute inset-y-0 left-0 w-2 rounded-r-full blur-2xl" style={{ backgroundColor: 'rgba(250,50,50,0.5)' }} initial={{ opacity: 0.8 }} animate={{ opacity: [0.7, 1, 0.7] }} transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }} />
                      <motion.div className="absolute inset-y-0 left-0 w-2/3 bg-gradient-to-r to-transparent" style={{ backgroundImage: 'linear-gradient(to right, rgba(250,50,50,0.5), transparent)' }} initial={{ opacity: 0.35 }} animate={{ opacity: [0.25, 0.5, 0.25] }} transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }} />
                      <motion.div className="absolute top-0 bottom-0 -left-16 w-40 bg-gradient-to-r to-transparent blur-2xl" style={{ backgroundImage: 'linear-gradient(to right, rgba(250,50,50,0.5), transparent)' }} animate={{ x: [0, 56, 0], opacity: [0.6, 1, 0.6] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }} />
                    </div>
                  )}
                  <div className="flex-1 truncate">{session.title}</div>
                  {/* Menu temporarily removed to avoid Radix Presence loop */}
                </motion.div>
              ))}
            </div>
          </div>
          <div className="border-t border-white/10 mx-2 p-2 space-y-1">
            <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/")}>
              <Home01Icon size={16} className="transition-all duration-200 group-hover:rotate-[-10deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.5)]" />
              Home
            </Button>
            <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/chat")}>
              <MessageMultiple02Icon size={16} className="transition-all duration-200 group-hover:rotate-[-10deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
              Chat
            </Button>
            <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/activity")}>
              <ComputerIcon size={16} className="transition-all duration-200 group-hover:rotate-[-10deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
              Activity
            </Button>
            <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/scheduled")}>
              <TimeScheduleIcon size={16} className="transition-all duration-200 group-hover:rotate-[360deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
              Schedule Task
            </Button>
            <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/settings")}>
              <Settings01Icon size={16} className="transition-all duration-200 group-hover:rotate-[180deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
              Settings
            </Button>
          </div>
        </AppSidebar>
        <motion.div 
          className="flex-1 flex flex-col h-screen overflow-hidden"
          animate={{ paddingLeft: showSidebar ? '16rem' : '4rem' }}
          transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
        >
          {showVoiceInstructions && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} transition={{ duration: 0.3 }} className="bg-blue-500/10 border-b border-blue-500/20 px-4 py-3 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 2, repeat: Infinity }}>
                    <VoiceIcon size={20} className="text-blue-400" />
                  </motion.div>
                  <div className="text-sm">
                    <div className="font-medium text-blue-100">Voice Mode Active</div>
                    <div className="text-blue-200/80">Say &quot;yuki&quot; followed by your command</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs border-blue-400/30 text-blue-300">Example: &quot;yuki, open calculator&quot;</Badge>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-blue-300 hover:text-blue-100" onClick={() => setShowVoiceInstructions(false)}>
                    <Cancel01Icon size={14} />
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        <div className="border-b border-white/10 px-4 py-3 flex items-center justify-between bg-black/20 backdrop-blur-sm flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors" onClick={() => setShowSidebar(!showSidebar)}>
                {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
              </div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-normal hidden sm:block">Yuki AI</h1>
            </div>
            </div>
            <div className="flex items-center gap-2">
              {(scheduledFlag || scheduledCount > 0) && (
                <Button variant="outline" size="sm" onClick={() => router.push('/scheduled')} className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 ring-1 ring-white/10 hover:ring-white/30">
                  Scheduled
                  {scheduledCount > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center h-5 min-w-5 px-2 rounded-full bg-white text-black text-[10px]">{scheduledCount}</span>
                  )}
                </Button>
              )}
            </div>
          </div>
        <div className="flex-1 px-2 sm:px-4 pb-28 overflow-auto">
            <div className="max-w-4xl mx-auto py-4 sm:py-8">
            {messages.length === 0 && !isLoading && inputPosition === 'centered' && (
              <motion.div className="flex flex-col items-center justify-center min-h-[80vh] text-center" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="mb-8">
                <div className="relative overflow-hidden">
                  <h2 className="text-4xl sm:text-6xl font-normal relative">
                    {["H","i",","," ","I","'","m"," ","Y","u","k","i"].map((letter, index) => (
                      <motion.span key={index} className="inline-block" animate={{ textShadow: ["0 0 0px rgba(255,255,255,0)","0 0 20px rgba(255,255,255,0.8)","0 0 0px rgba(255,255,255,0)"], filter: ["brightness(1)","brightness(1.5)","brightness(1)"] }} transition={{ duration: 0.8, delay: index * 0.15, repeat: Infinity, repeatDelay: 2, ease: "easeInOut" }}>{letter === " " ? "\u00A0" : letter}</motion.span>
                    ))}
                  </h2>
                </div>
                <div className="relative overflow-hidden">
                  <h2 className="text-3xl sm:text-4xl font-thin mb-4 relative">
                    {heroText.split("").map((letter, index) => (
                      <motion.span key={index} className="inline-block" animate={{ textShadow: ["0 0 0px rgba(255,255,255,0)","0 0 20px rgba(255,255,255,0.8)","0 0 0px rgba(255,255,255,0)"], filter: ["brightness(1)","brightness(1.5)","brightness(1)"] }} transition={{ duration: 0.8, delay: (index * 0.1) + 2, repeat: Infinity, repeatDelay: 2, ease: "easeInOut" }}>{letter === " " ? "\u00A0" : letter}</motion.span>
                    ))}
                  </h2>
                </div>
                  <p className="text-sm sm:text-md text-white/40 px-4 max-w-2xl">Ask me to automate Windows tasks, open applications, or control your system.</p>
                </motion.div>
                <motion.div className="w-full max-w-2xl" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
                  <ChatInput 
                    isListening={isListening}
                    isSpeaking={isSpeaking}
                    isLoading={isLoading}
                    input={input}
                    setInput={setInput}
                    sendMessage={sendMessage}
                    handleMicClick={handleMicClick}
                    inputRef={inputRef}
                    currentRequestId={currentRequestId}
                    stopRequested={stopRequested}
                    setStopRequested={setStopRequested}
                  />
                  <p className="text-xs text-gray-500 text-center mt-2 hidden sm:block">Press Enter to send, Shift+Enter for new line, Ctrl+Shift+V for voice mode</p>
                </motion.div>
              </motion.div>
            )}
              <div className="space-y-6">
                {messages.map((message, index) => (
                  <motion.div key={index} className={`group ${message.role === "user" ? "flex justify-end" : ""}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                    <div className={`flex gap-2 sm:gap-4 ${message.role === "user" ? "flex-row-reverse max-w-[80%]" : "w-full"}`}>
                      <div className="flex-shrink-0 mt-1">
                        {message.role === "user" ? (<img src="/logo.svg" alt="User" width={40} height={40} className="rounded-full" />) : (<div className="h-8 w-8"></div>)}
                      </div>
                      <div className="flex-1 space-y-2 min-w-0">
                        {message.role === "user" ? (
                          <div className="prose dark:prose-invert max-w-none bg-zinc-800/50 px-4 py-3 rounded-2xl">
                            <p className="whitespace-pre-wrap text-sm sm:text-base leading-relaxed text-gray-100">{message.content}</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {message.workflowSteps && message.workflowSteps.length > 0 && (<WorkflowSteps workflowSteps={message.workflowSteps} />)}
                            <div className="prose dark:prose-invert max-w-none">
                              {message.id && newlyGeneratedMessageIds.has(message.id) && mounted ? (
                                <TextGenerateEffect words={message.content} className="text-sm sm:text-base leading-relaxed text-gray-100 font-normal [&>div>div]:text-sm [&>div>div]:sm:text-base [&>div>div]:leading-relaxed [&>div>div]:text-gray-100 [&>div>div]:font-normal [&>div]:mt-0" duration={0.3} filter={false} />
                              ) : (
                                <p className="text-sm sm:text-base leading-relaxed text-gray-100 font-normal whitespace-pre-wrap">{message.content}</p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
                {isLoading && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                  <div className="flex gap-2 sm:gap-4">
                    <div className="flex-shrink-0 mt-1"><div className="h-8 w-8"></div></div>
                    <div className="flex-1 space-y-2">
                      <div className="text-2xl font-thin text-gray-100">
                        {mounted ? (
                          <TextGenerateEffect words="Thinking..." className="font-thin [&>div>div]:text-xl [&>div>div]:text-gray-100 [&>div>div]:font-thin [&>div]:mt-0" duration={0.2} filter={false} />
                        ) : (
                          <span>Thinking...</span>
                        )}
                      </div>
                      {currentWorkflow.length > 0 && (() => {
                        const latestStep = currentWorkflow[currentWorkflow.length - 1]
                        return (
                          <div className="p-2 pl-6">
                            <div className="flex items-start gap-2 text-sm">
                              <Loading02Icon size={20} className="animate-spin text-white mt-0.5" />
                              <p className="text-muted-foreground text-base">{latestStep.message}</p>
                            </div>
                          </div>
                        )
                      })()}
                    </div>
                  </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
          {inputPosition === 'bottom' && (
            <motion.div 
              className="bg-black/20 backdrop-blur-sm p-4 sm:p-6 fixed bottom-0 right-0 z-20" 
              initial={{ opacity: 0 }} 
              animate={{ 
                opacity: 1,
                left: showSidebar ? '16rem' : '4rem'
              }} 
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1], delay: 0.4 }}
            >
              <div className="max-w-4xl mx-auto">
                <ChatInput 
                  isListening={isListening}
                  isSpeaking={isSpeaking}
                  isLoading={isLoading}
                  input={input}
                  setInput={setInput}
                  sendMessage={sendMessage}
                  handleMicClick={handleMicClick}
                  inputRef={inputRef}
                  currentRequestId={currentRequestId}
                  stopRequested={stopRequested}
                  setStopRequested={setStopRequested}
                />
                <p className="text-xs text-gray-500 text-center mt-2 hidden sm:block">Press Enter to send, Shift+Enter for new line, Ctrl+Shift+V for voice mode</p>
              </div>
            </motion.div>
          )}
        </motion.div>
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Chat</DialogTitle>
            <DialogDescription>Enter a new name for this chat session.</DialogDescription>
          </DialogHeader>
          <Input value={newChatTitle} onChange={(e) => setNewChatTitle(e.target.value)} onKeyPress={(e) => e.key === "Enter" && renameChat()} placeholder="Chat name" autoFocus />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameDialogOpen(false)}>Cancel</Button>
            <Button onClick={renameChat}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </div>
    )
  )
}

export default function ChatPage() {
  class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; message?: string }>{
    constructor(props: { children: React.ReactNode }) {
      super(props)
      this.state = { hasError: false }
    }
    static getDerivedStateFromError(error: unknown) {
      return { hasError: true, message: error instanceof Error ? error.message : String(error) }
    }
    componentDidCatch(error: unknown, info: unknown) {
      // Log to console so we can see which subtree fails in production
      console.error('Chat ErrorBoundary caught:', error, info)
    }
    render() {
      if (this.state.hasError) {
        return (
          <div className="flex h-screen items-center justify-center bg-black text-white p-6">
            <div>
              <div className="text-lg mb-2">Something went wrong rendering the chat UI.</div>
              <div className="text-xs opacity-70">{this.state.message}</div>
            </div>
          </div>
        )
      }
      return this.props.children
    }
  }

  return (
    <ErrorBoundary>
      <Suspense fallback={<div className="flex h-screen items-center justify-center bg-black"><div className="text-white">Loading...</div></div>}>
        <ChatContent />
      </Suspense>
    </ErrorBoundary>
  )
}


