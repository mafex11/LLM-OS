"use client"

import { useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"

// Redirect to new chat with unique session ID
function ChatRedirectContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Generate unique session ID
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${performance.now()}`
    
    // Get task parameter if present
    const task = searchParams.get('task')
    
    // Redirect to new chat with unique session ID
    if (task) {
      router.push(`/chat/${sessionId}?task=${encodeURIComponent(task)}`)
      } else {
      router.push(`/chat/${sessionId}`)
    }
  }, [router, searchParams])

  return (
    <div className="flex h-screen items-center justify-center bg-black">
      <div className="text-white">Redirecting to new chat...</div>
    </div>
  )
}

export default function ChatRedirect() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-black">
        <div className="text-white">Loading...</div>
      </div>
    }>
      <ChatRedirectContent />
    </Suspense>
  )
}

