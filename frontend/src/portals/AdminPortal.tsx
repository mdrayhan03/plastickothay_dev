import { Navigate, Route, Routes } from 'react-router-dom'
import { AdminShell } from '@/components/admin/AdminShell'
import { StaffRoute } from '@/components/layout/ProtectedRoute'
import { AdminDashboard } from '@/pages/admin/AdminDashboard'
import { AllReports } from '@/pages/admin/AllReports'
import { AuditLog } from '@/pages/admin/AuditLog'
import { FeedbackPage } from '@/pages/admin/FeedbackPage'
import { MessagesPage } from '@/pages/admin/MessagesPage'
import { ReviewQueue } from '@/pages/admin/ReviewQueue'
import { SettingsPage } from '@/pages/admin/SettingsPage'
import { UsersPage } from '@/pages/admin/UsersPage'

/** The desktop admin portal - full width, no phone frame. Staff/admin only. */
export function AdminPortal() {
  return (
    <StaffRoute>
      <Routes>
        <Route element={<AdminShell />}>
          <Route index element={<AdminDashboard />} />
          <Route path="review" element={<ReviewQueue />} />
          <Route path="reports" element={<AllReports />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="messages" element={<MessagesPage />} />
          <Route path="feedback" element={<FeedbackPage />} />
          <Route path="audit" element={<AuditLog />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      </Routes>
    </StaffRoute>
  )
}
