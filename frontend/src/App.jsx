import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import MinisterioPage from './pages/MinisterioPage';
import VoluntariosPage from './pages/VoluntariosPage';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';

// Componente para proteger rotas
function PrivateRoute({ children }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? children : <Navigate to="/login" />;
}

function App() {
  const { isLoggedIn } = useAuth();

  return (
    <> 
      {/* ATENÇÃO: NÃO coloque <Router> ou <BrowserRouter> aqui dentro! Já está no main.jsx */}
      
      {isLoggedIn && <Navbar />}
      
      <main className="container">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          {/* Rotas Protegidas */}
          <Route path="/dashboard" element={
            <PrivateRoute><DashboardPage /></PrivateRoute>
          } />

          <Route path="/ministerio/:id" element={
            <PrivateRoute><MinisterioPage /></PrivateRoute>
          } />

          <Route path="/ministerio/:id/voluntarios" element={
            <PrivateRoute><VoluntariosPage /></PrivateRoute>
          } />

          {/* Redirecionamentos e Erros */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </>
  );
}

export default App;