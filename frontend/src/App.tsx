import { Camera, MoreHorizontal, Trophy, User } from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { MobileShell } from '@/components/layout/MobileShell'
import { HomePage } from '@/pages/HomePage'
import { Placeholder } from '@/pages/Placeholder'

export default function App() {
  return (
    <Routes>
      <Route element={<MobileShell />}>
        <Route index element={<HomePage />} />
        <Route
          path="leaderboard"
          element={<Placeholder title="Leaderboard" icon={Trophy} milestone="F3" />}
        />
        <Route
          path="report"
          element={<Placeholder title="Report plastic" icon={Camera} milestone="F2" />}
        />
        <Route path="me" element={<Placeholder title="My impact" icon={User} milestone="F3" />} />
        <Route
          path="more"
          element={<Placeholder title="More" icon={MoreHorizontal} milestone="F1" />}
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
