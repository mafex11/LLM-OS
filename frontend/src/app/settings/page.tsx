"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
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
  Home01Icon
} from "hugeicons-react"
import { useToast } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { useApiKeys } from "@/contexts/ApiKeyContext"
import { motion, AnimatePresence } from "framer-motion"
import Image from "next/image"

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

export default function SettingsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { theme, setTheme } = useTheme()
  const { apiKeys, updateApiKey, hasApiKey } = useApiKeys()
  const [showSidebar, setShowSidebar] = useState(true)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [showApiKeys, setShowApiKeys] = useState({
    google_api_key: false,
    elevenlabs_api_key: false,
    deepgram_api_key: false
  })
  const [savingKeys, setSavingKeys] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [pendingApiKey, setPendingApiKey] = useState("")
  const [pendingApiKeyType, setPendingApiKeyType] = useState<keyof ApiKeys | null>(null)

  useEffect(() => {
    fetchSystemStatus()
    fetchApiKeys()
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

  const fetchApiKeys = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/config/keys")
      if (response.ok) {
        const data = await response.json()
        // Update context with fetched API keys
        updateApiKey('google_api_key', data.google_api_key || "")
        updateApiKey('elevenlabs_api_key', data.elevenlabs_api_key || "")
        updateApiKey('deepgram_api_key', data.deepgram_api_key || "")
      }
    } catch (error) {
      console.error("Failed to fetch API keys:", error)
    }
  }

  const handleApiKeyChange = (keyType: keyof ApiKeys, value: string) => {
    setPendingApiKey(value)
    setPendingApiKeyType(keyType)
    setShowConfirmDialog(true)
  }

  const confirmApiKeyChange = async () => {
    if (!pendingApiKeyType) return
    
    updateApiKey(pendingApiKeyType, pendingApiKey)
    setShowConfirmDialog(false)
    
    // Save to backend for backup (optional)
    setSavingKeys(true)
    try {
      const updatedKeys = {
        ...apiKeys,
        [pendingApiKeyType]: pendingApiKey
      }
      
      const response = await fetch("http://localhost:8000/api/config/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updatedKeys),
      })

      if (response.ok) {
        toast({
          title: "Success",
          description: `${pendingApiKeyType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} API key saved!`,
        })
      } else {
        // Even if backend save fails, the frontend key is still saved
        toast({
          title: "Success",
          description: `${pendingApiKeyType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} API key saved!`,
        })
      }
    } catch (error) {
      // Even if backend save fails, the frontend key is still saved
      toast({
        title: "Success",
        description: `${pendingApiKeyType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} API key saved!`,
      })
    } finally {
      setSavingKeys(false)
    }
  }

  const cancelApiKeyChange = () => {
    setShowConfirmDialog(false)
    setPendingApiKey("")
    setPendingApiKeyType(null)
  }

  return (
    <div className="flex h-screen relative">
      {/* Crimson Depth Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          background: "radial-gradient(125% 125% at 50% 100%, #000000 40%, #2b0707 100%)",
        }}
      />
      <div className="relative z-10 flex w-full h-full">
      <AnimatePresence mode="wait">
        <motion.div 
          className={`${showSidebar ? 'w-64' : 'w-0'} transition-all duration-300 border-r border-white/10 bg-black/20 backdrop-blur-sm flex flex-col overflow-hidden`}
          initial={false}
          animate={{ width: showSidebar ? 256 : 0 }}
          transition={{ duration: 0.3 }}
        >
        {showSidebar && (
          <>
            {/* Sidebar Header */}
            <div className="p-4 border-b border-white/10 mx-2 space-y-4">
              <div className="flex items-center gap-2 px-2">
                <Image src="/logo.svg" alt="Logo" width={30} height={30} className="flex-shrink-0 rounded-full" />
                <span className="text-sm font-semibold">Netra</span>
              </div>
              <Button 
                onClick={() => router.push("/chat")} 
                className="w-full gap-2 hover:bg-black/20 backdrop-blur-sm border text-center justify-center border-white/20 hover:border-white/30" 
                variant="ghost"
              >
                Back to Chat
              </Button>
            </div>

            {/* Sidebar Content */}
            <ScrollArea className="flex-1 px-2 py-2">
              <div className="space-y-1">
                <div className="px-3 py-2 text-sm font-normal text-muted-foreground">
                  Settings
                </div>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-2 bg-black/60"
                >
                  <Settings01Icon size={16} />
                  Configuration
                </Button>
              </div>
            </ScrollArea>

            {/* Sidebar Footer */}
            <div className="border-t border-white/10 mx-2 p-2 space-y-1">
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 hover:bg-black/30"
                onClick={() => router.push("/")}
              >
                <Home01Icon size={16} />
                Home
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 hover:bg-black/30"
                onClick={() => router.push("/settings")}
              >
                <Settings01Icon size={16} />
                Settings
              </Button>
            </div>
          </>
        )}
        </motion.div>
        </AnimatePresence>

        <div className="flex-1 flex flex-col">
        <motion.div 
          className="border-b border-white/10 px-4 py-3 flex items-center justify-between bg-black/20 backdrop-blur-sm sticky top-0 z-10"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center gap-3">
            <div
              className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
            </div>
            <div className="flex items-center gap-2">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              >
                <Settings01Icon size={24} />
              </motion.div>
              <h1 className="text-lg font-normal hidden sm:block">Settings</h1>
            </div>
          </div>
        </motion.div>

        <ScrollArea className="flex-1 px-2 sm:px-4">
          <div className="max-w-4xl mx-auto py-4 sm:py-8">
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
              <Card className="bg-transparent border border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key01Icon size={20} />
                    API Keys
                  </CardTitle>
                  <CardDescription>
                    Configure your API keys for Netra services
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="google_api_key" className="text-sm font-normal">
                        Google API Key <span className="text-red-500">*</span>
                      </Label>
                      <div className="relative">
                        <Input
                          id="google_api_key"
                          type={showApiKeys.google_api_key ? "text" : "password"}
                          value={apiKeys.google_api_key}
                          onChange={(e) => handleApiKeyChange('google_api_key', e.target.value)}
                          placeholder="Enter your Google API key"
                          className="pr-10 bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white placeholder:text-gray-500"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys({ ...showApiKeys, google_api_key: !showApiKeys.google_api_key })}
                        >
                          {showApiKeys.google_api_key ? <ViewOffIcon size={16} /> : <ViewIcon size={16} />}
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
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

                    <Separator />

                    <div className="space-y-2">
                      <Label htmlFor="elevenlabs_api_key" className="text-sm font-normal">
                        ElevenLabs API Key
                      </Label>
                      <div className="relative">
                        <Input
                          id="elevenlabs_api_key"
                          type={showApiKeys.elevenlabs_api_key ? "text" : "password"}
                          value={apiKeys.elevenlabs_api_key}
                          onChange={(e) => handleApiKeyChange('elevenlabs_api_key', e.target.value)}
                          placeholder="Enter your ElevenLabs API key (optional)"
                          className="pr-10 bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white placeholder:text-gray-500"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys({ ...showApiKeys, elevenlabs_api_key: !showApiKeys.elevenlabs_api_key })}
                        >
                          {showApiKeys.elevenlabs_api_key ? <ViewOffIcon size={16} /> : <ViewIcon size={16} />}
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
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
                      <div className="relative">
                        <Input
                          id="deepgram_api_key"
                          type={showApiKeys.deepgram_api_key ? "text" : "password"}
                          value={apiKeys.deepgram_api_key}
                          onChange={(e) => handleApiKeyChange('deepgram_api_key', e.target.value)}
                          placeholder="Enter your Deepgram API key (optional)"
                          className="pr-10 bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white placeholder:text-gray-500"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys({ ...showApiKeys, deepgram_api_key: !showApiKeys.deepgram_api_key })}
                        >
                          {showApiKeys.deepgram_api_key ? <ViewOffIcon size={16} /> : <ViewIcon size={16} />}
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
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

                    <div className="text-xs text-muted-foreground text-center">
                      API key will be saved automatically when you confirm the change
                    </div>
                  </div>
                </CardContent>
              </Card>
              </motion.div>
            </div>
          </div>
        </ScrollArea>
        </div>
      </div>

      <Toaster />

      {/* Confirm Dialog */}
      {showConfirmDialog && pendingApiKeyType && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background border rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2">Confirm API Key Change</h3>
            <p className="text-muted-foreground mb-4">
              Are you sure you want to update your {pendingApiKeyType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} API key? This will take effect immediately.
            </p>
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={cancelApiKeyChange}
                disabled={savingKeys}
              >
                Cancel
              </Button>
              <Button
                onClick={confirmApiKeyChange}
                disabled={savingKeys}
              >
                {savingKeys ? (
                  <>
                    <Loading01Icon size={16} className="mr-2 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Confirm"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

