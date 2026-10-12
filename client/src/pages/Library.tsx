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
}