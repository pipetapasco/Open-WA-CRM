import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import InboxPage from './pages/inbox/InboxPage';
import ContactsPage from './pages/contacts/ContactsPage';
import WhatsAppAccountsPage from './pages/settings/WhatsAppAccountsPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import { UnreadProvider } from './contexts/UnreadContext';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <UnreadProvider>
          <Routes>
            {/* Rutas públicas */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Rutas protegidas */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/inbox" replace />} />
              <Route path="inbox" element={<InboxPage />} />
              <Route path="contacts" element={<ContactsPage />} />
              <Route path="settings" element={<WhatsAppAccountsPage />} />
            </Route>
          </Routes>
        </UnreadProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
