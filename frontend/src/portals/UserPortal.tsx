import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { AboutPage } from '@/pages/AboutPage'
import { ContactPage } from '@/pages/ContactPage'
import { EditProfilePage } from '@/pages/EditProfilePage'
import { FeedbackFormPage } from '@/pages/FeedbackFormPage'
import { HomePage } from '@/pages/HomePage'
import { LeaderboardPage } from '@/pages/LeaderboardPage'
import { MePage } from '@/pages/MePage'
import { MorePage } from '@/pages/MorePage'
import { ProfilePage } from '@/pages/ProfilePage'
import { ReportPage } from '@/pages/ReportPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage'
import { VerifyPage } from '@/pages/auth/VerifyPage'

/** The user portal — responsive: bottom-tab shell on mobile, sidebar on desktop. */
export function UserPortal() {
  return (
    <Routes>
      {/* full-screen auth stack (centred, no shell) */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify" element={<VerifyPage />} />
      <Route path="/forgot" element={<ForgotPasswordPage />} />
      <Route path="/reset" element={<ResetPasswordPage />} />

      {/* app shell */}
      <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="leaderboard" element={<LeaderboardPage />} />
          <Route path="report" element={<ReportPage />} />
          <Route
            path="me"
            element={
              <ProtectedRoute>
                <MePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="me/edit"
            element={
              <ProtectedRoute>
                <EditProfilePage />
              </ProtectedRoute>
            }
          />
          <Route path="more" element={<MorePage />} />
          <Route path="u/:id" element={<ProfilePage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="feedback" element={<FeedbackFormPage />} />
          <Route path="about" element={<AboutPage />} />
        </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
