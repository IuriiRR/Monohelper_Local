import { useEffect } from 'react'
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Sync } from './pages/Sync'
import { Transactions } from './pages/Transactions'
import { Accounts } from './pages/Accounts'
import { Setup } from './pages/Setup'

export function UnauthorizedRedirect() {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    function handler() {
      if (location.pathname !== '/setup') {
        navigate('/setup', { state: { from: location.pathname } })
      }
    }
    window.addEventListener('api:unauthorized', handler)
    return () => window.removeEventListener('api:unauthorized', handler)
  }, [navigate, location])

  return null
}

export default function App() {
  return (
    <>
      <UnauthorizedRedirect />
      <Routes>
        <Route path="setup" element={<Setup />} />
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="sync" element={<Sync />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="accounts" element={<Accounts />} />
        </Route>
      </Routes>
    </>
  )
}
