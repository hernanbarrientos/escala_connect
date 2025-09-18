import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext'; // Importa nosso hook
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import FuncoesPage from './pages/FuncoesPage';
import ServicosPage from './pages/ServicosPage';
import VoluntariosPage from './pages/VoluntariosPage';
import VinculosPage from './pages/VinculosPage'; 
import GerarEscalaPage from './pages/GerarEscalaPage';
import DashboardPage from './pages/DashboardPage';
import './App.css';

// --- MUDANÇA CRÍTICA AQUI ---
function PrivateRoute({ children }) {
  // Agora ele usa o estado do AuthContext, que é reativo
  const { isLoggedIn } = useAuth(); 
  return isLoggedIn ? children : <Navigate to="/login" />;
}

function App() {
  const { isLoggedIn } = useAuth(); // Pega o estado de login do contexto

  return (
    <>
      {isLoggedIn && <Navbar />}
      <main className="container">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route path="/" element={<Navigate to="/dashboard" />} />
          
          {/* Todas estas rotas agora usam a verificação correta */}
          <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          <Route path="/escala" element={<PrivateRoute><GerarEscalaPage /></PrivateRoute>} />
          <Route path="/funcoes" element={<PrivateRoute><FuncoesPage /></PrivateRoute>} />
          <Route path="/servicos" element={<PrivateRoute><ServicosPage /></PrivateRoute>} />
          <Route path="/voluntarios" element={<PrivateRoute><VoluntariosPage /></PrivateRoute>} />
          <Route path="/grupos" element={<PrivateRoute><VinculosPage /></PrivateRoute>} />
        </Routes>
      </main>
    </>
  );
}

export default App;