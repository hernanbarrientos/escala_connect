import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Para não piscar a tela de login ao dar F5
  const navigate = useNavigate();

  useEffect(() => {
    // Ao abrir o site, verifica se tem dados salvos
    const token = localStorage.getItem('accessToken');
    const savedUser = localStorage.getItem('userData');

    if (token && savedUser) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    // URLSearchParams é necessário para o OAuth2PasswordRequestForm do FastAPI
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/token', formData);
    
    // Captura os dados que o novo Backend manda
    const { access_token, user_name, igreja_nome, role } = response.data;

    // Salva no navegador
    localStorage.setItem('accessToken', access_token);
    const userData = { name: user_name, church: igreja_nome, role };
    localStorage.setItem('userData', JSON.stringify(userData));

    // Configura a API e o Estado
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setUser(userData);
    
    navigate('/dashboard'); 
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userData');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    navigate('/login');
  };

  const value = { 
    isLoggedIn: !!user, 
    user, // Agora os componentes podem acessar user.church, user.name
    login, 
    logout 
  };

  if (loading) {
    return <div>Carregando...</div>; // Ou seu componente Spinner
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};