export type ApiUser = {
  id: number
  email: string
  full_name: string | null
  google_id: string | null
  profile_picture: string | null
  google_token_expiry: string | null
  last_login_at: string | null
  created_at: string
}

export type AuthResponse = {
  access_token: string
  user: Pick<ApiUser, 'id' | 'email'>
}

export type EmailIntelligence = {
  id: number
  email_id: number
  category: string | null
  priority: string | null
  summary: string | null
  extracted_data: Record<string, unknown> | null
  tags: unknown[] | null
  confidence: number | null
  processed_at: string | null
  created_at: string
}

export type RetrievedEmail = {
  email_id: number
  subject: string
  sender: string
  category: string | null
  priority: string | null
  received_at: string | null
}

export type ChatResponse = {
  conversation_id: string
  answer: string
  sources: number[]
  emails_found: number
  retrieved_emails: RetrievedEmail[]
  query_plan: Record<string, unknown>
}

export type SyncResponse = {
  success: true
  days: number
  emails_synced: number
}

export type Email = {
  id: number
  sender: string
  initials: string
  subject: string
  preview: string
  time: string
  priority: 'High' | 'Medium' | 'Low'
  label: string
  labelTone: 'mint' | 'amber' | 'blue'
}

export type Insight = { title: string; detail: string; tone: 'mint' | 'amber' | 'blue' }

export const emails: Email[] = [
  { id: 1, sender: 'Alex Morgan', initials: 'AM', subject: 'Q4 launch plan — final review', preview: 'The latest version is ready for your feedback before tomorrow morning.', time: '9:42 AM', priority: 'High', label: 'Needs reply', labelTone: 'mint' },
  { id: 2, sender: 'Maya Patel', initials: 'MP', subject: 'Re: Design system handoff', preview: 'I added the component notes and linked the updated Figma file.', time: '8:16 AM', priority: 'Medium', label: 'Design', labelTone: 'blue' },
  { id: 3, sender: 'Northstar Labs', initials: 'NL', subject: 'Your September invoice is ready', preview: 'Your monthly invoice and usage breakdown are now available.', time: 'Yesterday', priority: 'Low', label: 'Finance', labelTone: 'amber' },
  { id: 4, sender: 'Jon Bell', initials: 'JB', subject: 'Quick question about the roadmap', preview: 'Do we still have room to bring the integrations milestone forward?', time: 'Yesterday', priority: 'High', label: 'Needs reply', labelTone: 'mint' },
]

export const insights: Insight[] = [
  { title: 'You have 8 emails waiting for a reply', detail: 'Most are from this week and can be handled in under 20 minutes.', tone: 'mint' },
  { title: 'Three conversations mention launch timing', detail: 'Alex, Jon, and the Northstar team all reference the October milestone.', tone: 'amber' },
  { title: 'Your inbox is trending quieter', detail: 'You received 18% fewer emails than the previous seven-day period.', tone: 'blue' },
]

export const weeklyActivity = [42, 68, 54, 82, 61, 37, 24]

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, '')
const apiBaseUrl = configuredApiUrl ?? ''

function getToken() {
  return typeof window === 'undefined' ? '' : sessionStorage.getItem('inquirea_token') ?? ''
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const detail = await response.text().catch(() => '')
    throw new Error(detail || `API request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function getGoogleLoginUrl() {
  return `${apiBaseUrl}/auth/google/login`
}

export function getGoogleCallbackUrl() {
  return `${apiBaseUrl}/auth/google/callback`
}

export function setAuthToken(accessToken: string) {
  if (typeof window !== 'undefined') sessionStorage.setItem('inquirea_token', accessToken)
}

export function clearAuthToken() {
  if (typeof window !== 'undefined') sessionStorage.removeItem('inquirea_token')
}

export function getCurrentUser() {
  return apiFetch<ApiUser>('/auth/me')
}

export function sendChat(message: string, conversationId?: string) {
  const path = conversationId ? `/chat/${encodeURIComponent(conversationId)}` : '/chat'
  return apiFetch<ChatResponse>(path, {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
  })
}

export function getEmailIntelligence() {
  return apiFetch<EmailIntelligence[]>('/email-intelligence/')
}

export function syncGmail(days = 7) {
  return apiFetch<SyncResponse>(`/gmail/sync?days=${days}`, { method: 'POST' })
}
