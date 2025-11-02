"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight01Icon, Settings01Icon, VoiceIcon } from "hugeicons-react"
import { GridBackground } from "@/components/ui/grid-background"
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

  return (
<div className="min-h-screen w-full relative overflow-hidden">
  {/* Enhanced Background with Animated Elements */}
  <div
    className="absolute inset-0 z-0"
    style={{
      background: "radial-gradient(125% 125% at 50% 100%, #000000 30%, #1a0b0b 70%, #2b0707 100%)",
    }}
  />
  
  <GridBackground />

  {/* Content */}
  <section className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-20">
    {/* Enhanced Logo with subtle animation */}
    <div className="mb-8 flex justify-center transform hover:scale-105 transition-transform duration-300">
      <div className="flex items-center gap-3 group">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-red-700 rounded-full blur-md opacity-75 group-hover:opacity-100 transition-opacity duration-300"></div>
          <Image 
            src="/logo.svg" 
            alt="Yuki AI Logo" 
            width={60} 
            height={60} 
            className="relative flex-shrink-0 rounded-full border-2 border-white/10"
          />
        </div>
        <span className="text-6xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent relative">
          Yuki
          <span className="absolute -bottom-2 left-0 w-full h-0.5 bg-gradient-to-r from-red-500 to-transparent"></span>
        </span>
      </div>
    </div>

    {/* Enhanced Main Headline */}
    <h1 className="mb-6 text-balance text-center font-sans text-4xl font-medium leading-tight tracking-tight md:text-5xl lg:text-6xl">
      Your AI copilot for{' '}
      <span className="bg-gradient-to-r from-white to-red-200 bg-clip-text text-transparent">
        devices
      </span>
      .
    </h1>

    {/* Enhanced Supporting Text */}
    <p className="mx-auto mb-10 max-w-2xl text-center text-pretty text-lg leading-relaxed text-white/60 md:text-xl">
      Meet <span className="text-white font-semibold">Yuki</span>, your intelligent AI copilot. Have natural conversations, 
      automate tasks, and control your device effortlessly through voice commands and smart automation.
    </p>

    {/* Enhanced Input Section */}
    <div className="mb-8 w-full max-w-2xl">
      <div className="relative flex gap-3">
        {/* Voice Button */}
        <button className="relative inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-full transition-all duration-300 hover:scale-110 hover:shadow-lg hover:shadow-red-500/20">
          <span className="absolute inset-0 bg-gradient-to-br from-red-600 to-red-800 rounded-full" />
          <span className="absolute inset-0 bg-gradient-to-br from-red-500 to-red-700 rounded-full opacity-0 hover:opacity-100 transition-opacity duration-300" />
          <span className="relative text-white">
            <VoiceIcon size={22} />
          </span>
        </button>

        {/* Input Field */}
        <div className="relative flex-1">
          <div className="absolute inset-0 bg-gradient-to-r from-red-600 to-red-800 rounded-full blur-sm opacity-50 transition-opacity duration-300 hover:opacity-75" />
          <input
            type="text"
            placeholder="Enter what you want to do..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className="relative w-full px-6 py-4 bg-black/80 backdrop-blur-3xl rounded-full text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/50 text-base border border-white/10"
          />
        </div>

        {/* Start Now Button */}
        <button 
          onClick={handleStartNow}
          className="relative inline-flex h-12 items-center px-6 overflow-hidden rounded-full bg-white text-black transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-black/30"
        >
          <span className="absolute inset-0 bg-black/5 rounded-full" />
          <span className="absolute inset-0 bg-white/10 rounded-full opacity-0 hover:opacity-100 transition-opacity duration-300" />
          <span className="relative font-medium text-sm">
            Start Now
          </span>
        </button>
      </div>
    </div>

    {/* Enhanced CTA Buttons */}
    <div className="mb-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
      <Link href="/chat">
        <Button 
          size="lg" 
          variant="outline"
          className="gap-3 px-8 py-6 border-2 border-white/20 bg-white/50 backdrop-blur-sm hover:bg-white/70 hover:border-white/30 hover:text-black text-black font-semibold rounded-xl transition-all duration-300 hover:scale-105 cursor-pointer"
        >
          Get Started
          <ArrowRight01Icon size={18} className="transition-transform duration-300 group-hover:translate-x-1" />
        </Button>
      </Link>
      <Link href="/settings">
        <Button 
          size="lg" 
          variant="outline"
          className="gap-3 px-8 py-6 border-2 border-white/20 bg-white/5 backdrop-blur-sm hover:bg-white/10 hover:border-white/30 text-white font-semibold rounded-xl transition-all duration-300"
        >
          <Settings01Icon size={18} />
          Configure API Keys
        </Button>
      </Link>
    </div>

    {/* Enhanced Example Commands */}
    <div className="w-full max-w-3xl">
      <p className="mb-4 text-center text-lg font-medium text-white/80">Try these examples</p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {exampleCommands.map((command, index) => (
          <button
            key={index}
            className="px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 hover:border-red-500/50 hover:bg-red-500/10 rounded-xl text-sm text-white/80 hover:text-white transition-all duration-300 hover:scale-105 cursor-pointer min-w-[140px]"
            onClick={() => setInputValue(command)}
          >
            {command}
          </button>
        ))}
      </div>
    </div>

    {/* Additional Features Preview */}

  </section>
</div>
  )
}

