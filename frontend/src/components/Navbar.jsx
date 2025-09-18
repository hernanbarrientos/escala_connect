import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext'; // 1. Importa o hook useAuth
import './Navbar.css';

function Navbar() {
  const { logout } = useAuth(); // 2. Pega a função de logout diretamente do contexto

  return (
    <nav className="navbar">
      <div className="nav-container">
        <span className="nav-logo">Escala Connect</span>
        <div className="nav-links">
          <NavLink to="/dashboard">Dashboard</NavLink> 
          <NavLink to="/escala">Gerar Escala</NavLink>
          <NavLink to="/funcoes">Funções</NavLink>
          <NavLink to="/servicos">Serviços</NavLink>
          <NavLink to="/voluntarios">Voluntários</NavLink>
          <NavLink to="/vinculos">Vínculos</NavLink>
        </div>
        
        <div className="nav-actions">
            {/* 3. O botão agora chama a função 'logout' do contexto */}
            <button onClick={logout} className="logout-btn">Sair</button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;