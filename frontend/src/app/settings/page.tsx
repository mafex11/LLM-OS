"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  BotIcon, 
  Key01Icon, 
  ComputerIcon, 
  FloppyDiskIcon, 
  ViewIcon, 
  ViewOffIcon, 
  Loading01Icon, 
  Settings01Icon, 
  SidebarLeft01Icon, 
  SidebarRight01Icon, 
  Sun01Icon, 
  Moon02Icon, 
  PaintBrush01Icon,
  Home01Icon,
  Cancel01Icon,
  Tick02Icon,
  ArrowRight02Icon,
  Mic02Icon,
  VolumeMute01Icon,
  ArrowDown01Icon,
  ArrowUp01Icon,
  AiBrowserIcon,
  Loading03Icon,
  AiBrain01Icon,
  TimeScheduleIcon,
  MessageMultiple02Icon
} from "hugeicons-react"
import { useToast } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { useAudioDevices } from "@/hooks/useAudioDevices"
// Removed useApiKeys import - using config file only
import { motion, AnimatePresence } from "framer-motion"
import { AppSidebar } from "@/components/layout/Sidebar"
import Image from "next/image"
import { getApiUrlSync } from "@/lib/api"

interface SystemStatus {
  agent_ready: boolean
  running_programs: Array<{ name: string; title: string; id: string }>
  memory_stats: any
  performance_stats: any
}

interface ApiKeys {
  google_api_key: string
  elevenlabs_api_key: string
  deepgram_api_key: string
}

type BrowserOption = "edge" | "chrome" | "firefox"
type ModelOption =
  | "gemini-2.5-pro"
  | "gemini-2.5-flash"
  | "gemini-2.5-flash-lite"
  | "gemini-2.0-flash"
  | "gemini-2.0-flash-lite"

const MODEL_OPTIONS: ModelOption[] = [
  "gemini-2.5-pro",
  "gemini-2.5-flash",
  "gemini-2.5-flash-lite",
  "gemini-2.0-flash",
  "gemini-2.0-flash-lite"
]

type AgentSettingsState = {
  enable_activity_tracking: boolean
  enable_vision: boolean
  enable_conversation: boolean
  enable_tts: boolean
  cache_timeout: number
  tts_voice_id: string
  browser: BrowserOption
  literal_mode: boolean
  consecutive_failures: number
  model: ModelOption
}

