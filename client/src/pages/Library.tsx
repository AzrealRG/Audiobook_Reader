import { useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../auth/AuthContext'
import { stageInfo } from '../types'

export default function Library() {
    const { token, user, logout } = useAuth()
    const qc = useQueryClient()
    const fileRef = useRef<HTMLInputElement>(null)
    const refresh = () => qc.invalidateQueries({ queryKey: ['books'] })

    const books = useQuery({
        queryKey: ['books'],
        queryFn: () => api.listBooks(token!),
        refetchInterval: (q) => (q.state.data?.some((b) => stageInfo(b.stage).working) ? 3000 : false),
    })
    const upload = useMutation({ mutationFn: (f: File) => api.uploadBook(token!, f), onSuccess: refresh })
    const remove = useMutation({ mutationFn: (id: string) => api.deleteBook(token!, id), onSuccess: refresh })
    
    return (
        <main className="mx-auto max-w-3xl px-6 py-10">
          <header className="flex items-center justify-between">
            <h1 className="font-serif text-4xl text-stone-50">Your library</h1>
            <div className="text-sm text-stone-400">
              {user?.email} <button onClick={logout} className="ml-3 text-amber-400 underline">Log out</button>
            </div>
          </header>
    
          <input ref={fileRef} type="file" accept="application/pdf" hidden
            onChange={(e) => { const f = e.target.files?.[0]; if (f) upload.mutate(f); e.target.value = '' }} />
          <button onClick={() => fileRef.current?.click()} disabled={upload.isPending}
            className="mt-6 rounded-md bg-amber-400 px-4 py-2 font-medium text-stone-900 hover:bg-amber-300 disabled:opacity-60">
            {upload.isPending ? 'Uploading…' : 'Upload a PDF'}
          </button>
          {upload.isError && <p role="alert" className="mt-2 text-sm text-red-400">{upload.error.message}</p>}
    
          {books.isLoading && <p className="mt-8 text-stone-400">Loading your books…</p>}
          {books.data?.length === 0 && <p className="mt-8 text-stone-400">No books yet. Upload a PDF and it will appear here while it processes.</p>}
    
          <ul className="mt-8 divide-y divide-stone-800">
            {books.data?.map((b) => {
              const s = stageInfo(b.stage)
              const pct = b.total_chapters ? Math.round(((b.completed_chapters ?? 0) / b.total_chapters) * 100) : 0
              return (
                <li key={b.id} className="flex items-center justify-between gap-4 py-4">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-stone-100">{b.title ?? b.original_filename}</p>
                    <p className={`text-sm ${s.failed ? 'text-red-400' : s.ready ? 'text-emerald-400' : 'text-stone-400'}`}>
                      {s.label}{b.total_chapters ? ` · ${b.completed_chapters ?? 0}/${b.total_chapters} chapters` : ''}
                    </p>
                    {s.working && b.total_chapters ? (
                      <div className="mt-2 h-1 rounded bg-stone-800"><div className="h-1 rounded bg-amber-400" style={{ width: `${pct}%` }} /></div>
                    ) : null}
                    {s.failed && b.error && <p className="text-sm text-red-400">{b.error}</p>}
                  </div>
                  <button onClick={() => remove.mutate(b.id)} className="text-sm text-stone-500 hover:text-red-400">Delete</button>
                </li>
              )
            })}
          </ul>
        </main>
      )
    }
    