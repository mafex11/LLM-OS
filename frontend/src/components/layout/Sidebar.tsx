"use client"

import { ReactNode } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface AppSidebarProps {
  isOpen: boolean
  width?: number
  children: ReactNode
}

export function AppSidebar({ isOpen, width = 256, children }: AppSidebarProps) {
  return (
    <AnimatePresence initial={false}>
      <motion.aside
        key="app-sidebar"
        className="fixed left-0 top-0 h-screen z-40 border-r border-white/10 bg-black/20 backdrop-blur-sm overflow-hidden"
        initial={false}
        animate={{ width: isOpen ? width : 0 }}
        exit={{ width: 0 }}
        transition={{ duration: 0.3 }}
        style={{ width: isOpen ? width : 0 }}
      >
        {isOpen && (
          <div className="flex h-full w-64 flex-col">
            {children}
          </div>
        )}
      </motion.aside>
    </AnimatePresence>
  )
}


