'use client'
import { useState } from 'react'
import { AppShell, type View } from '@/components/app-shell'
import { ChatView } from '@/components/chat-view'
import { DashboardView } from '@/components/dashboard-view'
import { SettingsView } from '@/components/settings-view'
import { syncGmail } from '@/lib/api'
export default function Home(){const [view,setView]=useState<View>('dashboard'); const [syncing,setSyncing]=useState(false); const onSync=async()=>{setSyncing(true);try{await syncGmail()}catch{}finally{setTimeout(()=>setSyncing(false),700)}}; return <AppShell view={view} onViewChange={setView}>{syncing&&<div className="fixed right-5 top-5 z-30 rounded-lg border border-[var(--line)] bg-[var(--surface-2)] px-4 py-3 text-sm text-[var(--mint)]">Syncing inbox…</div>}{view==='dashboard'?<DashboardView onSync={onSync}/>:view==='chat'?<ChatView/>:<SettingsView onSync={onSync}/>}</AppShell>}
