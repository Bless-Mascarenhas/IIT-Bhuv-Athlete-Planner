import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Planner from './pages/Planner';
import Chat from './pages/Chat';
import Calendar from './pages/Calendar';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Onboarding from './pages/Onboarding';
import { AthleteProvider } from './context/AthleteContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Play } from 'lucide-react';

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, hasOnboarded, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: '#e0e5ec' }}>
        <Play size={40} color="#fc5200" fill="#fc5200" className="pulse-anim" />
      </div>
    );
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }
  if (!hasOnboarded) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <AthleteProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/" element={<AuthGuard><Layout /></AuthGuard>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="planner" element={<Planner />} />
              <Route path="chat" element={<Chat />} />
              <Route path="calendar" element={<Calendar />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </Router>
      </AthleteProvider>
    </AuthProvider>
  );
}

export default App;
