import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api'
import type { User } from '../types'

interface AuthState {
    token: string | null
    user: string | null
    loading: boolean
    login: (email: string, password: string) => Promise<void>
    signup: (email: string, password: string) => Promise<void>
    logout: () => void
}

const Ctx = createContext<AuthState | null>(null)
const KEY = 'audiobook_token'

export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setToken] = useState<string | null>(() => localStorage.getItem(KEY))
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(!!token)

    useEffect(() => {
        if (!token) { setUser(null); setLoading(false); return }
        api.me(token).then(setUser).catch(() => logout()).finally(() => setLoading(false))
    }, [token])

    async function login(email: string, password: string) {
        const t = await api.login(email, password)
        localStorage.setItem(KEY, t.access_token)
        setToken(t.access_token)
    }
    async function signup(email: string, password: string) {
        await api.signup(email, password)
        await login(email, password)
    }
    function logout() {
        localStorage.removeItem(KEY)
        setToken(null)
        setUser(null)
    }
    
    return <Ctx.Provider value={{ token, user, loading, login, signup, logout }}>{children}</Ctx.Provider>
}

export function useAuth() { 
    const ctx = useContext(Ctx) 
    if (!ctx) throw new Error('useAuth must be inside AuthProvider')
    return ctx
}