import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import InboxPage from './pages/inbox/InboxPage';
import ContactsPage from './pages/contacts/ContactsPage';
import WhatsAppAccountsPage from './pages/settings/WhatsAppAccountsPage';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/inbox" replace />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="contacts" element={<ContactsPage />} />
          <Route path="settings" element={<WhatsAppAccountsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
