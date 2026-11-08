import type { Book, Manifest, Token, User } from '../types'

const wait = (ms = 400) => new Promise((r) => setTimeout(r, ms))
const now = () => new Date().toISOString()

// mock book input to test code
let books: Book[] = [
  { id: 'a1', title: 'Moby-Dick.pdf', original_filename: 'Moby-Dick.pdf', stage: 'Ready', total_chapters: 135, completed_chapters: 135, error: null, created_at: now(), updated_at: now() },
  { id: 'b2', title: 'Walden.pdf', original_filename: 'Walden.pdf', stage: 'Generating audio', total_chapters: 18, completed_chapters: 3, error: null, created_at: now(), updated_at: now() },
]

function tick() {
  books = books.map((b) => {
    if (b.stage === 'Generating audio' && b.total_chapters) {
      const done = Math.min((b.completed_chapters ?? 0) + 1, b.total_chapters)
      return { ...b, completed_chapters: done, stage: done === b.total_chapters ? 'Ready' : b.stage }
    }
    if (b.stage === 'Queued') return { ...b, stage: 'Extracting text' }
    if (b.stage === 'Extracting text') return { ...b, stage: 'Generating audio', total_chapters: 10, completed_chapters: 0 }
    return b
  })
}

const toneCache = new Map<string, string>()
function toneUrl(key: string, seconds = 20) {
  const cached = toneCache.get(key)
  if (cached) return cached
  const rate = 8000, n = rate * seconds
  const buf = new ArrayBuffer(44 + n * 2)
  const v = new DataView(buf)
  const w = (o: number, s: string) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)))
  w(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); w(8, 'WAVEfmt ')
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true)
  v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true)
  w(36, 'data'); v.setUint32(40, n * 2, true)
  const freq = 220 + toneCache.size * 60
  for (let i = 0; i < n; i++) v.setInt16(44 + i * 2, Math.sin((2 * Math.PI * freq * i) / rate) * 3000, true)
  const url = URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }))
  toneCache.set(key, url)
  return url
}

export const mock = {
  async getBook(id: string): Promise<Book> {
    await wait(150)
    const b = books.find((x) => x.id === id)
    if (!b) throw new Error('Book not found')
    return b
  },
  async getManifest(): Promise<Manifest> {
    await wait(200)
    return {
      chapters: [
        { index: 1, title: 'Chapter 1', audio_file: '01_chapter_1.mp3', char_count: 1193 },
        { index: 2, title: 'Chapter 2', audio_file: '02_chapter_2.mp3', char_count: 2094 },
        { index: 3, title: 'Chapter 3', audio_file: '03_chapter_3.mp3', char_count: 1388 },
        { index: 4, title: 'Chapter 4', audio_file: '04_chapter_4.mp3', char_count: 195 },
      ],
    }
  },
  audioUrl(file: string) { return toneUrl(file) },
  async signup(email: string, password: string): Promise<User> {
    await wait()
    if (password.length < 8) throw new Error('Password must be at least 8 characters')
    return { id: 1, email, created_at: now() }
  },
  async login(email: string, password: string): Promise<Token> {
    await wait()
    if (password.length < 8) throw new Error('Incorrect email or password')
    return { access_token: 'mock-' + email, token_type: 'bearer' }
  },
  async me(token: string): Promise<User> {
    await wait(150)
    return { id: 1, email: token.replace('mock-', ''), created_at: now() }
  },
  async listBooks(): Promise<Book[]> { await wait(200); tick(); return [...books] },
  async uploadBook(file: File) {
    await wait(600)
    const id = crypto.randomUUID()
    books = [{ id, title: file.name, original_filename: file.name, stage: 'queued', total_chapters: null, completed_chapters: null, error: null, created_at: now(), updated_at: now() }, ...books]
    return { book_id: id, status: 'queued' }
  },
  async deleteBook(id: string) { await wait(200); books = books.filter((b) => b.id !== id) },
}