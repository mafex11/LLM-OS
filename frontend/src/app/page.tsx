"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowRight01Icon, Settings01Icon, VoiceIcon } from "hugeicons-react"
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
    <div className="min-h-screen w-full relative">
      {/* Crimson Depth Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          background: "radial-gradient(125% 125% at 50% 100%, #000000 40%, #2b0707 100%)",
        }}
      />
      {/* Content */}
      <section className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-20">
        <motion.div className="mx-auto max-w-6xl text-center" variants={container} initial="hidden" animate="show">
          
          {/* Logo */}
          <motion.div variants={item} className="mb-8 flex justify-center">
            <div className="flex items-center gap-3">
              <Image src="/logo.svg" alt="Netra Logo" width={70} height={70} className="flex-shrink-0 rounded-full" />
               <span className="text-8xl font-semibold text-foreground relative">
                 {["N", "e", "t", "r", "a"].map((letter, index) => (
                   <motion.span
                     key={index}
                     className="inline-block"
                     animate={{
                       textShadow: [
                         "0 0 0px rgba(255, 255, 255, 0)",
                         "0 0 20px rgba(255, 255, 255, 0.8)",
                         "0 0 0px rgba(255, 255, 255, 0)"
                       ],
                       filter: [
                         "brightness(1)",
                         "brightness(1.5)",
                         "brightness(1)"
                       ]
                     }}
                     transition={{
                       duration: 0.8,
                       delay: index * 0.2,
                       repeat: Infinity,
                       repeatDelay: 2,
                       ease: "easeInOut"
                     }}
                   >
                     {letter}
                   </motion.span>
                 ))}
               </span>
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
            className="hidden sm:block mx-auto mb-12 max-w-4xl text-pretty text-md leading-relaxed text-white/40 md:text-md"
          >
            Meet your intelligent voice assistant. Have natural conversations, get factual answers, and control
            everything hands-free. No keyboard. No mouse. Just speak.
          </motion.p>

          {/* Input Box */}
          <motion.div variants={item} className="mb-8 flex justify-center">
            <div className="relative w-full max-w-3xl flex gap-2">
              <button className="relative inline-flex h-12 w-12 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50">
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#991B1B_0%,#450A0A_50%,#991B1B_100%)]" />
                <span className="inline-flex h-full w-full cursor-pointer items-center justify-center rounded-full bg-slate-950 text-white backdrop-blur-3xl">
                  <VoiceIcon size={24} />
                </span>
              </button>
              <div className="relative flex-1 inline-flex overflow-hidden rounded-full p-[1px]">
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#991B1B_0%,#450A0A_50%,#991B1B_100%)]" />
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
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#991B1B_0%,#450A0A_50%,#991B1B_100%)]" />
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
              <Button size="default" variant="destructive" className="gap-2">
                <Settings01Icon size={16} />
                Configure API Keys
                </Button>
            </Link>
          </motion.div>

          {/* Example Commands */}
          <motion.div variants={item} className="hidden sm:block">
            <p className="mb-4 text-xl font-normal text-white underline-offset-4 underline">Try these</p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              {exampleCommands.map((command, index) => (
                <motion.button
                  key={index}
                  variants={subtleItem}
                  initial="hidden"
                  animate="show"
                  transition={{ delay: 0.05 * index }}
                  className="flex-1 min-w-0 justify-center gap-2 hover:bg-black/20 backdrop-blur-sm border border-white/20 hover:border-white/30 rounded-lg px-4 py-3 text-sm text-center transition-colors"
                >
                  {command}
                </motion.button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </section>
    </div>
  )
}
