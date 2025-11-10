"use client"

import { ReactNode } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface AppSidebarProps {
  isOpen: boolean
  width?: number
  collapsedWidth?: number
  children: ReactNode
  collapsedContent?: ReactNode
}

export function AppSidebar({ isOpen, width = 256, collapsedWidth = 64, children, collapsedContent }: AppSidebarProps) {
  return (
    <motion.aside
      className="fixed left-0 top-0 h-screen z-40 border-r border-white/10 bg-black/20 backdrop-blur-sm overflow-hidden"
      initial={false}
      animate={{ width: isOpen ? width : collapsedWidth }}
      transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
    >
      <AnimatePresence mode="wait">
        {isOpen ? (
          <motion.div
            key="expanded"
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.1, ease: "easeOut" }}
            className="flex h-full w-64 flex-col"
          >
            {children}
          </motion.div>
        ) : (
          <motion.div
            key="collapsed"
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.1, ease: "easeOut" }}
            className="flex h-full w-16 flex-col items-center py-4 gap-2"
          >
            {collapsedContent}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.aside>
  )
}


