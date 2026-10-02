import type { Book, Token, User } from '../types'

const wait = (ms = 400) => new Promise((r) => setTimeout(r, ms))
const now = () => new Date().toISOString()

// mock book input to test code
let books: Book[] = [
    { id: 'a1', title: 'Moby-Dick.pdf', original_filename: 'Moby-Dick.pdf', stage: 'Ready', total_chapters: 135, completed_chapters: 135, error: null, created_at: now(), updated_at: now() },
    { id: 'b2', title: 'Walden.pdf', original_filename: 'Walden.pdf', stage: 'Generating audio', total_chapters: 18, completed_chapters: 3, error: null, created_at: now(), updated_at: now() },
  ]