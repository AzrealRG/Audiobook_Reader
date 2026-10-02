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