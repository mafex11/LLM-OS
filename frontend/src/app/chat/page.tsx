"use client"

import { useState, useEffect, useRef, Suspense, useMemo, useCallback } from "react"
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
  Cancel01Icon
} from "hugeicons-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useRouter, useSearchParams } from "next/navigation"
import { useApiKeys } from "@/contexts/ApiKeyContext"
import { motion, AnimatePresence } from "framer-motion"
import { AppSidebar } from "@/components/layout/Sidebar"
import Image from "next/image"
import { TextGenerateEffect } from "@/components/ui/text-generate-effect"
import { useToast } from "@/hooks/use-toast"

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

function WorkflowSteps({ workflowSteps }: { workflowSteps: WorkflowStep[] }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setIsOpen(!isOpen)} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors">
        <motion.div animate={{ rotate: isOpen ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ArrowRight01Icon size={12} className="text-white" />
        </motion.div>
        <CpuIcon size={12} className="text-white" />
        <span>View {workflowSteps.length} workflow steps</span>
      </button>
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: "easeInOut", opacity: { duration: 0.2 } }} className="mt-3 overflow-hidden">
            <div className="space-y-2 pl-4 border-l-2 border-muted">
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
                      <p className="text-muted-foreground">{step.message}</p>
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
  const [showSidebar, setShowSidebar] = useState(true)
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null)
  const [newChatTitle, setNewChatTitle] = useState("")
  const [taskExecuted, setTaskExecuted] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [voiceMode, setVoiceMode] = useState(false)
  const [showVoiceInstructions, setShowVoiceInstructions] = useState(false)
  const [newlyGeneratedMessageIds, setNewlyGeneratedMessageIds] = useState<Set<string>>(new Set())
  const workflowRef = useRef<WorkflowStep[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const generateUniqueSessionId = () => {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${performance.now()}`
  }

  const currentSession = chatSessions.find(s => s.id === currentSessionId)
  const messages = useMemo(() => currentSession?.messages || [], [currentSession?.messages])

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

  useEffect(() => {
    if (isInitialized) {
      createNewChat()
    }
  }, [isInitialized])

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

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages, currentWorkflow])

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
      const response = await fetch("http://localhost:8000/api/query/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: userMessage.content, use_vision: false, conversation_history: conversationHistory, api_key: getApiKey('google_api_key') }) })
      if (!response.ok) throw new Error("Failed to send query")
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
                const errorMessage: Message = { id: messageId, role: "assistant", content: isUserStop ? "Execution stopped by user" : `Error: ${rawMessage}`, timestamp: new Date(data.timestamp), workflowSteps: [...workflowRef.current] }
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
      const errorMsg: Message = { id: messageId, role: "assistant", content: "Failed to process query. Please make sure the API server is running.", timestamp: new Date() }
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
    const pollVoiceStatus = async () => { try { const r = await fetch("http://localhost:8000/api/voice/status"); if (r.ok) { const s = await r.json(); setIsListening(s.is_listening); setIsSpeaking(s.is_speaking) } } catch {} }
    const pollVoiceConversation = async () => { try { const r = await fetch("http://localhost:8000/api/voice/conversation"); if (r.ok) { const d = await r.json(); if (d.conversation && d.conversation.length > 0) { const voiceMessages = d.conversation.map((m: any) => ({ role: m.role, content: m.content, timestamp: new Date(m.timestamp * 1000), workflowSteps: m.workflowSteps ? m.workflowSteps.map((s: any) => ({ type: s.type, message: s.message, timestamp: new Date(s.timestamp * 1000), status: s.status, actionName: s.actionName })) : undefined })); const latestPlaceholder = [...voiceMessages].reverse().find((m: any) => m.role === 'assistant' && (!m.content || m.content.trim() === '') && m.workflowSteps && m.workflowSteps.length > 0); if (latestPlaceholder) { const steps: WorkflowStep[] = latestPlaceholder.workflowSteps.map((s: any) => ({ type: s.type, message: s.message, timestamp: new Date(s.timestamp), status: s.status, actionName: s.actionName })); setCurrentWorkflow(steps); setIsLoading(true) } const filtered = voiceMessages.filter((m: any) => !(m.role === 'assistant' && (!m.content || m.content.trim() === ''))); const newMsgs = filtered.filter((vm: any) => !messages.some(em => (em.role === vm.role && em.content === vm.content))); if (newMsgs.length > 0) { updateSessionMessages(currentSessionId, [...messages, ...newMsgs]); if (newMsgs.some((m: any) => m.role === 'assistant' && m.content && m.content.trim() !== '')) { setCurrentWorkflow([]); setIsLoading(false) } } } } } catch {} }
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

  const fetchSystemStatus = async () => {
    try { const r = await fetch("http://localhost:8000/api/status"); if (r.ok) setSystemStatus(await r.json()) } catch {}
  }

  const saveSessionsToStorage = (sessions: ChatSession[]) => { try { const s = sessions.filter(session => session.messages.length > 0); localStorage.setItem('chatSessions', JSON.stringify(s)) } catch {} }

  const saveConversationToServer = async (sessionId: string, messages: Message[]) => {
    try {
      const conversation = messages.map(msg => ({ role: msg.role, content: msg.content, timestamp: msg.timestamp.toISOString(), workflowSteps: msg.workflowSteps?.map(step => ({ ...step, timestamp: step.timestamp.toISOString() })) }))
      await fetch(`http://localhost:8000/api/conversation/${sessionId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(conversation) })
    } catch {}
  }

  const createNewChat = async () => {
    if (voiceMode) { await stopVoiceMode(); setVoiceMode(false) }
    const newSessionId = generateUniqueSessionId()
    const newSession: ChatSession = { id: newSessionId, title: "New Chat", messages: [], createdAt: new Date() }
    setChatSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newSessionId)
    try { const s = [newSession, ...chatSessions].filter(s => s.messages.length > 0); localStorage.setItem('chatSessions', JSON.stringify(s)) } catch {}
  }

  const deleteChat = async (sessionId: string) => {
    if (chatSessions.length === 1) return
    try { await fetch(`http://localhost:8000/api/conversation/${sessionId}`, { method: 'DELETE' }) } catch {}
    const updatedSessions = chatSessions.filter(s => s.id !== sessionId)
    setChatSessions(updatedSessions)
    try { saveSessionsToStorage(updatedSessions) } catch {}
    if (currentSessionId === sessionId) { if (updatedSessions.length > 0) { setCurrentSessionId(updatedSessions[0].id) } else { setCurrentSessionId("") } }
  }

  const openRenameDialog = (sessionId: string) => { const session = chatSessions.find(s => s.id === sessionId); if (session) { setRenamingSessionId(sessionId); setNewChatTitle(session.title); setRenameDialogOpen(true) } }
  const renameChat = () => { if (renamingSessionId && newChatTitle.trim()) { const updated = (prev => prev.map(session => session.id === renamingSessionId ? { ...session, title: newChatTitle.trim() } : session))(chatSessions); setChatSessions(updated); try { saveSessionsToStorage(updated) } catch {}; setRenameDialogOpen(false); setRenamingSessionId(null); setNewChatTitle("") } }
  const sendMessage = async () => { if (!input.trim() || isLoading) return; executeTask(input) }

  const startVoiceMode = useCallback(async () => {
    if (voiceModeStarting) return
    setVoiceModeStarting(true)
    try {
      const response = await fetch("http://localhost:8000/api/voice/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ api_key: getApiKey('google_api_key') }) })
      if (response.ok) {
        setIsListening(true); setShowVoiceInstructions(true)
        toast({ title: "Voice Mode Started", description: "Say 'yuki' followed by your command (e.g., 'yuki, open my calendar')" })
      } else { throw new Error("Failed to start voice mode") }
    } catch (error) {
      toast({ title: "Error Starting Voice Mode", description: error instanceof Error ? error.message : "Could not connect to voice system. Please check your API keys.", variant: "destructive" }); setVoiceMode(false)
    } finally { setVoiceModeStarting(false) }
  }, [getApiKey, toast, voiceModeStarting])

  const stopSpeaking = async () => { try { await fetch("http://localhost:8000/api/tts/stop", { method: "POST" }) } catch {} }
  const stopCurrentQuery = async () => { if (!currentRequestId || stopRequested) return; setStopRequested(true); try { await fetch("http://localhost:8000/api/query/stop", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: currentRequestId }) }) } catch {} }
  const stopVoiceMode = async () => { try { await fetch("http://localhost:8000/api/voice/stop", { method: "POST" }); setIsListening(false); setIsSpeaking(false); setShowVoiceInstructions(false) } catch {} }
  const handleMicClick = async () => { if (voiceModeStarting) return; try { if (!voiceMode) { await startVoiceMode(); setVoiceMode(true) } else { await stopVoiceMode(); setVoiceMode(false) } } catch {} }

  return (
    <div className="flex h-screen relative">
      <div className="absolute inset-0 z-0" style={{ background: "radial-gradient(125% 125% at 50% 100%, #000000 40%, #2b0707 100%)" }} />
      <div className="relative z-10 w-full h-full">
        <AppSidebar isOpen={showSidebar}>
          <div className="p-4 border-b border-white/10 mx-2 space-y-4">
            <div className="flex items-center gap-2 px-2">
              <Image src="/logo.svg" alt="Logo" width={30} height={30} className="flex-shrink-0 rounded-full" />
              <span className="text-sm font-semibold">Yuki AI</span>
            </div>
            <Button onClick={createNewChat} className="w-full justify-start gap-2 hover:bg-black/20 backdrop-blur-sm border border-white/20 hover:border-white/30" variant="ghost">
              <PlusSignIcon size={16} />
              New Chat
            </Button>
          </div>
          <ScrollArea className="flex-1 px-2 py-2">
            <div className="space-y-1">
              {chatSessions.map((session, index) => (
                <motion.div key={session.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2, delay: index * 0.05 }} className={`group relative overflow-hidden flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${currentSessionId === session.id ? "bg-black/60" : "hover:bg-black/30"}`}>
                  {currentSessionId === session.id && (
                    <div className="pointer-events-none absolute inset-0 border-1 border-black/20">
                      <motion.div className="absolute inset-y-0 left-0 w-2 bg-white/60 rounded-r-full blur-2xl" initial={{ opacity: 0.8 }} animate={{ opacity: [0.7, 1, 0.7] }} transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }} />
                      <motion.div className="absolute inset-y-0 left-0 w-2/3 bg-gradient-to-r from-white/60 to-transparent" initial={{ opacity: 0.35 }} animate={{ opacity: [0.25, 0.5, 0.25] }} transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }} />
                      <motion.div className="absolute top-0 bottom-0 -left-16 w-40 bg-gradient-to-r from-white/60 to-transparent blur-2xl" animate={{ x: [0, 56, 0], opacity: [0.6, 1, 0.6] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }} />
                    </div>
                  )}
                  <div className="flex-1 truncate cursor-pointer" onClick={() => { setCurrentSessionId(session.id); setNewlyGeneratedMessageIds(new Set()) }}>{session.title}</div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100" onClick={(e) => e.stopPropagation()}>
                        <MoreVerticalIcon size={12} />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openRenameDialog(session.id)}>
                        <PencilEdit02Icon size={12} className="mr-2" />
                        Rename
                      </DropdownMenuItem>
                      {chatSessions.length > 1 && (
                        <DropdownMenuItem onClick={() => deleteChat(session.id)} className="text-red-600">
                          <Delete02Icon size={12} className="mr-2" />
                          Delete
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </motion.div>
              ))}
            </div>
          </ScrollArea>
          <div className="border-t border-white/10 mx-2 p-2 space-y-1">
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/")}>
              <Home01Icon size={16} />
              Home
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/agent-settings")}>
              <BotIcon size={16} />
              Agent Settings
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/settings")}>
              <Settings01Icon size={16} />
              Settings
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/scheduled")}>
              <Navigation03Icon size={16} />
              Scheduled Tasks
            </Button>
          </div>
        </AppSidebar>
        <div className={`${showSidebar ? 'pl-64' : 'pl-0'} flex-1 flex flex-col`}>
        <AnimatePresence>
          {showVoiceInstructions && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.3 }} className="bg-blue-500/10 border-b border-blue-500/20 px-4 py-3 backdrop-blur-sm">
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
        </AnimatePresence>
        <motion.div className="border-b border-white/10 px-4 py-3 flex items-center justify-between bg-black/20 backdrop-blur-sm sticky top-0 z-10" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <div className="flex items-center gap-3">
              <div className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors" onClick={() => setShowSidebar(!showSidebar)}>
                {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
              </div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-normal hidden sm:block">Yuki AI</h1>
            </div>
            </div>
          </motion.div>
        <ScrollArea className="flex-1 px-2 sm:px-4 pb-28" ref={scrollRef}>
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
                              <Button onClick={() => { if (!stopRequested && currentRequestId) { fetch("http://localhost:8000/api/query/stop", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: currentRequestId }) }).catch(console.error); setStopRequested(true) } }} variant="ghost" size="sm" className="h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border border-red-500/50"><span className="flex items-center justify-center w-full h-full text-red-500"><Cancel01Icon size={28} /></span></Button>
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
                  <p className="text-xs text-gray-500 text-center mt-2 hidden sm:block">Press Enter to send, Shift+Enter for new line, Ctrl+Shift+V for voice mode</p>
                </motion.div>
              </motion.div>
            )}
              <div className="space-y-6">
              <AnimatePresence mode="popLayout">
                {messages.map((message, index) => (
                  <motion.div key={index} className={`group ${message.role === "user" ? "flex justify-end" : ""}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                    <div className={`flex gap-2 sm:gap-4 ${message.role === "user" ? "flex-row-reverse max-w-[80%]" : "w-full"}`}>
                      <div className="flex-shrink-0 mt-1">
                        {message.role === "user" ? (<Image src="/logo.svg" alt="User" width={40} height={40} className="rounded-full" />) : (<div className="h-8 w-8"></div>)}
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
                              {message.id && newlyGeneratedMessageIds.has(message.id) ? (
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
              </AnimatePresence>
                {isLoading && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                  <div className="flex gap-2 sm:gap-4">
                    <div className="flex-shrink-0 mt-1"><div className="h-8 w-8"></div></div>
                    <div className="flex-1 space-y-2">
                      <div className="text-2xl font-thin text-gray-100">
                        <TextGenerateEffect words="Thinking..." className="font-thin [&>div>div]:text-xl [&>div>div]:text-gray-100 [&>div>div]:font-thin [&>div]:mt-0" duration={0.2} filter={false} />
                      </div>
                      {currentWorkflow.length > 0 && (() => {
                        const latestStep = currentWorkflow[currentWorkflow.length - 1]
                        return (
                          <div className="flex items-start gap-2 text-sm pl-6">
                            <Loading02Icon size={20} className="animate-spin text-white mt-0.5" />
                            <p className="text-muted-foreground text-base">{latestStep.message}</p>
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
          </ScrollArea>
        <AnimatePresence>
          {inputPosition === 'bottom' && (
            <motion.div className="bg-black/20 backdrop-blur-sm p-4 sm:p-6 fixed bottom-0 right-0 z-20" style={{ left: showSidebar ? '16rem' : 0 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4, delay: 0.4 }}>
              <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-3">
                  <AnimatePresence mode="wait">
                    {!isListening ? (
                      <motion.div key="normal-input" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }} className="flex items-center gap-3 w-full">
                        <motion.div initial={{ opacity: 1, scale: 1 }} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} transition={{ duration: 0.2 }}>
                          <Button variant="ghost" size="sm" className={`h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border ${isListening ? 'border-red-500/50 bg-red-500/10' : isSpeaking ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/20 hover:border-white/30'}`} disabled={isLoading} title={isListening ? "Stop voice mode" : "Start voice mode (say 'yuki' + command)"} onClick={handleMicClick}>
                            {isListening ? (<motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 1, repeat: Infinity }}><VoiceIcon size={24} className="text-red-500" /></motion.div>) : isSpeaking ? (<motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 0.8, repeat: Infinity }}><VoiceIcon size={24} className="text-blue-500" /></motion.div>) : (<VoiceIcon size={24} className="text-white" />)}
                          </Button>
                        </motion.div>
                        <motion.div className="flex-1 relative" initial={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
                          <Input ref={inputRef} placeholder="What can I do for you?" value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()} disabled={isLoading} className="w-full text-base sm:text-lg bg-black/30 border border-white/20 text-gray-100 placeholder:text-gray-500 rounded-3xl shadow-lg focus-visible:ring-0 focus-visible:ring-offset-0 h-12 sm:h-14 backdrop-blur-sm hover:border-white/30 focus:border-white/40" />
                        </motion.div>
                        <motion.div initial={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20, scale: 0.8 }} transition={{ duration: 0.3 }}>
                          {isLoading ? (
                            <Button onClick={() => { if (!stopRequested && currentRequestId) { fetch("http://localhost:8000/api/query/stop", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: currentRequestId }) }).catch(console.error); setStopRequested(true) } }} variant="ghost" size="sm" className="h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border border-red-500/50"><span className="flex items-center justify-center w-full h-full text-red-500"><Cancel01Icon size={36} /></span></Button>
                          ) : (
                            <Button onClick={sendMessage} disabled={!input.trim()} variant="ghost" size="sm" className="h-12 w-12 sm:h-14 sm:w-14 p-0 hover:bg-black/20 rounded-full backdrop-blur-sm flex-shrink-0 border border-white/20 hover:border-white/30"><span className="flex items-center justify-center w-full h-full"><Navigation03Icon size={46} /></span></Button>
                          )}
                        </motion.div>
                      </motion.div>
                    ) : (
                      <motion.div key="listening-input" className="flex-1 relative" initial={{ width: "48px", opacity: 0 }} animate={{ width: "100%", opacity: 1 }} exit={{ width: "48px", opacity: 0 }} transition={{ duration: 0.5, ease: "easeInOut" }}>
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
                <p className="text-xs text-gray-500 text-center mt-2 hidden sm:block">Press Enter to send, Shift+Enter for new line, Ctrl+Shift+V for voice mode</p>
          </div>
            </motion.div>
          )}
        </AnimatePresence>
        </div>
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
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center bg-black"><div className="text-white">Loading...</div></div>}>
      <ChatContent />
    </Suspense>
  )
}


