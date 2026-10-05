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