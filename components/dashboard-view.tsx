'use client'

import useSWR from 'swr'
import { useState } from 'react'
import { AlertTriangle, ArrowRight, Brain, Check, Clock3, Inbox, Mail, MoreHorizontal, Paperclip, Search, Sparkles, Star, Tag, Users } from 'lucide-react'
import { getEmailIntelligence, syncGmail } from '@/lib/api'

const emails = [
  { id: 1, sender: 'Sarah Chen', email: 'sarah.chen@acme.io', subject: 'Q4 Strategy Proposal', preview: "Hi team, I've attached the Q4 strategy proposal for your review. The key focus areas are...", time: '10:42 AM', label: 'Work', color: '#fbbc04', unread: true, attachment: true },
  { id: 2, sender: 'Mike Rodriguez', email: 'mike@startuphub.com', subject: 'Re: Partnership Opportunity', preview: "Thanks for reaching out! I'd love to explore how we can work together on this. Are you free...", time: '9:15 AM', label: 'Clients', color: '#0f9d58', unread: true, attachment: false },
  { id: 3, sender: 'Emma Wilson', email: 'emma@designco.com', subject: 'Design Feedback — Homepage', preview: 'Here are my thoughts on the latest homepage designs. Overall, I think version B is the strongest...', time: 'Yesterday', label: 'Projects', color: '#8ab4f8', unread: true, attachment: true },
  { id: 4, sender: 'David Kim', email: 'david@acme.io', subject: 'Quick question about timeline', preview: 'Hey! Just wanted to check in on the timeline for the launch. Do you think we are still on track...', time: 'Yesterday', label: 'Work', color: '#fbbc04', unread: false, attachment: false },
  { id: 5, sender: 'Alex Morgan', email: 'alex@freelance.dev', subject: 'Invoice #1042', preview: 'Please find attached the invoice for the work completed in November. Let me know if you have any questions.', time: 'Dec 12', label: 'Finance', color: '#ea4335', unread: false, attachment: true },
]

