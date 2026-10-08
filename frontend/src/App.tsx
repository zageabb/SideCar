import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'

type Identity = 'Gez' | 'Tanya'
type Message = {
  id: string
  sender: Identity
  body: string
  created_at: string
  client_message_id: string
}

function newClientId() {
  return crypto.randomUUID()
}

export default function App() {
  const [identity, setIdentity] = useState<Identity | null>(null)
  const [selectedIdentity, setSelectedIdentity] = useState<Identity>('Gez')
  const [pin, setPin] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  const peer = useMemo(() => identity === 'Gez' ? 'Tanya' : 'Gez', [identity])

  async function loadMe() {
    const response = await fetch('/api/me')
    if (!response.ok) return
    const data = await response.json()
    setIdentity(data.identity)
  }

  async function loadMessages() {
    const response = await fetch('/api/messages')
    if (response.ok) setMessages(await response.json())
  }

  useEffect(() => { void loadMe() }, [])

  useEffect(() => {
    if (!identity) return
    void loadMessages()

    let socket: WebSocket | null = null
    let retry: number | undefined

    const connect = () => {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      socket = new WebSocket(`${protocol}//${location.host}/ws`)
      socket.onopen = () => setConnected(true)
      socket.onclose = () => {
        setConnected(false)
        retry = window.setTimeout(connect, 1500)
      }
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data)
        if (payload.type === 'message.created') {
          setMessages(current => current.some(m => m.id === payload.message.id)
            ? current
            : [...current, payload.message])
        }
      }
    }

    connect()
    return () => {
      if (retry) window.clearTimeout(retry)
      socket?.close()
    }
  }, [identity])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function login(event: FormEvent) {
    event.preventDefault()
    setError('')
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ identity: selectedIdentity, pin }),
    })
    if (!response.ok) {
      setError('That PIN did not work.')
      return
    }
    setIdentity(selectedIdentity)
    setPin('')
  }

  async function send(event: FormEvent) {
    event.preventDefault()
    const text = body.trim()
    if (!text) return
    setBody('')
    setError('')
    const response = await fetch('/api/messages', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ body: text, client_message_id: newClientId() }),
    })
    if (!response.ok) {
      setBody(text)
      setError('Message could not be sent.')
      return
    }
    const message = await response.json()
    setMessages(current => current.some(m => m.id === message.id) ? current : [...current, message])
  }

  async function logout() {
    await fetch('/api/logout', {method: 'POST'})
    setIdentity(null)
    setMessages([])
  }

  if (!identity) {
    return <main className="login-shell">
      <section className="login-card">
        <div className="brand-mark">S</div>
        <h1>Sidecar</h1>
        <p>Private chat and quick handoff between Gez and Tanya.</p>
        <form onSubmit={login}>
          <label>Who are you?</label>
          <div className="identity-picker">
            {(['Gez', 'Tanya'] as Identity[]).map(name =>
              <button type="button" key={name}
                className={selectedIdentity === name ? 'selected' : ''}
                onClick={() => setSelectedIdentity(name)}>{name}</button>
            )}
          </div>
          <label htmlFor="pin">PIN</label>
          <input id="pin" type="password" value={pin}
            onChange={e => setPin(e.target.value)} autoFocus />
          {error && <div className="error">{error}</div>}
          <button className="primary" type="submit">Open Sidecar</button>
        </form>
      </section>
    </main>
  }

  return <main className="app-shell">
    <header>
      <div>
        <h1>Sidecar</h1>
        <span className="subtle">{identity} ↔ {peer}</span>
      </div>
      <div className="header-actions">
        <span className={connected ? 'status online' : 'status'}>
          {connected ? 'Connected' : 'Reconnecting'}
        </span>
        <button className="ghost" onClick={logout}>Switch user</button>
      </div>
    </header>

    <section className="conversation">
      {messages.length === 0 && <div className="empty">
        <strong>Sidecar is ready.</strong>
        <span>Send the first message to {peer}.</span>
      </div>}
      {messages.map(message =>
        <article key={message.id}
          className={message.sender === identity ? 'message mine' : 'message theirs'}>
          <div className="meta">{message.sender}</div>
          <div className="bubble">
            <span>{message.body}</span>
            <button className="copy" onClick={() => navigator.clipboard.writeText(message.body)}>Copy</button>
          </div>
          <time>{new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</time>
        </article>
      )}
      <div ref={endRef} />
    </section>

    <form className="composer" onSubmit={send}>
      <textarea value={body} onChange={e => setBody(e.target.value)}
        placeholder={`Message ${peer}…`}
        onKeyDown={e => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            e.currentTarget.form?.requestSubmit()
          }
        }} />
      <button className="send" type="submit" disabled={!body.trim()}>Send</button>
    </form>
    {error && <div className="toast">{error}</div>}
  </main>
}
