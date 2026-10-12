import { useState, type SyntheticEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function AuthPage({ mode }: { mode: 'login' | 'signup' }) {
    const { token, login, signup } = useAuth()
    const navigate = useNavigate()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const isLogin = mode == 'login'

    if (token) return <Navigate to='/' replace />

    async function onSubmit(e: SyntheticEvent<HTMLFormElement>) {
        e.preventDefault()
        setError('')
        setBusy(true)
        try {
            await (isLogin ? login(email, password) : signup(email, password))
            navigate('/')
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong')
        } finally {
            setBusy(false)
        }
    }

    const input = 'mt-1 w-full rounded-md border border-stone-700 bg-stone-900 px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/40'

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-6">
      <h1 className="font-serif text-4xl text-stone-50">{isLogin ? 'Welcome back' : 'Start listening'}</h1>
      <p className="mt-2 text-stone-400">
        {isLogin ? 'Log in to pick up where you left off.' : 'Create an account to turn your PDFs into audiobooks.'}
      </p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block text-sm text-stone-300">
          Email
          <input className={input} type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="block text-sm text-stone-300">
          Password
          <input className={input} type="password" required minLength={8} autoComplete={isLogin ? 'current-password' : 'new-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
        <button disabled={busy} className="w-full rounded-md bg-amber-400 px-4 py-2 font-medium text-stone-900 hover:bg-amber-300 disabled:opacity-60">
          {busy ? 'Please wait…' : isLogin ? 'Log in' : 'Create account'}
        </button>
      </form>
      <p className="mt-6 text-sm text-stone-400">
        {isLogin ? 'New here? ' : 'Already have an account? '}
        <Link className="text-amber-400 underline" to={isLogin ? '/signup' : '/login'}>{isLogin ? 'Create an account' : 'Log in'}</Link>
      </p>
    </main>
  )
}
