import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext'; // <-- 1. Importe o AuthProvider
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider> {/* <-- 2. Envolva o App com ele */}
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);