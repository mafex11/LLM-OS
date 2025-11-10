import type { Metadata } from "next"
import { Montserrat } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { ApiKeyProvider } from "@/contexts/ApiKeyContext"
import { StaticGridBackground } from "@/components/ui/static-grid-background"
import DarkVeilBackground from "@/components/DarkVeilBackground"

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
          <DarkVeilBackground />
          <StaticGridBackground />
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

