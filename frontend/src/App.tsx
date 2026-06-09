import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Sync } from './pages/Sync'
import { Transactions } from './pages/Transactions'
import { Accounts } from './pages/Accounts'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sync" element={<Sync />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="accounts" element={<Accounts />} />
      </Route>
    </Routes>
  )
}
