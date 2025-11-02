import type { Metadata } from "next"
import { Inter } from "next/font/google"

const inter = Inter({
  subsets: ['latin'],
  // weight: ['400', '500', '600', '700'], // Uncomment and adjust weights as needed
  // display: 'swap', // Uncomment if you want to enable font-display: swap
})
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { ApiKeyProvider } from "@/contexts/ApiKeyContext"

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
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange={false}
        >
          <ApiKeyProvider>
            {children}
          </ApiKeyProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
