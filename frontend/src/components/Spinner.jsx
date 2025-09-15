// arquivo: frontend/src/components/Spinner.jsx

import React from 'react';
import './Spinner.css';

function Spinner({ text = "Carregando..." }) {
  return (
    <div className="spinner-container">
      <div className="spinner"></div>
      <p>{text}</p>
    </div>
  );
}

export default Spinner;