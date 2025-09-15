import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import FuncoesPage from './pages/FuncoesPage';
import ServicosPage from './pages/ServicosPage';
import VoluntariosPage from './pages/VoluntariosPage'
import VinculosPage from './pages/VinculosPage'; 
import GerarEscalaPage from './pages/GerarEscalaPage';
import './App.css';

function App() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<FuncoesPage />} /> {/* Rota inicial */}
          <Route path="/escala" element={<GerarEscalaPage />} />
          <Route path="/funcoes" element={<FuncoesPage />} />
          <Route path="/servicos" element={<ServicosPage />} />
          <Route path="/voluntarios" element={<VoluntariosPage />} />
          <Route path="/vinculos" element={<VinculosPage />} />
          {/* Adicione outras rotas aqui no futuro */}
        </Routes>
      </main>
    </>
  );
}

export default App;