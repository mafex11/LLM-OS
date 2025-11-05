"use client"

import { ReactNode } from "react"

interface AppSidebarProps {
  isOpen: boolean
  width?: number
  collapsedWidth?: number
  children: ReactNode
  collapsedContent?: ReactNode
}

export function AppSidebar({ isOpen, width = 256, collapsedWidth = 64, children, collapsedContent }: AppSidebarProps) {
  return (
    <aside
      className="fixed left-0 top-0 h-screen z-40 border-r border-white/10 bg-black/20 backdrop-blur-sm overflow-hidden"
      style={{ width: isOpen ? width : collapsedWidth }}
    >
      {isOpen ? (
        <div className="flex h-full w-64 flex-col">
          {children}
        </div>
      ) : (
        <div className="flex h-full w-16 flex-col items-center py-4 gap-2">
          {collapsedContent}
        </div>
      )}
    </aside>
  )
}


