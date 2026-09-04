import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './stores/authStore'

// User Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import GuestPredict from './pages/GuestPredict'
import UserDashboard from './pages/user/Dashboard'
import UploadPredict from './pages/user/UploadPredict'
import PredictionHistory from './pages/user/PredictionHistory'
import Profile from './pages/user/Profile'
import DLIAnalysis from './pages/user/DLIAnalysis'
import DLIDetail from './pages/user/DLIDetail'
import DLITextAnalysis from './pages/user/DLITextAnalysis'
import VideoAnalysis3M from './pages/user/VideoAnalysis3M'
import VideoAnalysis3MResult from './pages/user/VideoAnalysis3MResult'
import VideoAnalysis3MHistory from './pages/user/VideoAnalysis3MHistory'

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard'
import DocumentDataset from './pages/admin/DocumentDataset'
import UserManagement from './pages/admin/UserManagement'
import ActivityLogs from './pages/admin/ActivityLogs'
import SystemConfig from './pages/admin/SystemConfig'
import DLIAnomalyReport from './pages/admin/DLIAnomalyReport'
import DLIKeywords from './pages/admin/DLIKeywords'
import DLIDashboard from './pages/admin/DLIDashboard'
import DLIHistory from './pages/admin/DLIHistory'
import DLIAnalytics from './pages/admin/DLIAnalytics'
import DLIBulkAnalysis from './pages/admin/DLIBulkAnalysis'
import VideoAnalysis3MDashboard from './pages/admin/VideoAnalysis3MDashboard'
import VideoAnalysis3MEvaluation from './pages/admin/VideoAnalysis3MEvaluation'

// Layout
import AppLayout from './components/layout/AppLayout'
import KeyboardShortcuts from './components/KeyboardShortcuts'
import { LanguageProvider } from './contexts/LanguageContext'

function RequireAuth({ children, adminOnly = false }) {
  const { token, user } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  if (adminOnly && user?.role !== 'admin') return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <LanguageProvider>
    <BrowserRouter>
      <KeyboardShortcuts />
      <Toaster
        position="top-center"
        containerStyle={{
          top: '50%',
          transform: 'translateY(-50%)',
        }}
        toastOptions={{
          duration: 4000,
          style: {
            background: '#0f172a',
            color: '#e2e8f0',
            border: '1px solid #1e293b',
            borderRadius: '12px',
            fontFamily: 'DM Sans, sans-serif',
            padding: '16px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
          },
          success: {
            duration: 3000,
            style: {
              background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)',
              color: '#ffffff',
              border: '1px solid #14b8a6',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#0d9488',
            },
          },
          error: {
            duration: 4000,
            style: {
              background: 'linear-gradient(135deg, #991b1b 0%, #dc2626 100%)',
              color: '#ffffff',
              border: '1px solid #ef4444',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#dc2626',
            },
          },
          loading: {
            style: {
              background: 'linear-gradient(135deg, #4338ca 0%, #6366f1 100%)',
              color: '#ffffff',
              border: '1px solid #818cf8',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#6366f1',
            },
          },
        }}
      />
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/guest" element={<GuestPredict />} />

        {/* User Routes */}
        <Route path="/" element={<RequireAuth><AppLayout /></RequireAuth>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<UserDashboard />} />
          <Route path="predict" element={<UploadPredict />} />
          <Route path="history" element={<PredictionHistory />} />
          <Route path="profile" element={<Profile />} />
          <Route path="dli-analysis" element={<DLIAnalysis />} />
          <Route path="dli-analysis/:id" element={<DLIDetail />} />
          <Route path="dli-analysis/:id/text" element={<DLITextAnalysis />} />
          <Route path="video-analysis-3m" element={<VideoAnalysis3M />} />
          <Route path="video-analysis-3m/result/:jobId" element={<VideoAnalysis3MResult />} />
          <Route path="video-analysis-3m/history" element={<VideoAnalysis3MHistory />} />
        </Route>

        {/* Admin Routes */}
        <Route path="/admin" element={<RequireAuth adminOnly><AppLayout /></RequireAuth>}>
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="dataset/document" element={<DocumentDataset />} />

          <Route path="users" element={<UserManagement />} />
          <Route path="logs" element={<ActivityLogs />} />
          <Route path="config" element={<SystemConfig />} />
          <Route path="dli/anomaly" element={<DLIAnomalyReport />} />
          <Route path="dli/keywords" element={<DLIKeywords />} />
          <Route path="dli/dashboard" element={<DLIDashboard />} />
          <Route path="dli/history" element={<DLIHistory />} />
          <Route path="dli/analytics" element={<DLIAnalytics />} />
          <Route path="dli/bulk" element={<DLIBulkAnalysis />} />
          <Route path="video-analysis-3m" element={<VideoAnalysis3MDashboard />} />
          <Route path="video-analysis-3m/evaluation" element={<VideoAnalysis3MEvaluation />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
    </LanguageProvider>
  )
}