export default function SettingsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { theme, setTheme } = useTheme()
  const audioDevices = useAudioDevices()
  // Removed context dependency - using config file only
  const [showSidebar, setShowSidebar] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("sidebarOpen")
      return saved === "true"
    }
    return false
  })
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [notificationSoundsEnabled, setNotificationSoundsEnabled] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("notificationSoundsEnabled")
      return saved !== "false" // Default to true if not set
    }
    return true
  })
  
  // Save sidebar state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sidebarOpen", String(showSidebar))
    }
  }, [showSidebar])

  // Save notification sounds setting to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("notificationSoundsEnabled", String(notificationSoundsEnabled))
    }
  }, [notificationSoundsEnabled])
  const [showApiKeys, setShowApiKeys] = useState({
    google_api_key: false,
    elevenlabs_api_key: false,
    deepgram_api_key: false
  })
  const [savingKeys, setSavingKeys] = useState(false)
  const [savingAgentSettings, setSavingAgentSettings] = useState(false)
  const [maxSteps, setMaxSteps] = useState<number>(50)
  const [maxStepsInput, setMaxStepsInput] = useState<string>("50")
  const [maxStepsInvalid, setMaxStepsInvalid] = useState<boolean>(false)
  const [showRunningPrograms, setShowRunningPrograms] = useState(false)
  const [apiKeyInputs, setApiKeyInputs] = useState<ApiKeys>({
    google_api_key: "",
    elevenlabs_api_key: "",
    deepgram_api_key: ""
  })
  const [agentSettings, setAgentSettings] = useState<AgentSettingsState>({
    enable_activity_tracking: true,
    enable_vision: false,
    enable_conversation: true,
    enable_tts: false,
    cache_timeout: 2.0,
    tts_voice_id: "21m00Tcm4TlvDq8ikWAM",
    browser: "chrome",
    literal_mode: true,
    consecutive_failures: 3,
    model: "gemini-2.0-flash"
  })
  const [cacheTimeoutInput, setCacheTimeoutInput] = useState<string>("2.0")
  const [cacheTimeoutInvalid, setCacheTimeoutInvalid] = useState<boolean>(false)
  const [consecutiveFailuresInput, setConsecutiveFailuresInput] = useState<string>("3")
  const [consecutiveFailuresInvalid, setConsecutiveFailuresInvalid] = useState<boolean>(false)

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(getApiUrlSync("/api/status"))
      if (response.ok) {
        const data = await response.json()
        setSystemStatus(data)
      }
    } catch (error) {
      console.error("Failed to fetch system status:", error)
      // Set a default status when backend is not available
      setSystemStatus({
        agent_ready: false,
        running_programs: [],
        memory_stats: null,
        performance_stats: null
      })
    }
  }

  const loadApiKeys = useCallback(async () => {
    try {
      const response = await fetch(getApiUrlSync("/api/config/keys"))
      if (response.ok) {
        const data = await response.json()
        // Load API keys into input fields
        setApiKeyInputs({
          google_api_key: data.google_api_key || "",
          elevenlabs_api_key: data.elevenlabs_api_key || "",
          deepgram_api_key: data.deepgram_api_key || ""
        })
      }
    } catch (error) {
      console.error("Failed to fetch API keys:", error)
      // Keep existing values when backend is not available
    }
  }, [])

  const loadAgentSettings = useCallback(async () => {
    try {
      const response = await fetch(getApiUrlSync("/api/settings"))
      if (response.ok) {
        const data = await response.json()
        const parsedMaxSteps = Number(data.max_steps)
        const boundedMaxSteps = Math.max(1, Math.min(200, Number.isFinite(parsedMaxSteps) ? Math.floor(parsedMaxSteps) : 50))
        const parsedCacheTimeout = Number(data.cache_timeout)
        const boundedCacheTimeout = Math.max(0.1, Math.min(10, Number.isFinite(parsedCacheTimeout) ? parsedCacheTimeout : 2.0))
        const parsedFailures = Number(data.consecutive_failures)
        const boundedFailures = Math.max(1, Math.min(10, Number.isFinite(parsedFailures) ? Math.floor(parsedFailures) : 3))
        const browser: BrowserOption =
          typeof data.browser === "string" && ["edge", "chrome", "firefox"].includes(data.browser)
            ? (data.browser as BrowserOption)
            : "chrome"
        const rawModel = typeof data.model === "string" ? data.model : ""
        const model = (MODEL_OPTIONS.find(option => option === rawModel) ?? "gemini-2.0-flash") as ModelOption
        const ttsVoice = typeof data.tts_voice_id === "string" && data.tts_voice_id.trim().length > 0
          ? data.tts_voice_id.trim()
          : "21m00Tcm4TlvDq8ikWAM"
        setAgentSettings({
          enable_activity_tracking: data.enable_activity_tracking ?? true,
          enable_vision: data.enable_vision ?? false,
          enable_conversation: data.enable_conversation ?? true,
          enable_tts: data.enable_tts ?? false,
          cache_timeout: Number(boundedCacheTimeout.toFixed(2)),
          tts_voice_id: ttsVoice,
          browser,
          literal_mode: data.literal_mode ?? true,
          consecutive_failures: boundedFailures,
          model
        })
        setMaxSteps(boundedMaxSteps)
        setMaxStepsInput(String(boundedMaxSteps))
        setCacheTimeoutInvalid(false)
        setConsecutiveFailuresInvalid(false)
        setMaxStepsInvalid(false)
      }
    } catch (error) {
      console.error("Failed to fetch agent settings:", error)
      // Keep existing values when backend is not available
    }
  }, [])

  useEffect(() => {
    fetchSystemStatus()
    loadApiKeys()
    loadAgentSettings()
    const interval = setInterval(fetchSystemStatus, 5000)
    return () => clearInterval(interval)
  }, [loadApiKeys, loadAgentSettings])

  useEffect(() => {
    setMaxStepsInput(String(maxSteps))
  }, [maxSteps])

  useEffect(() => {
    setCacheTimeoutInput(String(agentSettings.cache_timeout))
  }, [agentSettings.cache_timeout])

  useEffect(() => {
    setConsecutiveFailuresInput(String(agentSettings.consecutive_failures))
  }, [agentSettings.consecutive_failures])

  const handleApiKeyChange = (keyType: keyof ApiKeys, value: string) => {
    // Update input field state
    setApiKeyInputs(prev => ({
      ...prev,
      [keyType]: value
    }))
  }

  const saveApiKeys = async () => {
    setSavingKeys(true)
    
    try {
      // Save to backend config file
      const response = await fetch(getApiUrlSync("/api/config/keys"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(apiKeyInputs),
      })

      if (response.ok) {
        // Also save to keytar if running in Electron
        if (typeof window !== 'undefined' && window.desktop) {
          try {
            await window.desktop.setSecret('google_api_key', apiKeyInputs.google_api_key || '');
            await window.desktop.setSecret('elevenlabs_api_key', apiKeyInputs.elevenlabs_api_key || '');
            await window.desktop.setSecret('deepgram_api_key', apiKeyInputs.deepgram_api_key || '');
          } catch (keytarError) {
            console.warn('Failed to save API keys to keytar (this is OK if not in Electron):', keytarError);
          }
        }
        
        toast({
          title: "API Keys Saved",
          description: "All API keys have been saved successfully!",
        })
      } else {
        toast({
          title: "Error",
          description: "Failed to save API keys to config file.",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error("Failed to save API keys:", error)
      toast({
        title: "Backend Unavailable",
        description: "Cannot connect to backend server. Please ensure the server is running.",
        variant: "destructive"
      })
    } finally {
      setSavingKeys(false)
    }
  }

  const resetApiKeys = () => {
    // Clear all input fields
    setApiKeyInputs({
      google_api_key: "",
      elevenlabs_api_key: "",
      deepgram_api_key: ""
    })
    toast({
      title: "API Keys Cleared",
      description: "All API key fields have been cleared.",
    })
  }

  const saveAgentSettings = async () => {
    if (maxStepsInvalid || cacheTimeoutInvalid || consecutiveFailuresInvalid) {
      toast({
        title: "Fix validation errors",
        description: "Resolve highlighted fields before saving.",
        variant: "destructive"
      })
      return
    }

    const trimmedMaxSteps = maxStepsInput.trim()
    const trimmedFailures = consecutiveFailuresInput.trim()
    const trimmedCacheTimeout = cacheTimeoutInput.trim()

    if (!trimmedMaxSteps || !trimmedFailures || !trimmedCacheTimeout) {
      if (!trimmedMaxSteps) setMaxStepsInvalid(true)
      if (!trimmedFailures) setConsecutiveFailuresInvalid(true)
      if (!trimmedCacheTimeout) setCacheTimeoutInvalid(true)
      toast({
        title: "Missing values",
        description: "Provide values for steps, failure limit, and cache timeout.",
        variant: "destructive"
      })
      return
    }

    setSavingAgentSettings(true)
    try {
      const fallbackMaxSteps = maxSteps > 0 ? maxSteps : 50
      const parsedMaxSteps = Number(trimmedMaxSteps)
      const boundedMaxSteps = Math.max(1, Math.min(200, Number.isFinite(parsedMaxSteps) ? Math.floor(parsedMaxSteps) : fallbackMaxSteps))
      const fallbackFailures = agentSettings.consecutive_failures > 0 ? agentSettings.consecutive_failures : 3
      const parsedFailures = Number(trimmedFailures)
      const boundedFailures = Math.max(1, Math.min(10, Number.isFinite(parsedFailures) ? Math.floor(parsedFailures) : fallbackFailures))
      const parsedCacheTimeout = Number(trimmedCacheTimeout)
      const boundedCacheTimeout = Math.max(0.1, Math.min(10, Number.isFinite(parsedCacheTimeout) ? parsedCacheTimeout : agentSettings.cache_timeout))
      const formattedCacheTimeout = Number(boundedCacheTimeout.toFixed(2))
      const trimmedVoice = agentSettings.tts_voice_id.trim() || "21m00Tcm4TlvDq8ikWAM"

      const response = await fetch(getApiUrlSync("/api/settings"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          max_steps: boundedMaxSteps,
          consecutive_failures: boundedFailures,
          browser: agentSettings.browser,
          literal_mode: agentSettings.literal_mode,
          enable_activity_tracking: agentSettings.enable_activity_tracking,
          enable_vision: agentSettings.enable_vision,
          enable_conversation: agentSettings.enable_conversation,
          enable_tts: agentSettings.enable_tts,
          cache_timeout: formattedCacheTimeout,
          tts_voice_id: trimmedVoice,
          model: agentSettings.model
        })
      })

      if (response.ok) {
        toast({
          title: "Agent settings saved",
          description: "Agent settings have been updated successfully."
        })
        setAgentSettings(prev => ({
          ...prev,
          cache_timeout: formattedCacheTimeout,
          consecutive_failures: boundedFailures,
          tts_voice_id: trimmedVoice
        }))
        setMaxSteps(boundedMaxSteps)
        setMaxStepsInput(String(boundedMaxSteps))
        setCacheTimeoutInput(formattedCacheTimeout.toString())
        setConsecutiveFailuresInput(String(boundedFailures))
        setCacheTimeoutInvalid(false)
        setConsecutiveFailuresInvalid(false)
        setMaxStepsInvalid(false)
      } else {
        toast({
          title: "Error",
          description: "Failed to update agent settings.",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Backend Unavailable",
        description: "Cannot connect to backend. Ensure the server is running.",
        variant: "destructive"
      })
    } finally {
      setSavingAgentSettings(false)
    }
  }

  const clearApiKey = (keyType: keyof ApiKeys) => {
    setApiKeyInputs(prev => ({
      ...prev,
      [keyType]: ""
    }))
    toast({
      title: "API Key Cleared",
      description: `${keyType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} field has been cleared.`,
    })
  }


  return (
    <div className="flex h-screen w-full overflow-hidden">
      <div className="relative z-10 w-full flex flex-col">
        <AppSidebar
          isOpen={showSidebar}
          collapsedContent={(
            <>
              <div className="flex items-center justify-center mt-0">
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-transparent" onClick={() => router.push('/chat')} title="Chat">
                  <img src="/logo.svg" alt="Logo" width={36} height={36} className="rounded-full" />
                </Button>
              </div>
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
                <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5 bg-white/10" onClick={() => router.push("/settings")}>
                  <Settings01Icon size={16} />
                </Button>
              </div>
            </>
          )}
        >
            {/* Sidebar Header */}
            <div className="p-4 border-b border-white/10 mx-2 space-y-4">
              <div className="flex items-center gap-3 px-2 cursor-pointer rounded-lg transition-colors" onClick={() => router.push('/chat')}>
                <img src="/logo.svg" alt="Logo" width={44} height={44} className="flex-shrink-0 rounded-full" />
                <span className="text-lg font-semibold">Yuki AI</span>
              </div>
              <Button 
                onClick={() => router.push("/chat")} 
                className="w-full gap-2 hover:bg-black/20 backdrop-blur-sm border text-center justify-center border-white/20 hover:border-white/30 rounded-full hover:shadow-white/10 hover:shadow-xl" 
                variant="ghost"
              >
                Back to Chat
              </Button>
            </div>
            {/* Sidebar Content */}
            <ScrollArea className="flex-1 px-4 py-2">
              <div className="space-y-1">
                <div className="px-3 py-2 text-sm font-normal text-muted-foreground">
                  Settings
                </div>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2  hover:bg-zinc-950 rounded-full hover:shadow-white/10 hover:shadow-xl hover:border hover:border-white/20"
                onClick={() => document.getElementById('api-keys')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                API Keys
                <span className="ml-auto opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                  <ArrowRight02Icon size={14} />
                </span>
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-zinc-950 rounded-full hover:shadow-white/10 hover:shadow-xl hover:border hover:border-white/20"
                onClick={() => document.getElementById('agent-settings')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Agent Settings
                <span className="ml-auto opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                  <ArrowRight02Icon size={14} />
                </span>
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-zinc-950 rounded-full hover:shadow-white/10 hover:shadow-xl hover:border hover:border-white/20"
                onClick={() => document.getElementById('audio-settings')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Audio Settings
                <span className="ml-auto opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                  <ArrowRight02Icon size={14} />
                </span>
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-zinc-950 rounded-full hover:shadow-white/10 hover:shadow-xl hover:border hover:border-white/20"
                onClick={() => document.getElementById('system-status')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                System Status
                <span className="ml-auto opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                  <ArrowRight02Icon size={14} />
                </span>
              </Button>
              </div>
            </ScrollArea>
            {/* Sidebar Footer */}
            <div className="border-t border-white/10 mx-2 p-2 space-y-1">
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-black/30"
                onClick={() => router.push("/")}
              >
                <Home01Icon size={16} className="transition-all duration-200 group-hover:rotate-[-10deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.5)]" />
                Home
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-white/5"
                onClick={() => router.push('/chat')}
              >
                <MessageMultiple02Icon size={16} className="transition-all duration-200 group-hover:rotate-[-10deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
                Chat
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-white/5"
                onClick={() => router.push("/activity")}
              >
                <ComputerIcon size={16} className="transition-all duration-200 group-hover:rotate-[-10deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
                Activity
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-white/5"
                onClick={() => router.push("/scheduled")}
              >
                <TimeScheduleIcon size={16} className="transition-all duration-200 group-hover:rotate-[360deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
                Schedule Task
              </Button>
              <Button
                variant="ghost"
                className="group w-full justify-start gap-2 hover:bg-black/30"
                onClick={() => router.push("/settings")}
              >
                <Settings01Icon size={16} className="transition-all duration-200 group-hover:rotate-[180deg] group-hover:drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
                Settings
              </Button>
            </div>
        </AppSidebar>

        <motion.div 
          className="flex-1 flex flex-col overflow-hidden"
          animate={{ paddingLeft: showSidebar ? '16rem' : '4rem' }}
          transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
        >
        <div 
          className="border-b border-white/10 px-4 py-3 flex items-center justify-between bg-black/20 backdrop-blur-sm sticky top-0 z-50 flex-shrink-0"
        >
          <div className="flex items-center gap-3">
            <div
              className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
            </div>
            <div className="flex items-center gap-2">
              <Settings01Icon size={24} />
              <h1 className="text-lg font-normal hidden sm:block">Settings</h1>
            </div>
          </div>
        </div>

        <ScrollArea className="flex-1 px-2 sm:px-4">
          <div className="max-w-4xl mx-auto py-4 sm:py-8">
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
              <Card id="api-keys" className="bg-black/40 border border-white/20 rounded-3xl ">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 font-normal text-white">
                    {/* <Key01Icon size={20} /> */}
                    API Keys
                  </CardTitle>
                  <CardDescription className="text-md font-thin text-white/40">
                    Configure your API keys for Yuki services
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="google_api_key" className="text-sm font-normal pl-2">
                        Google API Key <span className="text-red-500">*</span>
                      </Label>
                      <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                          <Input
                            id="google_api_key"
                            type={showApiKeys.google_api_key ? "text" : "password"}
                            value={apiKeyInputs.google_api_key}
                            onChange={(e) => handleApiKeyChange('google_api_key', e.target.value)}
                            placeholder="Enter your Google API key"
                            className="pr-10 rounded-full bg-transparent border border-white/40 hover:border-white/30 text-white outline-none focus placeholder:text-gray-500"
                          />
                          <div className="absolute right-0 top-0 h-full flex items-center pr-2 pt-0.5">
                            <motion.div
                              whileTap={{ scale: 0.85, rotate: 180 }}
                              transition={{ duration: 0.2 }}
                            >
                              <Button
                                type="button"
                                variant="default"
                                size="icon"
                                className="h-6 w-6 bg-white hover:bg-gray-400  text-black rounded-full"
                                onClick={() => setShowApiKeys({ ...showApiKeys, google_api_key: !showApiKeys.google_api_key })}
                              >
                                <motion.div
                                  animate={{ rotate: showApiKeys.google_api_key ? 360 : 0 }}
                                  transition={{ duration: 0.3 }}
                                >
                                  {showApiKeys.google_api_key ? <ViewOffIcon size={14} /> : <ViewIcon size={14} />}
                                </motion.div>
                              </Button>
                            </motion.div>
                          </div>
                        </div>
                        <div 
                          className={`h-9 w-9 flex items-center justify-center rounded-full cursor-pointer ${apiKeyInputs.google_api_key ? 'bg-white border border-zinc-950/40' : 'bg-zinc-900 border border-white/40'}`}
                          onClick={() => apiKeyInputs.google_api_key && clearApiKey('google_api_key')}
                        >
                          <Tick02Icon size={16} className={apiKeyInputs.google_api_key ? 'text-green-700' : 'text-gray-500'} />
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                      <p className="text-xs text-gray-500">
                        Required for Gemini AI. Get your key from{" "}
                        <a 
                          href="https://makersuite.google.com/app/apikey" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="underline hover:text-foreground"
                        >
                          Google AI Studio
                        </a>
                      </p>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <Label htmlFor="elevenlabs_api_key" className="text-sm font-normal">
                        ElevenLabs API Key
                      </Label>
                      <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                          <Input
                            id="elevenlabs_api_key"
                            type={showApiKeys.elevenlabs_api_key ? "text" : "password"}
                            value={apiKeyInputs.elevenlabs_api_key}
                            onChange={(e) => handleApiKeyChange('elevenlabs_api_key', e.target.value)}
                            placeholder="Enter your ElevenLabs API key (optional)"
                            className="pr-10 rounded-full bg-transparent border border-white/40 hover:border-white/30 text-white outline-none focus:- placeholder:text-gray-500"
                          />
                          <div className="absolute right-0 top-0 h-full flex items-center pr-2 pt-0.5">
                            <motion.div
                              whileTap={{ scale: 0.85, rotate: 180 }}
                              transition={{ duration: 0.2 }}
                            >
                              <Button
                                type="button"
                                variant="default"
                                size="icon"
                                className="h-6 w-6 bg-white hover:bg-gray-400  text-black rounded-full"
                                onClick={() => setShowApiKeys({ ...showApiKeys, elevenlabs_api_key: !showApiKeys.elevenlabs_api_key })}
                              >
                                <motion.div
                                  animate={{ rotate: showApiKeys.elevenlabs_api_key ? 360 : 0 }}
                                  transition={{ duration: 0.3 }}
                                >
                                  {showApiKeys.elevenlabs_api_key ? <ViewOffIcon size={14} /> : <ViewIcon size={14} />}
                                </motion.div>
                              </Button>
                            </motion.div>
                          </div>
                        </div>
                        <div 
                          className={`h-9 w-9 flex items-center justify-center rounded-full cursor-pointer ${apiKeyInputs.elevenlabs_api_key ? 'bg-white' : 'bg-zinc-800'}`}
                          onClick={() => apiKeyInputs.elevenlabs_api_key && clearApiKey('elevenlabs_api_key')}
                        >
                          <Tick02Icon size={16} className={apiKeyInputs.elevenlabs_api_key ? 'text-green-700' : 'text-gray-500'} />
                        </div>
                      </div>
                      <p className="text-xs text-gray-500">
                        Optional for text-to-speech. Get your key from{" "}
                        <a 
                          href="https://elevenlabs.io/" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="underline hover:text-foreground"
                        >
                          ElevenLabs
                        </a>
                      </p>
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <Label htmlFor="deepgram_api_key" className="text-sm font-normal">
                        Deepgram API Key
                      </Label>
                      <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                          <Input
                            id="deepgram_api_key"
                            type={showApiKeys.deepgram_api_key ? "text" : "password"}
                            value={apiKeyInputs.deepgram_api_key}
                            onChange={(e) => handleApiKeyChange('deepgram_api_key', e.target.value)}
                            placeholder="Enter your Deepgram API key (optional)"
                            className="pr-10 rounded-full bg-transparent border border-white/20 hover:border-white/30 text-white outline-none focus:- placeholder:text-gray-500"
                          />
                          <div className="absolute right-0 top-0 h-full flex items-center pr-2 pt-0.5">
                            <motion.div
                              whileTap={{ scale: 0.85, rotate: 180 }}
                              transition={{ duration: 0.2 }}
                            >
                              <Button
                                type="button"
                                variant="default"
                                size="icon"
                                className="h-6 w-6 bg-white hover:bg-gray-400  text-black rounded-full"
                                onClick={() => setShowApiKeys({ ...showApiKeys, deepgram_api_key: !showApiKeys.deepgram_api_key })}
                              >
                                <motion.div
                                  animate={{ rotate: showApiKeys.deepgram_api_key ? 360 : 0 }}
                                  transition={{ duration: 0.3 }}
                                >
                                  {showApiKeys.deepgram_api_key ? <ViewOffIcon size={14} /> : <ViewIcon size={14} />}
                                </motion.div>
                              </Button>
                            </motion.div>
                          </div>
                        </div>
                        <div 
                          className={`h-9 w-9 flex items-center justify-center rounded-full cursor-pointer ${apiKeyInputs.deepgram_api_key ? 'bg-white' : 'bg-zinc-800'}`}
                          onClick={() => apiKeyInputs.deepgram_api_key && clearApiKey('deepgram_api_key')}
                        >
                          <Tick02Icon size={16} className={apiKeyInputs.deepgram_api_key ? 'text-green-700' : 'text-gray-500'} />
                        </div>
                      </div>
                      <p className="text-xs text-gray-500">
                        Optional for voice control. Get your key from{" "}
                        <a 
                          href="https://deepgram.com/" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="underline hover:text-foreground"
                        >
                          Deepgram
                        </a>
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-4">
                      <div className="text-xs text-gray-500">
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            toast({
                              title: "API Keys Status",
                              description: `Google: ${apiKeyInputs.google_api_key ? 'Working' : 'Not Found'}, ElevenLabs: ${apiKeyInputs.elevenlabs_api_key ? 'Working' : 'Not Found'}, Deepgram: ${apiKeyInputs.deepgram_api_key ? 'Working' : 'Not Found'}`,
                            })
                          }}
                          className="text-xs rounded-full border-white/30 bg-zinc-950 hover:bg-zinc-950 hover:shadow-[0_0_22px_rgba(255,255,255,0.2)] ring-1 ring-white/10 hover:ring-white/30 transition-all"
                        >
                          Test Keys
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={resetApiKeys}
                          className="text-xs rounded-full border-white/30 bg-zinc-950 hover:bg-zinc-950 hover:shadow-[0_0_22px_rgba(255,255,255,0.2)] ring-1 ring-white/10 hover:ring-white/30 transition-all"
                        >
                          Reset
                        </Button>
                        <Button
                          onClick={saveApiKeys}
                          disabled={savingKeys}
                          size="sm"
                          className="text-xs rounded-full bg-white text-black hover:bg-white/90 shadow-[0_0_14px_rgba(255,255,255,0.45)] hover:shadow-[0_0_24px_rgba(255,255,255,0.65)] ring-1 ring-white/60 hover:ring-white/80 transition-all"
                        >
                          {savingKeys ? (
                            <>
                              <Loading03Icon size={14} className="mr-1 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>Save Keys</>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              </motion.div>

              {/* Agent Settings */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.25 }}
              >
                <Card id="agent-settings" className="bg-black/40 border border-white/20 rounded-3xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 font-normal text-white">
                      Agent Settings
                    </CardTitle>
                    <CardDescription className="text-md font-thin text-white/40">
                      Configure agent behavior
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div className="space-y-2 max-w-full">
                        <Label htmlFor="max-steps" className="text-sm font-normal">Max tool calls per run</Label>
                        <Input
                          id="max-steps"
                          type="text"
                          inputMode="numeric"
                          pattern="[0-9]*"
                          value={maxStepsInput}
                          onChange={(e) => {
                            const raw = e.target.value
                            const isDigitsOnly = /^\d*$/.test(raw)
                            setMaxStepsInput(raw)
                            if (!isDigitsOnly) { setMaxStepsInvalid(true); return }
                            if (raw === "") { setMaxStepsInvalid(true); setMaxSteps(0); return }
                            setMaxStepsInvalid(false)
                            setMaxSteps(Number(raw))
                          }}
                          onBlur={() => {
                            const raw = maxStepsInput.trim()
                            if (raw === "") {
                              const fallback = maxSteps > 0 ? maxSteps : 50
                              setMaxSteps(fallback)
                              setMaxStepsInput(String(fallback))
                              setMaxStepsInvalid(false)
                              return
                            }
                            const num = Number(raw.replace(/[^\d]/g, ""))
                            const bounded = isNaN(num) ? 1 : Math.max(1, Math.min(200, Math.floor(num)))
                            setMaxSteps(bounded)
                            setMaxStepsInput(String(bounded))
                            setMaxStepsInvalid(false)
                          }}
                          className={`rounded-full bg-transparent border ${maxStepsInvalid ? 'border-red-500/60 shadow-[0_0_12px_rgba(239,68,68,0.45)]' : 'border-white/20'} hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0`}
                        />
                        {maxStepsInvalid && (<p className="text-xs text-red-400">Numbers only. Range 1–200.</p>)}
                        <p className="text-xs text-muted-foreground w-full">Control how many tool calls the agent can make per run.</p>
                      </div>

                      <div className="space-y-2 max-w-full">
                        <Label htmlFor="max-failures" className="text-sm font-normal">Max consecutive failures</Label>
                        <Input
                          id="max-failures"
                          type="text"
                          inputMode="numeric"
                          pattern="[0-9]*"
                          value={consecutiveFailuresInput}
                          onChange={(e) => {
                            const raw = e.target.value
                            const isDigitsOnly = /^\d*$/.test(raw)
                            setConsecutiveFailuresInput(raw)
                            if (!isDigitsOnly) { setConsecutiveFailuresInvalid(true); return }
                            if (raw === "") { setConsecutiveFailuresInvalid(true); return }
                            setConsecutiveFailuresInvalid(false)
                          }}
                          onBlur={() => {
                            const raw = consecutiveFailuresInput.trim()
                            if (raw === "") {
                              const fallback = agentSettings.consecutive_failures > 0 ? agentSettings.consecutive_failures : 3
                              setConsecutiveFailuresInput(String(fallback))
                              setConsecutiveFailuresInvalid(false)
                              return
                            }
                            const num = Number(raw)
                            const bounded = Math.max(1, Math.min(10, Number.isFinite(num) ? Math.floor(num) : agentSettings.consecutive_failures))
                            setAgentSettings(prev => ({ ...prev, consecutive_failures: bounded }))
                            setConsecutiveFailuresInput(String(bounded))
                            setConsecutiveFailuresInvalid(false)
                          }}
                          className={`rounded-full bg-transparent border ${consecutiveFailuresInvalid ? 'border-red-500/60 shadow-[0_0_12px_rgba(239,68,68,0.45)]' : 'border-white/20'} hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0`}
                        />
                        {consecutiveFailuresInvalid && (<p className="text-xs text-red-400">Numbers only. Range 1–10.</p>)}
                        <p className="text-xs text-muted-foreground w-full">Stop a run after repeated errors to avoid loops.</p>
                      </div>

                      <div className="space-y-2 max-w-full">
                        <Label htmlFor="cache-timeout" className="text-sm font-normal">Desktop cache timeout (s)</Label>
                        <Input
                          id="cache-timeout"
                          type="text"
                          inputMode="decimal"
                          value={cacheTimeoutInput}
                          onChange={(e) => {
                            const raw = e.target.value
                            setCacheTimeoutInput(raw)
                            if (raw === "") { setCacheTimeoutInvalid(true); return }
                            const isDecimal = /^\d*\.?\d*$/.test(raw)
                            setCacheTimeoutInvalid(!isDecimal)
                          }}
                          onBlur={() => {
                            const raw = cacheTimeoutInput.trim()
                            if (raw === "") {
                              const fallback = agentSettings.cache_timeout
                              setCacheTimeoutInput(fallback.toString())
                              setCacheTimeoutInvalid(false)
                              return
                            }
                            const num = Number(raw)
                            if (!Number.isFinite(num)) {
                              setCacheTimeoutInput(agentSettings.cache_timeout.toString())
                              setCacheTimeoutInvalid(false)
                              return
                            }
                            const bounded = Math.max(0.1, Math.min(10, num))
                            const formatted = Number(bounded.toFixed(2))
                            setAgentSettings(prev => ({ ...prev, cache_timeout: formatted }))
                            setCacheTimeoutInput(formatted.toString())
                            setCacheTimeoutInvalid(false)
                          }}
                          className={`rounded-full bg-transparent border ${cacheTimeoutInvalid ? 'border-red-500/60 shadow-[0_0_12px_rgba(239,68,68,0.45)]' : 'border-white/20'} hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0`}
                        />
                        {cacheTimeoutInvalid && (<p className="text-xs text-red-400">Use numbers only. Range 0.1–10.</p>)}
                        <p className="text-xs text-muted-foreground w-full">Set how long desktop and app snapshots stay cached.</p>
                      </div>

                      <Separator />

                      <div className="space-y-4">
                        <Label className="text-sm font-normal">Execution preferences</Label>
                        <div className="space-y-3">
                          <div className="space-y-2">
                            <Label htmlFor="default-browser" className="text-sm font-normal">
                              Default browser
                            </Label>
                            <Select
                              value={agentSettings.browser}
                              onValueChange={(value) => setAgentSettings(prev => ({ ...prev, browser: value as BrowserOption }))}
                            >
                              <SelectTrigger
                                id="default-browser"
                                className="rounded-full bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0"
                              >
                                <SelectValue placeholder="Select browser" />
                              </SelectTrigger>
                              <SelectContent className="bg-zinc-950 border border-white/20 rounded-2xl">
                                <SelectItem value="chrome" className="text-white hover:bg-white/10 rounded-3xl pb-2">
                                  Google Chrome
                                </SelectItem>
                                <SelectItem value="edge" className="text-white hover:bg-white/10 rounded-3xl pb-2">
                                  Microsoft Edge
                                </SelectItem>
                                <SelectItem value="firefox" className="text-white hover:bg-white/10 rounded-3xl pb-2">
                                  Mozilla Firefox
                                </SelectItem>
                              </SelectContent>
                            </Select>
                            <p className="text-xs text-muted-foreground">Choose which browser the agent launches for web tasks.</p>
                          </div>

                      <div className="space-y-2">
                        <Label htmlFor="model-select" className="text-sm font-normal">
                          Language model
                        </Label>
                        <Select
                          value={agentSettings.model}
                          onValueChange={(value) => setAgentSettings(prev => ({ ...prev, model: value as ModelOption }))}
                        >
                          <SelectTrigger
                            id="model-select"
                            className="rounded-full bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0"
                          >
                            <SelectValue placeholder="Select Gemini model" />
                          </SelectTrigger>
                          <SelectContent className="bg-zinc-950 border border-white/20 rounded-2xl">
                            {MODEL_OPTIONS.map(option => (
                              <SelectItem key={option} value={option} className="text-white hover:bg-white/10 rounded-3xl pb-2">
                                {option}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">Toggle between Gemini 2.5 and 2.0 variants to balance quality and speed.</p>
                      </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="literal-mode-toggle" className="text-sm font-normal cursor-pointer">
                                Literal mode
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Keep plans concise and action-focused when enabled.
                              </p>
                            </div>
                            <button
                              id="literal-mode-toggle"
                              type="button"
                              onClick={() => setAgentSettings(prev => ({ ...prev, literal_mode: !prev.literal_mode }))}
                              aria-pressed={agentSettings.literal_mode}
                              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black ${
                                agentSettings.literal_mode ? 'bg-white' : 'bg-gray-600'
                              }`}
                            >
                              <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${
                                  agentSettings.literal_mode ? 'translate-x-6' : 'translate-x-1'
                                }`}
                              />
                            </button>
                          </div>
                        </div>
                      </div>

                      <Separator />

                      <div className="space-y-4">
                        <Label className="text-sm font-normal">AI Features</Label>
                        
                        {/* Screenshot analysis toggle disabled */}
                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="enable-activity-tracking" className="text-sm font-normal cursor-pointer">
                                Activity Tracking
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Track app usage and productivity metrics
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setAgentSettings(prev => ({ ...prev, enable_activity_tracking: !prev.enable_activity_tracking }))}
                              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black ${
                                agentSettings.enable_activity_tracking ? 'bg-white' : 'bg-gray-600'
                              }`}
                            >
                              <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${
                                  agentSettings.enable_activity_tracking ? 'translate-x-6' : 'translate-x-1'
                                }`}
                              />
                            </button>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="enable-vision" className="text-sm font-normal cursor-pointer">
                                Vision Mode
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Use AI vision to analyze screenshots during tasks
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setAgentSettings(prev => ({ ...prev, enable_vision: !prev.enable_vision }))}
                              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black ${
                                agentSettings.enable_vision ? 'bg-white' : 'bg-gray-600'
                              }`}
                            >
                              <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${
                                  agentSettings.enable_vision ? 'translate-x-6' : 'translate-x-1'
                                }`}
                              />
                            </button>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="enable-conversation" className="text-sm font-normal cursor-pointer">
                                Conversation Mode
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Maintain conversation context across queries
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setAgentSettings(prev => ({ ...prev, enable_conversation: !prev.enable_conversation }))}
                              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black ${
                                agentSettings.enable_conversation ? 'bg-white' : 'bg-gray-600'
                              }`}
                            >
                              <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${
                                  agentSettings.enable_conversation ? 'translate-x-6' : 'translate-x-1'
                                }`}
                              />
                            </button>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                              <Label htmlFor="enable-tts" className="text-sm font-normal cursor-pointer">
                                Text-to-Speech
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Speak agent responses aloud
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setAgentSettings(prev => ({ ...prev, enable_tts: !prev.enable_tts }))}
                              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black ${
                                agentSettings.enable_tts ? 'bg-white' : 'bg-gray-600'
                              }`}
                            >
                              <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${
                                  agentSettings.enable_tts ? 'translate-x-6' : 'translate-x-1'
                                }`}
                              />
                            </button>
                          </div>
                        </div>

                        <div className="space-y-2 pt-2">
                          <Label htmlFor="tts-voice-id" className="text-sm font-normal">
                            TTS voice ID
                          </Label>
                          <Input
                            id="tts-voice-id"
                            type="text"
                            value={agentSettings.tts_voice_id}
                            onChange={(e) => setAgentSettings(prev => ({ ...prev, tts_voice_id: e.target.value }))}
                            disabled={!agentSettings.enable_tts}
                            placeholder="21m00Tcm4TlvDq8ikWAM"
                            className="rounded-full bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-60"
                          />
                          <p className="text-xs text-muted-foreground">
                            Use a voice ID from ElevenLabs. Leave the default if unsure.
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-end pt-2">
                        <Button onClick={saveAgentSettings} disabled={savingAgentSettings} size="sm" className="text-xs rounded-full bg-white text-black hover:bg-white/90 shadow-[0_0_14px_rgba(255,255,255,0.45)] hover:shadow-[0_0_24px_rgba(255,255,255,0.65)] ring-1 ring-white/60 hover:ring-white/80 transition-all">
                          {savingAgentSettings ? (
                            <>
                              <Loading03Icon size={14} className="mr-1 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>Save Agent Settings</>
                          )}
                        </Button>
                      </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Audio Settings Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
              >
                <Card id="audio-settings" className="bg-black/40 border border-white/20 rounded-3xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 font-normal text-white">
                      {/* <BotIcon size={20} /> */}
                      Audio Settings
                    </CardTitle>
                    <CardDescription className="text-md font-thin text-white/40">
                      Configure microphone and speaker settings for voice interactions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* Microphone Permission */}
                      <div className="space-y-2">
                        <Label className="text-sm font-normal">
                          Microphone Permission
                        </Label>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {audioDevices.hasPermission ? (
                              <Tick02Icon size={16} className="text-green-400" />
                            ) : (
                              <Cancel01Icon size={16} className="text-red-400" />
                            )}
                            <span className="text-sm">
                              {audioDevices.hasPermission ? "Granted" : "Not Granted"}
                            </span>
                          </div>
                          <div className="flex gap-2">
                            {!audioDevices.hasPermission && (
                              <Button
                                onClick={async () => {
                                  const granted = await audioDevices.requestPermission()
                                  if (granted) {
                                    toast({
                                      title: "Permission Granted",
                                      description: "Microphone access has been granted",
                                    })
                                  } else {
                                    toast({
                                      title: "Permission Denied",
                                      description: "Microphone access was denied",
                                      variant: "destructive"
                                    })
                                  }
                                }}
                                disabled={audioDevices.isLoading}
                                size="sm"
                                variant="outline"
                                className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30 transition-all focus:outline-none focus:ring-0 focus-visible:ring-0"
                              >
                                {audioDevices.isLoading ? (
                                  <>
                                    <Loading01Icon size={14} className="mr-1 animate-spin" />
                                    Requesting...
                                  </>
                                ) : (
                                  <>
                                    <Mic02Icon size={14} className="mr-1" />
                                    Grant Permission
                                  </>
                                )}
                              </Button>
                            )}
                            <Button
                              onClick={audioDevices.refreshDevices}
                              disabled={audioDevices.isLoading}
                              size="sm"
                              variant="outline"
                              className="text-xs rounded-full border-white/30 bg-zinc-950 hover:bg-zinc-950 hover:shadow-[0_0_22px_rgba(255,255,255,0.2)] ring-1 ring-white/10 hover:ring-white/30 transition-all"
                            >
                              {/* <Loading01Icon size={14} className="mr-1" /> */}
                              Refresh
                            </Button>
                          </div>
                        </div>
                        {audioDevices.error && (
                          <p className="text-xs text-red-400">{audioDevices.error}</p>
                        )}
                      </div>

                      <Separator />

                      {/* Microphone Input Selector */}
                      <div className="space-y-2">
                        <Label htmlFor="microphone-input" className="text-sm font-normal">
                          Microphone Input
                        </Label>
                        <Select
                          value={audioDevices.selectedInputDevice || ""}
                          onValueChange={audioDevices.setSelectedInputDevice}
                          disabled={!audioDevices.hasPermission || audioDevices.isLoading}
                        >
                          <SelectTrigger 
                            id="microphone-input"
                            className="rounded-full bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0 "
                          >
                            <SelectValue placeholder="Select microphone..." />
                          </SelectTrigger>
                          <SelectContent className="bg-zinc-950 border border-white/20 rounded-2xl">
                            {audioDevices.inputDevices
                              .filter(device => device.deviceId && device.deviceId.trim() !== '')
                              .map((device) => (
                              <SelectItem 
                                key={device.deviceId} 
                                value={device.deviceId}
                                className="text-white hover:bg-white/10 rounded-3xl pb-2"
                              >
                                <div className="flex items-center gap-2 ">
                                  <Mic02Icon size={14} />
                                  {device.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-gray-500">
                          {audioDevices.inputDevices.length} microphone(s) detected
                        </p>
                      </div>

                      <Separator />

                      {/* Audio Output Selector */}
                      <div className="space-y-2">
                        <Label htmlFor="audio-output" className="text-sm font-normal">
                          Audio Output
                        </Label>
                        <Select
                          value={audioDevices.selectedOutputDevice || ""}
                          onValueChange={audioDevices.setSelectedOutputDevice}
                          disabled={audioDevices.isLoading}
                        >
                          <SelectTrigger 
                            id="audio-output"
                            className="rounded-full bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white focus:outline-none focus:ring-0 focus-visible:ring-0"
                          >
                            <SelectValue placeholder="Select speaker..." />
                          </SelectTrigger>
                          <SelectContent className="bg-black/90 border border-white/20 rounded-2xl">
                            {audioDevices.outputDevices
                              .filter(device => device.deviceId && device.deviceId.trim() !== '')
                              .map((device) => (
                              <SelectItem 
                                key={device.deviceId} 
                                value={device.deviceId}
                                className="text-white hover:bg-white/10 rounded-3xl pb-2"
                              >
                                <div className="flex items-center gap-2">
                                  <VolumeMute01Icon size={16} />
                                  {device.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-gray-500">
                          {audioDevices.outputDevices.length} speaker(s) detected
                        </p>
                      </div>

                      <Separator />

                      {/* Notification Sounds Toggle */}
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label htmlFor="notification-sounds-toggle" className="text-sm font-normal cursor-pointer">
                            Notification Sounds
                          </Label>
                          <p className="text-xs text-muted-foreground">
                            Play sounds when tasks start and complete
                          </p>
                        </div>
                        <button
                          id="notification-sounds-toggle"
                          type="button"
                          onClick={() => setNotificationSoundsEnabled(prev => !prev)}
                          aria-pressed={notificationSoundsEnabled}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black ${
                            notificationSoundsEnabled ? 'bg-white' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${
                              notificationSoundsEnabled ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>

                      <div className="flex items-center justify-between pt-4">
                        <div className="text-xs text-muted-foreground">
                          Audio settings are automatically saved
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              toast({
                                title: "Audio Test",
                                description: `Input: ${audioDevices.inputDevices.find(d => d.deviceId === audioDevices.selectedInputDevice)?.label || 'None'}, Output: ${audioDevices.outputDevices.find(d => d.deviceId === audioDevices.selectedOutputDevice)?.label || 'None'}`,
                              })
                            }}
                            className="text-xs rounded-full border-white/30 bg-zinc-950 hover:bg-zinc-950 hover:shadow-[0_0_22px_rgba(255,255,255,0.2)] ring-1 ring-white/10 hover:ring-white/30 transition-all"
                          >
                            Test Audio
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* System Status Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.4 }}
              >
                <Card id="system-status" className="bg-black/40 border border-white/20 rounded-3xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 font-normal text-white">
                      {/* <ComputerIcon size={20} /> */}
                      System Status
                    </CardTitle>
                    <CardDescription className="text-md font-thin text-white/40">
                      Current status of Yuki AI services
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Agent Status</span>
                        <Badge 
                          variant={systemStatus?.agent_ready ? "default" : "destructive"}
                          className={systemStatus?.agent_ready 
                            ? "rounded-full bg-white/10 text-white border border-white/30 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10"
                            : "rounded-full bg-red-500/20 text-red-300 border border-red-500/40 shadow-[0_0_14px_rgba(239,68,68,0.35)] hover:shadow-[0_0_24px_rgba(239,68,68,0.55)] ring-1 ring-red-500/20"
                          }
                        >
                          {systemStatus?.agent_ready ? "Available" : "No API Key"}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <button
                            type="button"
                            onClick={() => setShowRunningPrograms(!showRunningPrograms)}
                            className="inline-flex items-center gap-2 text-left"
                          >
                            <span className="text-sm underline-offset-2 underline ">Running Programs</span>
                            {systemStatus?.running_programs && systemStatus.running_programs.length > 0 && (
                              showRunningPrograms ? (
                                <ArrowUp01Icon size={17} />
                              ) : (
                                <ArrowDown01Icon size={17} />
                              )
                            )}
                          </button>
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant="secondary" 
                              className="rounded-full bg-white/10 text-white border border-white/30 shadow-[0_0_12px_rgba(255,255,255,0.35)]"
                            >
                              {systemStatus?.running_programs?.length || 0} active
                            </Badge>
                          </div>
                        </div>
                        
                        <AnimatePresence initial={false}>
                          {showRunningPrograms && systemStatus?.running_programs && systemStatus.running_programs.length > 0 && (
                            <motion.div
                              key="running-programs-list"
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.2 }}
                              className="space-y-2 pl-4  border-white/10 overflow-hidden"
                            >
                              {systemStatus.running_programs.map((program, index) => (
                                <motion.div
                                  key={program.id || index}
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  exit={{ opacity: 0, x: -10 }}
                                  transition={{ duration: 0.2, delay: index * 0.05 }}
                                  className="flex items-center justify-between p-2 rounded-full bg-black/20 border border-white/10"
                                >
                                  <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 flex items-center justify-center rounded-full bg-white shadow-[0_0_12px_rgba(255,255,255,0.65)]">
                                      <AiBrowserIcon size={16} className="text-black" />
                                    </div>
                                    <div className="flex gap-3">
                                      <span className="text-xs font-thin text-white">
                                        {program.title || program.name}
                                      </span>
                                      {program.name !== program.title && (
                                        <span className="text-xs text-gray-400 font-thin">
                                          {program.name}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <Badge variant="default" className="text-xs text-white bg-zinc-900">
                                    ID: {program.id}
                                  </Badge>
                                </motion.div>
                              ))}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>

                      <Separator />

                      <div className="flex items-center justify-between">
                        <span className="text-sm">Voice Mode</span>
                        <Badge 
                          variant={apiKeyInputs.deepgram_api_key ? "default" : "destructive"}
                          className={apiKeyInputs.deepgram_api_key 
                            ? "rounded-full bg-white/10 text-white border border-white/30 shadow-[0_0_12px_rgba(255,255,255,0.35)]"
                            : "rounded-full bg-red-500/20 text-red-300 border border-red-500/40 shadow-[0_0_14px_rgba(239,68,68,0.35)]"
                          }
                        >
                          {apiKeyInputs.deepgram_api_key ? "Available" : "No API Key"}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm">Text-to-Speech</span>
                        <Badge 
                          variant={apiKeyInputs.elevenlabs_api_key ? "default" : "destructive"}
                          className={apiKeyInputs.elevenlabs_api_key 
                            ? "rounded-full bg-white/10 text-white border border-white/30 shadow-[0_0_12px_rgba(255,255,255,0.35)]"
                            : "rounded-full bg-red-500/20 text-red-300 border border-red-500/40 shadow-[0_0_14px_rgba(239,68,68,0.35)]"
                          }
                        >
                          {apiKeyInputs.elevenlabs_api_key ? "Available" : "No API Key"}
                        </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
              </motion.div>
            </div>
          </div>
        </ScrollArea>
        </motion.div>
      </div>

      <Toaster />
    </div>
  )
}

