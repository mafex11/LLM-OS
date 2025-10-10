"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowRight01Icon, Settings01Icon, Mic01Icon } from "hugeicons-react"
import { DottedGlowBackground } from "@/components/ui/dotted-glow-background"
import Link from "next/link"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"

export default function LandingPage() {
  const [inputValue, setInputValue] = useState("")
  const router = useRouter()

  const handleStartNow = () => {
    if (inputValue.trim()) {
      router.push(`/chat?task=${encodeURIComponent(inputValue)}`)
    } else {
      router.push("/chat")
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleStartNow()
    }
  }

  const exampleCommands = [
    "Open Chrome and search for AI news",
    "Create a new folder on Desktop",
    "What's running on my system?",
  ]

  const container = {
    hidden: { opacity: 0, y: 12 },
    show: {
      opacity: 1,
      y: 0,
      transition: { type: "spring" as const, stiffness: 60, damping: 16, staggerChildren: 0.08 },
    },
  } as const
  const item = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
  } as const
  const subtleItem = {
    hidden: { opacity: 0, y: 6 },
    show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  } as const

  return (
    <div className="min-h-screen w-full bg-black relative">
      {/* Dotted Glow Background - Centered */}
      <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
        <div className="relative h-screen w-screen border border-white/10 rounded-lg">
          <DottedGlowBackground
            gap={20}
            radius={2}
            color="rgba(100, 100, 100, 0.5)"
            darkColor="rgba(200, 200, 200, 0.5)"
            glowColor="rgba(200, 120, 255, 1)"
            darkGlowColor="rgba(200, 120, 255, 1)"
            opacity={0.5}
            backgroundOpacity={0}
            speedMin={0.3}
            speedMax={0.8}
            speedScale={1}
          />
            </div>
      </div>
      {/* Content */}
      <section className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-20">
        <motion.div className="mx-auto max-w-6xl text-center" variants={container} initial="hidden" animate="show">
          
          {/* Logo */}
          <motion.div variants={item} className="mb-8 flex justify-center">
            <div className="flex items-center gap-3">
              <Image src="/logo.svg" alt="Windows-Use AI Logo" width={40} height={40} className="flex-shrink-0" />
              <span className="text-xl font-semibold text-foreground">Windows-Use AI</span>
                    </div>
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            variants={item}
            className="mb-6 text-balance font-sans text-4xl font-light leading-tight tracking-tight text-foreground md:text-5xl lg:text-6xl"
          >
            The easiest way to interact with your computer.

          </motion.h1>

          {/* Supporting Text */}
          <motion.p
            variants={item}
            className="mx-auto mb-12 max-w-4xl text-pretty text-md leading-relaxed text-muted-foreground md:text-md"
          >
            Meet your intelligent voice assistant. Have natural conversations, get factual answers, and control
            everything hands-free. No keyboard. No mouse. Just speak.
          </motion.p>

          {/* Input Box */}
          <motion.div variants={item} className="mb-8 flex justify-center">
            <div className="relative w-full max-w-3xl flex gap-2">
              <button className="relative inline-flex h-12 w-12 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50">
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)]" />
                <span className="inline-flex h-full w-full cursor-pointer items-center justify-center rounded-full bg-slate-950 text-white backdrop-blur-3xl">
                  <Mic01Icon size={18} />
                </span>
              </button>
              <div className="relative flex-1 inline-flex overflow-hidden rounded-full p-[1px]">
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)]" />
                <input
                  type="text"
                  placeholder="Enter what you want to do..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="relative w-full px-4 py-2.5 bg-slate-950 backdrop-blur-3xl rounded-full text-white placeholder:text-gray-500 focus:outline-none text-sm"
                />
              </div>
              <button 
                onClick={handleStartNow}
                className="relative inline-flex h-12 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50"
              >
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)]" />
                <span className="inline-flex h-full w-full cursor-pointer items-center justify-center rounded-full bg-slate-950 px-3 py-1 text-sm font-medium text-white backdrop-blur-3xl">
                  Start Now
                </span>
              </button>
            </div>
          </motion.div>

          {/* CTA Buttons */}
          <motion.div variants={item} className="mb-12 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/chat">
              <Button size="default" className="gap-2">
                Get Started
                <ArrowRight01Icon size={16} />
            </Button>
            </Link>
            <Link href="/settings">
              <Button size="default" variant="outline" className="gap-2">
                <Settings01Icon size={16} />
                Configure API Keys
                </Button>
            </Link>
          </motion.div>

          {/* Example Commands */}
          <motion.div variants={item}>
            <p className="mb-4 text-sm font-normal text-muted-foreground">Try:</p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              {exampleCommands.map((command, index) => (
                <motion.span
                  key={index}
                  variants={subtleItem}
                  initial="hidden"
                  animate="show"
                  transition={{ delay: 0.05 * index }}
                  className="rounded-full border border-border bg-secondary px-4 py-2 text-sm text-secondary-foreground transition-colors hover:bg-accent hover:text-accent-foreground cursor-pointer"
                >
                  {command}
                </motion.span>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </section>
    </div>
  )
}
