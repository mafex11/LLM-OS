"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { 
  Home01Icon, 
  Settings01Icon, 
  SidebarLeft01Icon, 
  SidebarRight01Icon,
  MessageMultiple02Icon,
  TimeScheduleIcon,
  ComputerIcon,
  Loading01Icon,
  BulbIcon
} from "hugeicons-react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { AppSidebar } from "@/components/layout/Sidebar"
import { useToast } from "@/hooks/use-toast"

interface Activity {
  id: string
  app_name: string
  window_title?: string
  start_time: string
  end_time?: string
  duration_seconds?: number
  category?: string
}

interface TabActivity extends Activity {
  tab_url?: string
  tab_title?: string
  is_research?: boolean
  is_entertainment?: boolean
}

interface DailySummary {
  date: string
  total_focus_time: number
  work_time: number
  research_time: number
  entertainment_time: number
  distraction_time: number
  focus_score: number
  app_usage_stats: Record<string, any>
  top_apps: Array<{ app: string; time: number }>
  insights: string
  screenshot_count: number
}

export default function ActivityPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [showSidebar, setShowSidebar] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("sidebarOpen")
      return saved === "true"
    }
    return false
  })
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])
  
  // Save sidebar state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sidebarOpen", String(showSidebar))
    }
  }, [showSidebar])
  const [activities, setActivities] = useState<{ app_activities: Activity[]; tab_activities: TabActivity[] }>({
    app_activities: [],
    tab_activities: []
  })
  const [summary, setSummary] = useState<DailySummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentActivity, setCurrentActivity] = useState<any>(null)

  const fetchActivityData = useCallback(async (date: string) => {
    setLoading(true)
    try {
      // Fetch activities
      const activitiesResponse = await fetch(`http://localhost:8000/api/tracking/activity?date=${date}`)
      if (activitiesResponse.ok) {
        const activitiesData = await activitiesResponse.json()
        setActivities({
          app_activities: activitiesData.app_activities || [],
          tab_activities: activitiesData.tab_activities || []
        })
      }

      // Fetch summary
      const summaryResponse = await fetch(`http://localhost:8000/api/tracking/summary?date=${date}`)
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json()
        setSummary(summaryData)
      } else if (summaryResponse.status === 404) {
        // Summary doesn't exist yet, that's okay
        setSummary(null)
      }

      // Fetch current activity
      const currentResponse = await fetch(`http://localhost:8000/api/tracking/current`)
      if (currentResponse.ok) {
        const currentData = await currentResponse.json()
        setCurrentActivity(currentData)
      }
    } catch (error) {
      console.error("Error fetching activity data:", error)
      toast({
        title: "Error",
        description: "Failed to fetch activity data. Make sure Yuki is running.",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  const showBrowserNotification = useCallback((title: string, message: string) => {
    if ("Notification" in window && Notification.permission === "granted") {
      try {
        const notification = new Notification(title, {
          body: message,
          icon: "/logo.svg",
          tag: "yuki-activity-notification"
        })
        
        // Auto-close after 5 seconds
        setTimeout(() => {
          notification.close()
        }, 5000)
      } catch (error) {
        console.error("Error showing browser notification:", error)
        // Fallback to toast
        toast({
          title: title,
          description: message,
          variant: "default"
        })
      }
    } else if (Notification.permission !== "denied") {
      // Request permission and show toast as fallback
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          showBrowserNotification(title, message)
        } else {
          toast({
            title: title,
            description: message,
            variant: "default"
          })
        }
      })
    } else {
      // Permission denied, use toast
      toast({
        title: title,
        description: message,
        variant: "default"
      })
    }
  }, [toast])

  const showNotification = useCallback((title: string, message: string) => {
    // Check if we're in Electron (Windows notifications)
    const isElectron = typeof window !== "undefined" && (window as any).electron
    
    if (isElectron && (window as any).electron?.showNotification) {
      // Use Electron's notification API for Windows OS notifications
      try {
        ;(window as any).electron.showNotification(title, message)
      } catch (error) {
        console.error("Error showing Electron notification:", error)
        // Fallback to browser notification
        showBrowserNotification(title, message)
      }
    } else {
      // Use browser notifications for local development
      showBrowserNotification(title, message)
    }
  }, [showBrowserNotification])

  useEffect(() => {
    fetchActivityData(selectedDate)
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchActivityData(selectedDate)
    }, 30000)
    return () => clearInterval(interval)
  }, [selectedDate, fetchActivityData])

  // Notification handling
  useEffect(() => {
    // Request notification permission on mount
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission()
    }

    // Poll for notifications every 5 seconds
    const checkNotifications = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/notifications?clear=true")
        if (response.ok) {
          const data = await response.json()
          if (data.notifications && data.notifications.length > 0) {
            // Show notifications
            data.notifications.forEach((notif: { title: string; message: string; timestamp: string }) => {
              showNotification(notif.title, notif.message)
            })
          }
        }
      } catch (error) {
        console.error("Error checking notifications:", error)
      }
    }

    // Check immediately, then every 5 seconds
    checkNotifications()
    const notificationInterval = setInterval(checkNotifications, 5000)

    return () => clearInterval(notificationInterval)
  }, [showNotification])

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }


  // Only use app activities (tabs disabled)
  const allActivities = [
    ...activities.app_activities.map(a => ({ ...a, type: 'app' as const }))
    // Tab activities are disabled
    // ...activities.tab_activities.map(a => ({ ...a, type: 'tab' as const }))
  ].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())

  // Calculate total active time from all activities
  const totalActiveTime = allActivities.reduce((total, activity) => {
    return total + (activity.duration_seconds || 0)
  }, 0)

  return (
    <div className="flex min-h-screen w-full relative">
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
              <Button variant="ghost" size="icon" className="h-10 w-10 hover:bg-white/5 bg-white/10" onClick={() => router.push("/activity")}>
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
        <div className="p-4 border-b border-white/10 mx-2 space-y-4">
          <div className="flex items-center gap-3 px-2 cursor-pointer rounded-lg transition-colors" onClick={() => router.push('/chat')}>
            <img src="/logo.svg" alt="Logo" width={44} height={44} className="flex-shrink-0 rounded-full" />
            <span className="text-lg font-semibold">Yuki AI</span>
          </div>
        </div>
        <div className="flex-1 px-2 py-2 overflow-auto">
        </div>
        <div className="border-t border-white/10 mx-2 p-2 space-y-1">
          <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/")}>
            <Home01Icon size={16} />
            Home
          </Button>
          <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/chat")}>
            <MessageMultiple02Icon size={16} />
            Chat
          </Button>
          <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5 bg-white/10" onClick={() => router.push("/activity")}>
            <ComputerIcon size={16} />
            Activity
          </Button>
          <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/scheduled")}>
            <TimeScheduleIcon size={16} />
            Schedule Task
          </Button>
          <Button variant="ghost" className="group w-full justify-start gap-2 hover:bg-white/5" onClick={() => router.push("/settings")}>
            <Settings01Icon size={16} />
            Settings
          </Button>
        </div>
      </AppSidebar>

      <motion.div 
        className="flex-1 flex flex-col h-screen overflow-hidden"
        animate={{ paddingLeft: showSidebar ? '16rem' : '4rem' }}
        transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
      >
        <div 
          className="border-b border-white/10 px-4 py-3 flex items-center justify-between bg-black/20 backdrop-blur-sm flex-shrink-0"
        >
          <div className="flex items-center gap-3">
            <div className="cursor-pointer p-2 hover:bg-black/20 rounded-lg transition-colors" onClick={() => setShowSidebar(!showSidebar)}>
              {showSidebar ? <SidebarLeft01Icon size={24} /> : <SidebarRight01Icon size={24} />}
            </div>
            <div className="flex items-center gap-2">
              <ComputerIcon size={24} />
              <h1 className="text-lg font-normal hidden sm:block">Activity Tracker</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-white/20"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fetchActivityData(selectedDate)}
              disabled={loading}
            >
              <Loading01Icon size={16} className={loading ? "animate-spin" : ""} />
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1 px-2 sm:px-4">
          <div className="max-w-4xl mx-auto py-4 sm:py-8">
            <div className="space-y-6">
            {/* Current Activity */}
            {currentActivity && currentActivity.app && (
              <Card className="bg-black/20 border-white/10 rounded-3xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TimeScheduleIcon size={18} />
                    Current Activity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{currentActivity.app.name}</p>
                      {currentActivity.app.title && (
                        <p className="text-sm text-white/60">{currentActivity.app.title}</p>
                      )}
                    </div>
                    <span className="text-sm text-white/60">
                      {formatDuration(currentActivity.duration || 0)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-black/20 border-white/10 rounded-3xl">
                <CardHeader className="pb-2">
                  <CardDescription>Total Active Time</CardDescription>
                  <CardTitle className="text-3xl">
                    {formatDuration(totalActiveTime)}
                  </CardTitle>
                </CardHeader>
              </Card>

              {(() => {
                // Calculate most used app from app activities only (no tabs)
                const appUsage: Record<string, number> = {}
                allActivities
                  .filter(activity => activity.type === 'app')  // Only app activities, no tabs
                  .forEach(activity => {
                    const appName = activity.app_name
                    appUsage[appName] = (appUsage[appName] || 0) + (activity.duration_seconds || 0)
                  })
                
                const sortedApps = Object.entries(appUsage)
                  .map(([app, time]) => ({ app, time }))
                  .sort((a, b) => b.time - a.time)
                
                const mostUsedApp = sortedApps[0]
                const focusTime = mostUsedApp?.time || 0
                
                return mostUsedApp ? (
                  <Card className="bg-black/20 border-white/10 rounded-3xl">
                    <CardHeader className="pb-2">
                      <CardDescription>Focus Time</CardDescription>
                      <CardTitle className="text-2xl">{mostUsedApp.app}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg text-white/60">{formatDuration(focusTime)}</p>
                    </CardContent>
                  </Card>
                ) : null
              })()}
            </div>

            {/* Insights */}
            {/* {summary && summary.insights && (
              <Card className="bg-black/20 border-white/10 rounded-3xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BulbIcon size={18} />
                    Daily Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-white/80">{summary.insights}</p>
                </CardContent>
              </Card>
            )} */}

            {/* Activity Timeline */}
            <Card className="bg-black/20 border-white/10 rounded-3xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TimeScheduleIcon size={18} />
                  Activity Timeline
                </CardTitle>
                <CardDescription>
                  {allActivities.filter(a => a.type === 'app').length} activities tracked
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-4">
                    {allActivities.filter(a => a.type === 'app').length === 0 ? (
                      <div className="text-center py-12 text-white/40">
                        <p>No activities tracked for this date.</p>
                        <p className="text-sm mt-2">Activities will appear here as you use your computer.</p>
                      </div>
                    ) : (
                      allActivities
                        .filter(activity => activity.type === 'app')  // Only show app activities, no tabs
                        .map((activity, index) => (
                        <motion.div
                          key={activity.id || index}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.05 }}
                          className="flex items-start gap-4 p-4 rounded-lg bg-black/20 border border-white/10 hover:bg-black/30 transition-colors"
                        >
                          <div className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-500 mt-2" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium truncate">
                                    {activity.app_name}
                                  </span>
                                </div>
                                {activity.window_title && activity.window_title !== activity.app_name && (
                                  <p className="text-sm text-white/60 truncate">{activity.window_title}</p>
                                )}
                                {activity.duration_seconds && (
                                  <div className="mt-2 text-xs text-white/50">
                                    <span>{formatDuration(activity.duration_seconds)}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
            </div>
          </div>
        </ScrollArea>
      </motion.div>
    </div>
  )
}

