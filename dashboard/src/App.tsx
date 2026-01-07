import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Runs from './pages/Runs'
import RunDetail from './pages/RunDetail'
import Policies from './pages/Policies'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="runs" element={<Runs />} />
        <Route path="runs/:runId" element={<RunDetail />} />
        <Route path="policies" element={<Policies />} />
        <Route path="audit" element={<AuditLog />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
