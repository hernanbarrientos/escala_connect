import React, { createContext, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    // Verifica se já existe um token no início
    const token = localStorage.getItem('accessToken');
    return token ? { loggedIn: true } : null;
  });
  const navigate = useNavigate();

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/token', formData);
    
    localStorage.setItem('accessToken', response.data.access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
    setUser({ loggedIn: true });
    navigate('/dashboard'); // Redireciona para o dashboard após o login
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    navigate('/login');
  };

  const value = { isLoggedIn: !!user, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook customizado para facilitar o uso do contexto
export const useAuth = () => {
  return useContext(AuthContext);
};