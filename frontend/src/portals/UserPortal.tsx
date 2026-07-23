import { User } from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { MobileShell } from '@/components/layout/MobileShell'
import { PhoneFrame } from '@/components/layout/PhoneFrame'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { HomePage } from '@/pages/HomePage'
import { LeaderboardPage } from '@/pages/LeaderboardPage'
import { MePage } from '@/pages/MePage'
import { MorePage } from '@/pages/MorePage'
import { Placeholder } from '@/pages/Placeholder'
import { ReportPage } from '@/pages/ReportPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage'
import { VerifyPage } from '@/pages/auth/VerifyPage'

/** The mobile user portal, rendered inside the phone frame. */
export function UserPortal() {
  return (
    <PhoneFrame>
      <Routes>
        {/* full-screen auth stack */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/forgot" element={<ForgotPasswordPage />} />
        <Route path="/reset" element={<ResetPasswordPage />} />

        {/* bottom-tab shell */}
        <Route element={<MobileShell />}>
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
          <Route path="more" element={<MorePage />} />
          <Route path="contact" element={<Placeholder title="Contact us" icon={User} milestone="soon" />} />
          <Route path="feedback" element={<Placeholder title="Feedback" icon={User} milestone="soon" />} />
          <Route path="about" element={<Placeholder title="About" icon={User} milestone="soon" />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </PhoneFrame>
  )
}
