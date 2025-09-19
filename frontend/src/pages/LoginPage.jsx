import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false); // 1. Adicionar state de loading
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true); // 2. Ativar loading no início
    try {
      await login(username, password);
    } catch (err) {
      setError('Usuário ou senha inválidos.');
    } finally {
      setLoading(false); // 3. Desativar loading no final (sucesso ou erro)
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
            disabled={loading} // 4. Desativar input durante o loading
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
            disabled={loading} // 5. Desativar input durante o loading
          />
        </div>
        {/* 6. Alterar o botão para mostrar o estado de loading */}
        <button type="submit" className="btn-save" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}

export default LoginPage;