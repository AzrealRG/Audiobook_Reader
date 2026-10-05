import type { Book, Token, User } from '../types'
import { mock } from './mock'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, token: string | null, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers)
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const res = await fetch(BASE + path, { ...init, headers })
    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(typeof body.detail === 'string' ? body.detail : 'Something went wrong')
    }
    return res.status === 204 ? (undefined as T) : res.json()
}

export const api = {
    signup: (email: string, password: string): Promise<User> =>
        USE_MOCK ? mock.signup(email, password) 
            : request('/auth/signup', null, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) }),
    
    login: (email: string, password: string): Promise<Token> => 
        USE_MOCK ? mock.login(email, password)
            : request('/auth/login', null, { method: 'POST', body: new URLSearchParams({ username: email, password}) }),
    me: (token: string): Promise<User> => (USE_MOCK ? mock.me(token) : request('/auth/me', token)),

    listBooks: (token: string): Promise<Book[]> => (USE_MOCK ? mock.listBooks() : request('/books', token)),

    uploadBook: (token: string, file: File): Promise<{ book_id: string, status: string }> => {
        if (USE_MOCK) return mock.uploadBook(file)
        const form = new FormData()
        form.append('file', file)
        return request('/books', token, { method: 'POST', body: form })
    },

    deleteBook: (token: string, id: string): Promise<unknown> =>
        USE_MOCK ? mock.deleteBook(id) : request(`/books/${id}`, token, { method: 'DELETE' }),
}