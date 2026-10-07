import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function ProtectedRoute() {
    const { token, loading } = useAuth()
    if (loading) return <p className="p-8 text-stone-400">Loading...</p>
    return token ? <Outlet /> : <Navigate to="/login" replace />
}