import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = { title: 'Inquirea · AI Email Copilot', description: 'A focused command center for your inbox.' }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en" className="bg-[#101112]"><body>{children}</body></html> }
