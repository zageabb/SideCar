import { ClipboardEvent, DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react'

type Identity = 'Gez' | 'Tanya'

type Attachment = {
  id: string
  original_filename: string
  mime_type: string
  size_bytes: number
  download_url: string
}

type Message = {
  id: string
  sender: Identity
  body: string
  created_at: string
  client_message_id: string
  attachments?: Attachment[]
}

function newClientId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16)
    crypto.getRandomValues(bytes)
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
  }
  return `sidecar-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function App() {
  const [identity, setIdentity] = useState<Identity | null>(null)
  const [selectedIdentity, setSelectedIdentity] = useState<Identity>('Gez')
  const [pin, setPin] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [body, setBody] = useState('')
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)
  const [sending, setSending] = useState(false)
  const [dragging, setDragging] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const peer = useMemo(() => identity === 'Gez' ? 'Tanya' : 'Gez', [identity])
  const canSend = Boolean(body.trim() || pendingFiles.length)

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

  function addFiles(files: File[]) {
    if (!files.length) return
    setPendingFiles(current => [...current, ...files])
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)
    addFiles(Array.from(event.dataTransfer.files))
  }

  function handlePaste(event: ClipboardEvent<HTMLTextAreaElement>) {
    const files = Array.from(event.clipboardData.items)
      .filter(item => item.kind === 'file')
      .map(item => item.getAsFile())
      .filter((file): file is File => Boolean(file))
    if (files.length) {
      event.preventDefault()
      addFiles(files)
    }
  }

  async function send(event: FormEvent) {
    event.preventDefault()
    const text = body.trim()
    if (!text && !pendingFiles.length) return

    const filesToSend = pendingFiles
    setSending(true)
    setError('')

    try {
      let response: Response
      if (filesToSend.length) {
        const form = new FormData()
        form.append('body', text)
        form.append('client_message_id', newClientId())
        filesToSend.forEach(file => form.append('files', file, file.name))
        response = await fetch('/api/messages/with-files', { method: 'POST', body: form })
      } else {
        response = await fetch('/api/messages', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ body: text, client_message_id: newClientId() }),
        })
      }

      if (!response.ok) {
        const detail = await response.json().catch(() => null)
        setError(detail?.detail ? `Could not send: ${detail.detail}` : 'Could not send the message.')
        return
      }

      const message = await response.json()
      setMessages(current => current.some(m => m.id === message.id) ? current : [...current, message])
      setBody('')
      setPendingFiles([])
    } catch {
      setError('Could not send. Check the Sidecar connection and try again.')
    } finally {
      setSending(false)
    }
  }

  async function logout() {
    await fetch('/api/logout', {method: 'POST'})
    setIdentity(null)
    setMessages([])
    setPendingFiles([])
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

  return <main
    className={dragging ? 'app-shell dragging' : 'app-shell'}
    onDragEnter={event => { event.preventDefault(); setDragging(true) }}
    onDragOver={event => event.preventDefault()}
    onDragLeave={event => {
      if (event.currentTarget === event.target) setDragging(false)
    }}
    onDrop={handleDrop}
  >
    {dragging && <div className="drop-overlay">Drop files to send</div>}

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
        <span>Send a message or drop a file for {peer}.</span>
      </div>}

      {messages.map(message =>
        <article key={message.id}
          className={message.sender === identity ? 'message mine' : 'message theirs'}>
          <div className="meta">{message.sender}</div>
          <div className="bubble">
            {message.body && <div className="message-text">{message.body}</div>}
            {message.attachments?.map(attachment => {
              const isImage = attachment.mime_type.startsWith('image/')
              return <a className="attachment-card" key={attachment.id}
                href={attachment.download_url} target="_blank" rel="noreferrer">
                {isImage && <img src={attachment.download_url} alt={attachment.original_filename} />}
                <div className="attachment-details">
                  <strong>{attachment.original_filename}</strong>
                  <span>{formatBytes(attachment.size_bytes)}</span>
                </div>
                <span className="download-mark">↓</span>
              </a>
            })}
            {message.body && <button className="copy"
              onClick={() => navigator.clipboard.writeText(message.body)}>Copy</button>}
          </div>
          <time>{new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</time>
        </article>
      )}
      <div ref={endRef} />
    </section>

    <form className="composer-wrap" onSubmit={send}>
      {pendingFiles.length > 0 && <div className="pending-files">
        {pendingFiles.map((file, index) =>
          <div className="pending-file" key={`${file.name}-${file.size}-${index}`}>
            <span>
              <strong>{file.name}</strong>
              <small>{formatBytes(file.size)}</small>
            </span>
            <button type="button" onClick={() =>
              setPendingFiles(current => current.filter((_, i) => i !== index))
            }>×</button>
          </div>
        )}
      </div>}

      <div className="composer">
        <input ref={fileInputRef} className="file-input" type="file" multiple
          onChange={event => {
            addFiles(Array.from(event.target.files || []))
            event.target.value = ''
          }} />
        <button className="attach" type="button" title="Attach files"
          onClick={() => fileInputRef.current?.click()}>＋</button>
        <textarea value={body} onChange={e => setBody(e.target.value)}
          onPaste={handlePaste}
          placeholder={`Message ${peer}… or paste/drop a file`}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              e.currentTarget.form?.requestSubmit()
            }
          }} />
        <button className="send" type="submit" disabled={!canSend || sending}>
          {sending ? 'Sending…' : 'Send'}
        </button>
      </div>
      <div className="transfer-hint">Drop files anywhere • Paste screenshots • Use + to browse</div>
    </form>
    {error && <div className="toast">{error}</div>}
  </main>
}
