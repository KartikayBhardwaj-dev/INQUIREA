'use client'

import { useState } from 'react'
import { Bot, Send, Sparkles, UserRound } from 'lucide-react'
import { sendChat } from '@/lib/api'

const starter = 'I found 3 conversations related to the launch timeline. Alex is waiting on final review, while Jon asked whether the integrations milestone can move forward.'

export function ChatView() {
  const [message, setMessage] = useState('')
  const [answer, setAnswer] = useState(starter)
  const [sending, setSending] = useState(false)

  const submit = async () => {
    if (!message.trim()) return
    const current = message
    setMessage('')
    setSending(true)
    try {
      const result = await sendChat(current)
      setAnswer(result.answer)
    } catch {
      setAnswer('I searched your synced inbox and found a few related conversations. Connect the API in Settings to enable live answers.')
    } finally {
      setSending(false)
    }
  }

  return (
    <main className="min-w-0 flex-1 px-4 py-5 sm:px-7 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-5">
        <div>
          <p className="mb-1 text-sm text-[var(--muted)]">AI email assistant</p>
          <h1 className="text-3xl font-semibold tracking-tight">AI Assistant</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">Search context, understand threads, and move replies forward.</p>
        </div>
        <section className="flex min-h-[650px] w-full flex-col overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface)] shadow-sm">
          <div className="flex items-center gap-3 border-b border-[var(--line)] px-4 py-4 sm:px-6">
            <div className="flex size-9 items-center justify-center rounded-full bg-[var(--blue-soft)] text-[var(--blue)]"><Bot className="size-5" /></div>
            <div><p className="text-sm font-semibold">AI Assistant</p><p className="text-xs text-[var(--muted)]">Connected to your inbox</p></div>
            <span className="ml-auto size-2 rounded-full bg-[#0f9d58]" />
          </div>
          <div className="flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
            <div className="flex gap-3"><div className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--blue-soft)] text-[var(--blue)]"><Bot className="size-4" /></div><div className="max-w-[90%] rounded-2xl rounded-tl-sm bg-[var(--surface-2)] px-4 py-3 text-sm leading-6"><p>{answer}</p><div className="mt-3 flex flex-wrap gap-2 text-xs text-[var(--blue)]"><button type="button" onClick={() => setMessage('Show me emails from Sarah this week')} className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 hover:bg-[var(--blue-soft)]">Show related emails</button><button type="button" onClick={() => setMessage('Draft a reply to the latest launch email')} className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 hover:bg-[var(--blue-soft)]">Draft a reply</button></div></div></div>
            {message && <div className="flex justify-end gap-3"><div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-[var(--blue)] px-4 py-3 text-sm leading-6 text-white">{message}</div><div className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--surface-2)] text-[var(--muted)]"><UserRound className="size-4" /></div></div>}
            {sending && <div className="flex items-center gap-2 text-sm text-[var(--muted)]"><Sparkles className="size-4" /> Thinking through your inbox...</div>}
          </div>
          <div className="border-t border-[var(--line)] p-4 sm:p-5"><div className="flex items-end gap-2 rounded-xl border border-[var(--line)] bg-[var(--surface-2)] p-2 focus-within:border-[var(--blue)]"><textarea value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && event.keyCode !== 229) { event.preventDefault(); void submit() } }} placeholder="Ask about your emails..." rows={2} className="min-h-14 flex-1 resize-none bg-transparent px-2 py-1 text-sm leading-6 outline-none" /><button type="button" onClick={() => void submit()} disabled={!message.trim() || sending} className="grid size-9 shrink-0 place-items-center rounded-lg bg-[var(--blue)] text-white transition hover:opacity-90 disabled:opacity-40" aria-label="Send message"><Send className="size-4" /></button></div><p className="mt-2 text-center text-[11px] text-[var(--muted)]">AI can make mistakes. Check important information.</p></div>
        </section>
      </div>
    </main>
  )
}
