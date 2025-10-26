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
  Cancel01Icon
} from "hugeicons-react"
import { useToast } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { useAudioDevices } from "@/hooks/useAudioDevices"
// Removed useApiKeys import - using config file only
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
  const audioDevices = useAudioDevices()
  // Removed context dependency - using config file only
  const [showSidebar, setShowSidebar] = useState(true)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [showApiKeys, setShowApiKeys] = useState({
    google_api_key: false,
    elevenlabs_api_key: false,
    deepgram_api_key: false
  })
  const [savingKeys, setSavingKeys] = useState(false)
  const [apiKeyInputs, setApiKeyInputs] = useState<ApiKeys>({
    google_api_key: "",
    elevenlabs_api_key: "",
    deepgram_api_key: ""
  })

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/status")
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
      const response = await fetch("http://localhost:8000/api/config/keys")
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

  useEffect(() => {
    fetchSystemStatus()
    loadApiKeys()
    const interval = setInterval(fetchSystemStatus, 5000)
    return () => clearInterval(interval)
  }, [loadApiKeys])

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
      // Save to backend config file only
      const response = await fetch("http://localhost:8000/api/config/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(apiKeyInputs),
      })

      if (response.ok) {
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
                <span className="text-sm font-semibold">Yuki AI</span>
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
                    Configure your API keys for Yuki AI services
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
                          value={apiKeyInputs.google_api_key}
                          onChange={(e) => handleApiKeyChange('google_api_key', e.target.value)}
                          placeholder="Enter your Google API key"
                          className="pr-10 bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white placeholder:text-gray-500"
                        />
                        <div className="absolute right-0 top-0 h-full flex">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-full px-2"
                            onClick={() => clearApiKey('google_api_key')}
                            disabled={!apiKeyInputs.google_api_key}
                          >
                            <Cancel01Icon size={14} />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-full px-2"
                            onClick={() => {
                              navigator.clipboard.writeText(apiKeyInputs.google_api_key)
                              toast({
                                title: "Copied!",
                                description: "Google API key copied to clipboard",
                              })
                            }}
                            disabled={!apiKeyInputs.google_api_key}
                          >
                            <FloppyDiskIcon size={14} />
                          </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                            className="h-full px-2"
                          onClick={() => setShowApiKeys({ ...showApiKeys, google_api_key: !showApiKeys.google_api_key })}
                        >
                          {showApiKeys.google_api_key ? <ViewOffIcon size={16} /> : <ViewIcon size={16} />}
                        </Button>
                      </div>
                      </div>
                      <div className="flex items-center justify-between">
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
                        {apiKeyInputs.google_api_key && (
                          <Badge variant="secondary" className="text-xs">
                            ✓ Configured
                          </Badge>
                        )}
                      </div>
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
                          value={apiKeyInputs.elevenlabs_api_key}
                          onChange={(e) => handleApiKeyChange('elevenlabs_api_key', e.target.value)}
                          placeholder="Enter your ElevenLabs API key (optional)"
                          className="pr-10 bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white placeholder:text-gray-500"
                        />
                        <div className="absolute right-0 top-0 h-full flex">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-full px-2"
                            onClick={() => clearApiKey('elevenlabs_api_key')}
                            disabled={!apiKeyInputs.elevenlabs_api_key}
                          >
                            <Cancel01Icon size={14} />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-full px-2"
                            onClick={() => {
                              navigator.clipboard.writeText(apiKeyInputs.elevenlabs_api_key)
                              toast({
                                title: "Copied!",
                                description: "ElevenLabs API key copied to clipboard",
                              })
                            }}
                            disabled={!apiKeyInputs.elevenlabs_api_key}
                          >
                            <FloppyDiskIcon size={14} />
                          </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                            className="h-full px-2"
                          onClick={() => setShowApiKeys({ ...showApiKeys, elevenlabs_api_key: !showApiKeys.elevenlabs_api_key })}
                        >
                          {showApiKeys.elevenlabs_api_key ? <ViewOffIcon size={16} /> : <ViewIcon size={16} />}
                        </Button>
                      </div>
                      </div>
                      <div className="flex items-center justify-between">
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
                        {apiKeyInputs.elevenlabs_api_key && (
                          <Badge variant="secondary" className="text-xs">
                            ✓ Configured
                          </Badge>
                        )}
                      </div>
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
                          value={apiKeyInputs.deepgram_api_key}
                          onChange={(e) => handleApiKeyChange('deepgram_api_key', e.target.value)}
                          placeholder="Enter your Deepgram API key (optional)"
                          className="pr-10 bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white placeholder:text-gray-500"
                        />
                        <div className="absolute right-0 top-0 h-full flex">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-full px-2"
                            onClick={() => clearApiKey('deepgram_api_key')}
                            disabled={!apiKeyInputs.deepgram_api_key}
                          >
                            <Cancel01Icon size={14} />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-full px-2"
                            onClick={() => {
                              navigator.clipboard.writeText(apiKeyInputs.deepgram_api_key)
                              toast({
                                title: "Copied!",
                                description: "Deepgram API key copied to clipboard",
                              })
                            }}
                            disabled={!apiKeyInputs.deepgram_api_key}
                          >
                            <FloppyDiskIcon size={14} />
                          </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                            className="h-full px-2"
                          onClick={() => setShowApiKeys({ ...showApiKeys, deepgram_api_key: !showApiKeys.deepgram_api_key })}
                        >
                          {showApiKeys.deepgram_api_key ? <ViewOffIcon size={16} /> : <ViewIcon size={16} />}
                        </Button>
                      </div>
                      </div>
                      <div className="flex items-center justify-between">
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
                        {apiKeyInputs.deepgram_api_key && (
                          <Badge variant="secondary" className="text-xs">
                            ✓ Configured
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-4">
                      <div className="text-xs text-muted-foreground">
                        Edit API keys above, then click Save to apply changes
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            toast({
                              title: "API Keys Status",
                              description: `Google: ${apiKeyInputs.google_api_key ? '✓' : '✗'}, ElevenLabs: ${apiKeyInputs.elevenlabs_api_key ? '✓' : '✗'}, Deepgram: ${apiKeyInputs.deepgram_api_key ? '✓' : '✗'}`,
                            })
                          }}
                          className="text-xs"
                        >
                          Test Keys
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={resetApiKeys}
                          className="text-xs"
                        >
                          Reset
                        </Button>
                        <Button
                          onClick={saveApiKeys}
                          disabled={savingKeys}
                          size="sm"
                          className="text-xs"
                        >
                          {savingKeys ? (
                            <>
                              <Loading01Icon size={14} className="mr-1 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <FloppyDiskIcon size={14} className="mr-1" />
                              Save Keys
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
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
                <Card className="bg-transparent border border-white/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BotIcon size={20} />
                      Audio Settings
                    </CardTitle>
                    <CardDescription>
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
                            <Settings01Icon size={16} />
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
                                className="text-xs"
                              >
                                {audioDevices.isLoading ? (
                                  <>
                                    <Loading01Icon size={14} className="mr-1 animate-spin" />
                                    Requesting...
                                  </>
                                ) : (
                                  <>
                                    <BotIcon size={14} className="mr-1" />
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
                              className="text-xs"
                            >
                              <Loading01Icon size={14} className="mr-1" />
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
                            className="bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white"
                          >
                            <SelectValue placeholder="Select microphone..." />
                          </SelectTrigger>
                          <SelectContent className="bg-black/90 border border-white/20">
                            {audioDevices.inputDevices.map((device) => (
                              <SelectItem 
                                key={device.deviceId} 
                                value={device.deviceId}
                                className="text-white hover:bg-white/10"
                              >
                                <div className="flex items-center gap-2">
                                  <BotIcon size={14} />
                                  {device.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
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
                            className="bg-transparent border border-white/20 hover:border-white/30 focus:border-white/40 text-white"
                          >
                            <SelectValue placeholder="Select speaker..." />
                          </SelectTrigger>
                          <SelectContent className="bg-black/90 border border-white/20">
                            {audioDevices.outputDevices.map((device) => (
                              <SelectItem 
                                key={device.deviceId} 
                                value={device.deviceId}
                                className="text-white hover:bg-white/10"
                              >
                                <div className="flex items-center gap-2">
                                  <ComputerIcon size={14} />
                                  {device.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          {audioDevices.outputDevices.length} speaker(s) detected
                        </p>
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
                            className="text-xs"
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
                <Card className="bg-transparent border border-white/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <ComputerIcon size={20} />
                      System Status
                    </CardTitle>
                    <CardDescription>
                      Current status of Yuki AI services
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Agent Status</span>
                        <Badge variant={systemStatus?.agent_ready ? "default" : "destructive"}>
                          {systemStatus?.agent_ready ? "✓ Ready" : "✗ Not Ready"}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Running Programs</span>
                        <Badge variant="secondary">
                          {systemStatus?.running_programs?.length || 0} active
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm">Voice Mode</span>
                        <Badge variant={apiKeyInputs.deepgram_api_key ? "default" : "secondary"}>
                          {apiKeyInputs.deepgram_api_key ? "✓ Available" : "⚠ No API Key"}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm">Text-to-Speech</span>
                        <Badge variant={apiKeyInputs.elevenlabs_api_key ? "default" : "secondary"}>
                          {apiKeyInputs.elevenlabs_api_key ? "✓ Available" : "⚠ No API Key"}
                        </Badge>
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
    </div>
  )
}

