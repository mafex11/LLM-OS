"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { motion, AnimatePresence } from "framer-motion"
import { AppSidebar } from "@/components/layout/Sidebar"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { Loading01Icon, Settings01Icon, SidebarLeft01Icon, SidebarRight01Icon, Home01Icon, BotIcon, ArrowRight02Icon, TimeScheduleIcon, AiBrain01Icon } from "hugeicons-react"
import { useToast } from "@/hooks/use-toast"

export default function AgentSettingsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [showSidebar, setShowSidebar] = useState(true)
  const [savingAgentSettings, setSavingAgentSettings] = useState(false)
  const [maxSteps, setMaxSteps] = useState<number>(50)
  const [maxStepsInput, setMaxStepsInput] = useState<string>("50")
  const [maxStepsInvalid, setMaxStepsInvalid] = useState<boolean>(false)

  useEffect(() => { setMaxStepsInput(String(maxSteps)) }, [maxSteps])

  const saveAgentSettings = async () => {
    setSavingAgentSettings(true)
    try {
      const value = Number(maxSteps)
      const bounded = isNaN(value) ? 50 : Math.max(1, Math.min(200, Math.floor(value)))
      const response = await fetch("http://localhost:8000/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_steps: bounded })
      })
      if (response.ok) {
        toast({ title: "Agent settings saved", description: `Max tool calls set to ${bounded}.` })
        setMaxSteps(bounded)
      } else {
        toast({ title: "Error", description: "Failed to update agent settings.", variant: "destructive" })
      }
    } catch {
      toast({ title: "Backend Unavailable", description: "Cannot connect to backend. Ensure the server is running.", variant: "destructive" })
    } finally {
      setSavingAgentSettings(false)
    }
  }

  return (
    <div className="flex min-h-screen w-full ">
      <div className="relative z-10 w-full">
        <AppSidebar isOpen={showSidebar}>
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

          <ScrollArea className="flex-1 px-2 py-2">
            <div className="space-y-1">
              <div className="px-3 py-2 text-sm font-normal text-muted-foreground">
                Agent Settings
              </div>
              <Button 
                variant="ghost" 
                className="group w-full justify-start gap-2 hover:bg-zinc-950"
                onClick={() => document.getElementById('agent-settings')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Agent Settings
                <span className="ml-auto opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                  <ArrowRight02Icon size={14} />
                </span>
              </Button>
            </div>
          </ScrollArea>

          <div className="border-t border-white/10 mx-2 p-2 space-y-1">
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-black/30" onClick={() => router.push("/")}> 
              <Home01Icon size={16} />
              Home
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-black/30" onClick={() => router.push("/agent-settings")}>
              <AiBrain01Icon size={16} />
              Agent Settings
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-black/30" onClick={() => router.push("/settings")}>
              <Settings01Icon size={16} />
              Settings
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/scheduled")}>
              <TimeScheduleIcon size={16} />
              Scheduled Tasks
            </Button>
          </div>
        </AppSidebar>

        <div className={`${showSidebar ? 'pl-64' : 'pl-0'} flex-1 flex flex-col`}>
          <motion.div
            className="border-b border-white/10 px-4 py-3 flex items-center justify-between bg-black/20 backdrop-blur-sm sticky top-0 z-10"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-3">
              <div className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors" onClick={() => setShowSidebar(!showSidebar)}>
                {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
              </div>
              <div className="flex items-center gap-2">
                <motion.div animate={{ rotate: [0, 10, -10, 0] }} transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}>
                  <BotIcon size={24} />
                </motion.div>
                <h1 className="text-lg font-normal hidden sm:block">Agent Settings</h1>
              </div>
            </div>
          </motion.div>

          <ScrollArea className="flex-1 px-2 sm:px-4">
            <div className="max-w-4xl mx-auto py-4 sm:py-8">
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.15 }}>
                <Card id="agent-settings" className="bg-black/40 border border-white/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 font-normal text-white">
                      Agent Settings
                    </CardTitle>
                    <CardDescription>Configure your agent's settings</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
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
                            setMaxStepsInvalid(false)
                            const num = raw === "" ? 0 : Number(raw)
                            setMaxSteps(num)
                          }}
                          onBlur={() => {
                            const num = Number(maxStepsInput.replace(/[^\d]/g, ""))
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

                      <div className="flex items-center justify-end">
                        <Button onClick={saveAgentSettings} disabled={savingAgentSettings} size="sm" className="text-xs rounded-full bg-white text-black hover:bg-white/90 shadow-[0_0_14px_rgba(255,255,255,0.45)] hover:shadow-[0_0_24px_rgba(255,255,255,0.65)] ring-1 ring-white/60 hover:ring-white/80 transition-all">
                          {savingAgentSettings ? (<><Loading01Icon size={14} className="mr-1 animate-spin" />Saving...</>) : (<>Save Agent Settings</>)}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}


