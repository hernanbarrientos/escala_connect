import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './LoginPage.css'; // Criaremos este CSS

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      // O FastAPI com OAuth2PasswordRequestForm espera os dados como FormData
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      // Salva o token no localStorage
      localStorage.setItem('accessToken', response.data.access_token);

      // Redireciona para a página principal
      navigate('/escala'); 
      window.location.reload(); // Força o reload para o App detectar a mudança

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