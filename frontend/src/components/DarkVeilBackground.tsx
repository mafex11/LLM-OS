"use client"

import DarkVeil from "@/components/DarkVeil"

export default function DarkVeilBackground() {
  return (
    <div className="absolute inset-0 z-0">
      <DarkVeil 
        hueShift={245}
        noiseIntensity={0.02}
        scanlineIntensity={0.1}
        speed={0.3}
        scanlineFrequency={2.0}
        warpAmount={0.5}
        resolutionScale={1}
      />
    </div>
  )
}