export function DashboardView({ onSync }: { onSync: () => void }) {
  const [selected, setSelected] = useState<number[]>([])
  const [query, setQuery] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [synced, setSynced] = useState(false)
  const [status, setStatus] = useState('Last synced: 5 minutes ago')
  const { data: intelligence } = useSWR('email-intelligence', getEmailIntelligence, { revalidateOnFocus: false })
  const intelligenceCount = intelligence?.length ?? 36
  const intelligenceOverview = intelligence ? 'Processed from your synced inbox' : 'Ready for your next inbox sync'
  const filteredEmails = emails.filter((email) => `${email.sender} ${email.subject} ${email.preview}`.toLowerCase().includes(query.toLowerCase()))
  const toggleSelected = (id: number) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])
  const toggleAll = () => setSelected(selected.length === filteredEmails.length ? [] : filteredEmails.map((email) => email.id))
  const handleSync = async () => {
    setSyncing(true)
    try {
      const result = await syncGmail(7)
      setStatus(`Last synced: just now · ${result.emails_synced} emails`)
      setSynced(true)
      onSync()
      window.setTimeout(() => setSynced(false), 2400)
    } catch {
      setStatus('Sync unavailable — check your Gmail connection')
    } finally {
      setSyncing(false)
    }
  }

  return <main className="min-w-0 flex-1 px-4 py-5 sm:px-7 lg:px-10 lg:py-8"><div className="mx-auto flex max-w-[1180px] flex-col gap-5">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="mb-1 text-sm text-[var(--muted)]">Tuesday, December 17, 2024</p><h1 className="text-3xl font-semibold tracking-tight">Good morning, Alex</h1></div><div className="flex items-center gap-2 text-sm text-[var(--muted)]"><span className="size-2 rounded-full bg-[#0f9d58]" />{status}</div></div>
    <div className="grid gap-3 sm:grid-cols-3">{[['Unread','42','-8%',Mail,'orange'],['Need reply','18','+5%',Clock3,'red'],['Intelligence emails',String(intelligenceCount),'AI processed',Brain,'blue']].map(([label,value,trend,Icon,tone]) => <Stat key={String(label)} label={String(label)} value={String(value)} trend={String(trend)} Icon={Icon as typeof Inbox} tone={String(tone)} />)}</div>
    <p className="-mt-2 text-xs text-[var(--muted)]">Intelligence emails: {intelligenceOverview}</p>
    <section className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface)] shadow-sm"><div className="flex flex-col gap-4 border-b border-[var(--line)] px-4 py-4 sm:px-6 sm:py-5 lg:flex-row lg:items-center lg:justify-between"><div><h2 className="text-lg font-semibold">Inbox intelligence</h2><p className="mt-1 text-sm text-[var(--muted)]">AI-powered insights from your recent emails</p></div><button type="button" onClick={handleSync} disabled={syncing} className="inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--blue)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-60">{syncing ? 'Syncing...' : synced ? <><Check className="size-4" /> Synced</> : <><Sparkles className="size-4" /> Sync Gmail</>}</button></div>
      <div className="grid divide-y border-b border-[var(--line)] sm:grid-cols-3 sm:divide-x sm:divide-y-0"><Insight icon={AlertTriangle} title="3 high-priority emails" copy="Need your attention today" tone="red" /><Insight icon={Clock3} title="7 emails waiting" copy="For more than 3 days" tone="orange" /><Insight icon={Users} title="12 follow-ups due" copy="Based on your conversations" tone="blue" /></div>
      <div className="flex flex-col gap-3 border-b border-[var(--line)] px-4 py-4 sm:flex-row sm:items-center sm:px-6"><button type="button" onClick={toggleAll} aria-label="Select all emails" className={`flex size-8 items-center justify-center rounded-md border ${selected.length === filteredEmails.length ? 'border-[var(--blue)] bg-[var(--blue)] text-white' : 'border-[var(--line)] text-[var(--muted)]'}`}>{selected.length === filteredEmails.length ? <Check className="size-4" /> : <span className="size-3" />}</button><div className="relative flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your inbox" className="h-10 w-full rounded-lg border border-[var(--line)] bg-[var(--surface-2)] pl-9 pr-3 text-sm outline-none transition focus:border-[var(--blue)]" /></div><div className="flex items-center gap-2"><button type="button" aria-label="Label selected emails" className="rounded-lg border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[var(--surface-2)]"><Tag className="size-4" /></button><button type="button" aria-label="More inbox actions" className="rounded-lg border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[var(--surface-2)]"><MoreHorizontal className="size-4" /></button></div></div>
      <div className="divide-y divide-[var(--line)]">{filteredEmails.map((email) => <article key={email.id} className={`group grid gap-3 px-4 py-4 transition hover:bg-[var(--surface-2)] sm:grid-cols-[auto_1fr_auto] sm:items-start sm:px-6 ${email.unread ? 'bg-[#fafbfe]' : ''}`}><div className="flex items-center gap-3"><button type="button" onClick={() => toggleSelected(email.id)} aria-label={`Select ${email.subject}`} className={`flex size-5 items-center justify-center rounded border ${selected.includes(email.id) ? 'border-[var(--blue)] bg-[var(--blue)] text-white' : 'border-[var(--line)]'}`}>{selected.includes(email.id) && <Check className="size-3" />}</button><Star className="size-4 text-[var(--muted)] transition hover:fill-[#fbbc04] hover:text-[#fbbc04]" /></div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><strong className={`text-sm ${email.unread ? 'font-semibold' : 'font-medium'}`}>{email.sender}</strong><span className="text-xs text-[var(--muted)]">&lt;{email.email}&gt;</span><span className="rounded px-2 py-0.5 text-[11px] font-semibold" style={{ backgroundColor: `${email.color}22`, color: email.color }}>{email.label}</span></div><h3 className={`mt-1 truncate text-sm ${email.unread ? 'font-semibold' : 'font-medium'}`}>{email.subject}</h3><p className="mt-1 line-clamp-1 text-sm text-[var(--muted)]">{email.preview}</p>{email.attachment && <span className="mt-2 inline-flex items-center gap-1 text-xs text-[var(--muted)]"><Paperclip className="size-3" /> Attachment</span>}</div><time className="text-xs text-[var(--muted)] sm:pt-1">{email.time}</time></article>)}{filteredEmails.length === 0 && <div className="px-6 py-12 text-center text-sm text-[var(--muted)]">No emails match your search.</div>}</div>
      <div className="flex items-center justify-between px-4 py-4 text-sm text-[var(--muted)] sm:px-6"><span>Showing {filteredEmails.length} of 1,284 emails</span><button type="button" className="inline-flex items-center gap-1 font-semibold text-[var(--blue)] hover:underline">View all emails <ArrowRight className="size-4" /></button></div>
    </section></div></main>
}
function Stat({ label, value, trend, Icon, tone }: { label: string; value: string; trend: string; Icon: typeof Inbox; tone: string }) { const colors: Record<string, string> = { blue: '#4285f4', orange: '#fbbc04', red: '#ea4335', green: '#0f9d58' }; return <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm text-[var(--muted)]">{label}</span><Icon className="size-4" style={{ color: colors[tone] }} /></div><div className="mt-3 flex items-end justify-between"><strong className="text-2xl font-semibold">{value}</strong><span className="text-xs font-semibold" style={{ color: colors[tone] }}>{trend}</span></div></div> }
function Insight({ icon: Icon, title, copy, tone }: { icon: typeof AlertTriangle; title: string; copy: string; tone: 'red' | 'orange' | 'blue' }) { const colors = { red: '#ea4335', orange: '#fbbc04', blue: '#4285f4' }; return <div className="flex items-center gap-3 px-4 py-4 sm:px-6"><div className="flex size-9 items-center justify-center rounded-lg" style={{ color: colors[tone], backgroundColor: `${colors[tone]}18` }}><Icon className="size-4" /></div><div><p className="text-sm font-semibold">{title}</p><p className="mt-0.5 text-xs text-[var(--muted)]">{copy}</p></div></div> }
