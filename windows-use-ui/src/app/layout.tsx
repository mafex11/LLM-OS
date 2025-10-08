import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Windows-Use Agent",
  description: "AI-powered Windows automation agent with modern web interface",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
