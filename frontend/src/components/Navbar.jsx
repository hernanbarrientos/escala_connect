import { NavLink } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <span className="nav-logo">Escala Connect</span>
        <div className="nav-links">
          <NavLink to="/escala">Gerar Escala</NavLink>
          <NavLink to="/funcoes">Gerenciar Funções</NavLink>
          <NavLink to="/servicos">Gerenciar Serviços</NavLink>
          <NavLink to="/voluntarios">Gerenciar Voluntários</NavLink>
          <NavLink to="/vinculos">Gerenciar Vínculos</NavLink>
          {/* Adicione outros links aqui */}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;