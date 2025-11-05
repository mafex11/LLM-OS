import type { Metadata } from "next"
import { Montserrat } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { ApiKeyProvider } from "@/contexts/ApiKeyContext"
import { GridBackground } from "@/components/ui/grid-background"

const montserrat = Montserrat({ 
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-montserrat",
})

export const metadata: Metadata = {
  title: "Yuki AI",
  description: "AI-powered Windows automation assistant",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${montserrat.className} min-h-screen w-full relative overflow-hidden bg-black`}>
        <div className="fixed inset-0">
          <div 
            className="absolute inset-0 z-0"
            style={{
              background: "radial-gradient(125% 125% at 50% 100%, #000000 30%, #1a0b0b 70%, #2b0707 100%)",
            }}
          />
          {/* <GridBackground /> */}
        </div>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark" 
          enableSystem={false}  
          disableTransitionOnChange={false}
        >
          <ApiKeyProvider>
            <div className="relative z-10 min-h-screen">
              {children}
            </div>
          </ApiKeyProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

