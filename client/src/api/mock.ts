import type { Book, Token, User } from '../types'

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
            return { ...b, completed_chapters: done, stage: done === b.total_chapters ? 'Ready': b.stage }
        }
        if (b.stage === 'Queued') return { ...b, stage: 'Extracting text' }
        if (b.stage === 'Extracting text') return { ...b, stage: 'Generating audio', total_chapters: 10, completed_chapters: 0 }
        return b
    })
}

export const mock = {
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