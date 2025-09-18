import { useState } from 'react';
import { useAuth } from '../context/AuthContext'; // 1. Importa o hook useAuth
import api from '../services/api';
import './LoginPage.css';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth(); // 2. Pega a função de login do contexto

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      // 3. Usa a função de login do contexto
      // Ela já cuida de salvar o token, atualizar o estado e navegar
      await login(username, password);
    } catch (err) {
      setError('Usuário ou senha inválidos.');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>Login</h2>
        {error && <p className="error-message">{error}</p>}
        <div className="form-group">
          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
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
          />
        </div>
        <button type="submit" className="btn-save">Entrar</button>
      </form>
    </div>
  );
}

export default LoginPage;