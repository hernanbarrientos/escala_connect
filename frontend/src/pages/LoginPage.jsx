// arquivo: frontend/src/pages/LoginPage.jsx (MODIFICADO)

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';
import logo from '../assets/HUB.png'; // 1. Importar a imagem do logo

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err) {
      setError('Usuário ou senha inválidos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        
        {/* 2. Adicionar o novo cabeçalho com o logo e os textos */}
        <div className="login-header">
          <img src={logo} alt="Logo Escala Connect" className="login-logo" />
          <h2>Renovo Hub</h2>
          <p>Sistema gerador de escala</p>
        </div>
        
        {error && <p className="error-message">{error}</p>}
        <div className="form-group">
          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Senha</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        <button type="submit" className="btn-save" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}

export default LoginPage;