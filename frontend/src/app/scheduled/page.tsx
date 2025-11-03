"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useRouter } from "next/navigation"
import { AppSidebar } from "@/components/layout/Sidebar"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { 
  PlusSignIcon,
  PencilEdit02Icon,
  Delete02Icon,
  Home01Icon,
  Settings01Icon,
  BotIcon,
  SidebarLeft01Icon,
  SidebarRight01Icon,
  CheckmarkCircle01Icon,
  CancelCircleIcon,
  Cancel01Icon,
  Tick02Icon
} from "hugeicons-react"
import { motion } from "framer-motion"
import Image from "next/image"

type ScheduledTask = {
  id: string
  name: string
  delay_seconds?: number | null
  run_at?: string | null
  status: string
  created_at: string
  scheduled_for?: string | null
  last_error?: string | null
}

export default function ScheduledTasksPage() {
  const router = useRouter()
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [loading, setLoading] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<ScheduledTask | null>(null)
  const [name, setName] = useState("")
  const [delaySeconds, setDelaySeconds] = useState<string>("")
  const [runAt, setRunAt] = useState<string>("")
  const [taskText, setTaskText] = useState("")
  const [delayMinutes, setDelayMinutes] = useState<string>("")
  const [dateInput, setDateInput] = useState<string>("")
  const [timeInput, setTimeInput] = useState<string>("")
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const fetchTasks = async () => {
    try {
      const r = await fetch("http://localhost:8000/api/scheduled-tasks")
      if (r.ok) {
        const data = await r.json()
        setTasks(data)
      }
    } catch {}
  }

  useEffect(() => { fetchTasks() }, [])

  const openCreate = () => {
    setEditingTask(null)
    setName("")
    setDelaySeconds("")
    setRunAt("")
    setDateInput("")
    setTimeInput("")
    setDialogOpen(true)
  }

  const openEdit = (task: ScheduledTask) => {
    setEditingTask(task)
    setName(task.name)
    setDelaySeconds(task.delay_seconds != null ? String(task.delay_seconds) : "")
    setRunAt(task.run_at || "")
    setDialogOpen(true)
  }

  const saveTask = async () => {
    if (!name.trim()) return
    setLoading(true)
    try {
      const body: any = { name }
      const delayVal = delaySeconds.trim()
      const runAtVal = runAt.trim()
      if (dateInput && timeInput) {
        body.run_at = `${dateInput}T${timeInput}:00`
      } else {
        if (delayVal) body.delay_seconds = Number(delayVal)
        if (runAtVal) body.run_at = runAtVal
      }
      if (editingTask) {
        const r = await fetch(`http://localhost:8000/api/scheduled-tasks/${editingTask.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        if (r.ok) { setDialogOpen(false); await fetchTasks() }
      } else {
        const r = await fetch("http://localhost:8000/api/scheduled-tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        if (r.ok) { setDialogOpen(false); await fetchTasks() }
      }
    } finally { setLoading(false) }
  }

  const deleteTask = async (id: string) => {
    setLoading(true)
    try { await fetch(`http://localhost:8000/api/scheduled-tasks/${id}`, { method: "DELETE" }); await fetchTasks() } finally { setLoading(false) }
  }

  const cancelTask = async (id: string) => {
    setLoading(true)
    try { await fetch(`http://localhost:8000/api/scheduled-tasks/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "cancelled" }) }); await fetchTasks() } finally { setLoading(false) }
  }

  const repeatTask = async (id: string) => {
    setLoading(true)
    try { await fetch(`http://localhost:8000/api/scheduled-tasks/${id}/repeat`, { method: "POST" }); await fetchTasks() } finally { setLoading(false) }
  }

  const badgeVariant = (status: string) => {
    switch ((status || "").toLowerCase()) {
      case "scheduled": return "outline"
      case "running": return "default"
      case "completed": return "secondary"
      case "failed": return "destructive"
      case "cancelled": return "outline"
      default: return "outline"
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
                  Sections
                </div>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-2 bg-black/60"
                  onClick={() => document.getElementById('schedule-task')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                >
                  Schedule Task
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-2"
                  onClick={() => document.getElementById('upcoming-tasks')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                >
                  Upcoming Tasks
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-2"
                  onClick={() => document.getElementById('task-history')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                >
                  Task History
                </Button>
              </div>
            </ScrollArea>
            <div className="border-t border-white/10 mx-2 p-2 space-y-1">
              <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-black/30" onClick={() => router.push("/")}>
                <Home01Icon size={16} />
                Home
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-black/30" onClick={() => router.push("/agent-settings")}>
                <BotIcon size={16} />
                Agent Settings
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2 hover:bg-black/30" onClick={() => router.push("/settings")}>
                <Settings01Icon size={16} />
                Settings
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
              <div className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors" onClick={() => { setShowSidebar(!showSidebar) }}>
                {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
              </div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-normal hidden sm:block">Scheduled Tasks</h1>
              </div>
            </div>
            {/* New button removed as per requirements */}
          </motion.div>
          <ScrollArea className="flex-1 px-2 sm:px-4 pb-8">
            <div className="max-w-4xl mx-auto py-4 sm:py-8 space-y-6">
              <Card id="schedule-task" className="bg-black/40 border border-white/20 ">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 font-normal text-white">Schedule Task</CardTitle>
                  <CardDescription>Create a new scheduled task by selecting date and time</CardDescription>
                </CardHeader>
                <CardContent>
                   <div className="space-y-6">
                     <div className="space-y-2">
                       <Label className="text-sm font-normal pl-2">Task description</Label>
                       <Input 
                         placeholder="e.g., go to Chrome, open YouTube, search Minecraft videos, play the first video"
                         value={taskText}
                         onChange={(e) => setTaskText(e.target.value)}
                         className="rounded-full bg-transparent border border-white/40 hover:border-white/30 text-white outline-none focus placeholder:text-gray-500"
                       />
                       <p className="text-xs text-muted-foreground">Use natural language; the agent will execute this at the scheduled time. Include timing in your description, e.g., "in 20 minutes" or "in 50 seconds"</p>
                     </div>

                     {/* Natural-language timing only; no explicit date/time fields */}

                    <div className="flex items-center justify-between pt-2">
                       <div className="text-xs text-muted-foreground"></div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => { setTaskText("") }}
                          className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30"
                        >
                          Reset
                        </Button>
                        <Button 
                          onClick={async () => {
                             if (!taskText.trim()) return
                            setLoading(true)
                            try {
                               const body: any = { query: taskText }
                               const r = await fetch("http://localhost:8000/api/scheduled-tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
                              if (r.ok) {
                                 setTaskText("")
                                await fetchTasks()
                              }
                            } finally { setLoading(false) }
                          }}
                           disabled={loading || !taskText.trim()}
                          size="sm"
                          className="text-xs rounded-full bg-white text-black hover:bg-white/90 shadow-[0_0_14px_rgba(255,255,255,0.45)] hover:shadow-[0_0_24px_rgba(255,255,255,0.65)] ring-1 ring-white/60 hover:ring-white/80"
                        >
                          Create
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card id="upcoming-tasks" className="bg-black/40 border border-white/20 ">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 font-normal text-white">Upcoming</CardTitle>
                  <CardDescription>Tasks that are scheduled or currently running</CardDescription>
                </CardHeader>
                <CardContent>
                  {tasks.filter(t => ["scheduled","running"].includes((t.status||"").toLowerCase())).length === 0 ? (
                    <div className="text-sm text-white/70">No upcoming tasks.</div>
                  ) : (
                    <div className="space-y-2">
                      {tasks.filter(t => ["scheduled","running"].includes((t.status||"").toLowerCase())).map((t) => (
                        <div key={t.id} className="flex items-center gap-2">
                          <div className="flex items-center justify-between bg-black/20 border border-white/10 rounded-full px-5 py-4 w-full overflow-hidden min-h-[64px]">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="flex flex-col min-w-0 flex-1 justify-center">
                                <button
                                  type="button"
                                  onClick={() => setExpandedIds(prev => { const next = new Set(prev); next.has(t.id) ? next.delete(t.id) : next.add(t.id); return next })}
                                  className={`${expandedIds.has(t.id) ? 'text-sm text-white whitespace-pre-wrap break-words text-left' : 'text-sm text-white truncate text-left cursor-pointer hover:underline'}`}
                                  title="Click to expand"
                                >
                                  {(t as any).query || t.name}
                                </button>
                                <div className="text-xs text-white/60 truncate">
                                  {(() => {
                                    const now = Date.now()
                                    if (t.run_at) {
                                      const target = new Date(t.run_at).getTime()
                                      const diff = Math.max(0, target - now)
                                      const mins = Math.floor(diff / 60000)
                                      const secs = Math.floor((diff % 60000) / 1000)
                                      return `Executes in ${mins}m ${secs}s`
                                    }
                                    if (t.delay_seconds != null) {
                                      const created = new Date(t.created_at).getTime()
                                      const target = created + (t.delay_seconds * 1000)
                                      const diff = Math.max(0, target - now)
                                      const mins = Math.floor(diff / 60000)
                                      const secs = Math.floor((diff % 60000) / 1000)
                                      return `Executes in ${mins}m ${secs}s`
                                    }
                                    return "Scheduled"
                                  })()}
                                </div>
                                {t.last_error && <div className="text-xs text-red-400 truncate">{t.last_error}</div>}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <div className="text-xs text-white/40 truncate hidden sm:block">{new Date(t.created_at).toLocaleString()}</div>
                              {t.status.toLowerCase() !== 'scheduled' && (
                                <Badge 
                                  variant={badgeVariant(t.status) as any} 
                                  className={`text-xs capitalize rounded-full ${t.status.toLowerCase()==='running' ? 'bg-white/10 text-white border border-white/30 shadow-[0_0_12px_rgba(255,255,255,0.35)] ring-1 ring-white/10' : 'bg-white/5 text-white border border-white/20'}`}
                                >
                                  {t.status}
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => openEdit(t)}
                              className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30"
                            >
                              <PencilEdit02Icon size={14} />
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => deleteTask(t.id)}
                              className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30"
                            >
                              <Delete02Icon size={14} />
                            </Button>
                            {t.status.toLowerCase() === 'scheduled' && (
                              <Button 
                                variant="outline" 
                                size="sm" 
                                onClick={() => cancelTask(t.id)}
                                className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30"
                              >
                                Cancel
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card id="task-history" className="bg-black/40 border border-white/20 ">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 font-normal text-white">History</CardTitle>
                  <CardDescription>Completed, failed, or cancelled tasks with quick repeat</CardDescription>
                </CardHeader>
                <CardContent>
                  {tasks.filter(t => ["completed","failed","cancelled"].includes((t.status||"").toLowerCase())).length === 0 ? (
                    <div className="text-sm text-white/70">No history yet.</div>
                  ) : (
                    <div className="space-y-2">
                      {tasks.filter(t => ["completed","failed","cancelled"].includes((t.status||"").toLowerCase())).map((t) => (
                        <div key={t.id} className="flex items-center gap-2">
                          <div className="flex items-center justify-between bg-black/20 border border-white/10 rounded-full px-5 py-4 w-full overflow-hidden min-h-[64px]">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="flex flex-col min-w-0 flex-1 justify-center">
                                <div className="text-sm text-white truncate">{(t as any).query || t.name}</div>
                                <div className="text-xs text-white/60 truncate">{t.run_at ? `At ${t.run_at}` : (t.delay_seconds != null ? `In ${t.delay_seconds}s` : "")}</div>
                                {t.last_error && <div className="text-xs text-red-400 truncate">{t.last_error}</div>}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <div className="text-xs text-white/40 truncate hidden sm:block">{new Date(t.created_at).toLocaleString()}</div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            {(() => {
                              const s = (t.status || '').toLowerCase()
                              if (s === 'completed') {
                                return (
                                  <div className="h-9 w-9 flex items-center justify-center rounded-full bg-white border border-zinc-950/40">
                                    <Tick02Icon size={16} className="text-green-700" />
                                  </div>
                                )
                              }
                              if (s === 'failed') {
                                return (
                                  <span className="inline-flex items-center justify-center h-8 w-8 rounded-full border border-white/30 bg-white/5 ring-1 ring-white/10">
                                    <CancelCircleIcon size={16} className="text-red-400" />
                                  </span>
                                )
                              }
                              if (s === 'cancelled') {
                                return (
                                  <span className="inline-flex items-center justify-center h-8 w-8 rounded-full border border-white/30 bg-white/5 ring-1 ring-white/10">
                                    <Cancel01Icon size={16} className="text-white/70" />
                                  </span>
                                )
                              }
                              return null
                            })()}
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => repeatTask(t.id)}
                              className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30"
                            >
                              Repeat
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => deleteTask(t.id)}
                              className="text-xs rounded-full border-white/30 bg-white/5 hover:bg-white/10 shadow-[0_0_12px_rgba(255,255,255,0.35)] hover:shadow-[0_0_22px_rgba(255,255,255,0.55)] ring-1 ring-white/10 hover:ring-white/30"
                            >
                              <Delete02Icon size={14} />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingTask ? "Edit Scheduled Task" : "New Scheduled Task"}</DialogTitle>
              <DialogDescription>Provide an app name, then either a delay in seconds or a time like 10:00.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <Input placeholder="Application name (e.g., calculator, chrome)" value={name} onChange={(e) => setName(e.target.value)} />
              <Input placeholder="Delay seconds (e.g., 10)" value={delaySeconds} onChange={(e) => setDelaySeconds(e.target.value)} />
              <Input placeholder="Run at (HH:MM or ISO 2025-11-03T10:00:00)" value={runAt} onChange={(e) => setRunAt(e.target.value)} />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button onClick={saveTask} disabled={loading || !name.trim()}>Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}


