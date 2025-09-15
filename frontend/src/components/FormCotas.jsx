// arquivo: frontend/src/components/FormCotas.jsx

import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './FormCotas.css';

function FormCotas({ servico, allFuncoes, onSave, onCancel }) {
  const [cotas, setCotas] = useState({});
  const [loading, setLoading] = useState(true);

  // Busca as cotas atuais quando o componente é aberto
  useEffect(() => {
    const fetchCotas = async () => {
      if (servico) {
        setLoading(true);
        const response = await api.get(`/servicos/${servico.id_servico}/cotas`);
        setCotas(response.data);
        setLoading(false);
      }
    };
    fetchCotas();
  }, [servico]);

  // Atualiza o valor de uma cota específica
  const handleCotaChange = (id_funcao, valor) => {
    const novoValor = parseInt(valor, 10);
    setCotas(prevCotas => ({
      ...prevCotas,
      [id_funcao]: isNaN(novoValor) ? 0 : novoValor
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave(servico.id_servico, cotas);
  };

  if (loading) return <p>Carregando cotas atuais...</p>;

  return (
    <form onSubmit={handleSubmit} className="cotas-form">
      <div className="form-group-grid">
        {allFuncoes.map(funcao => (
          <div key={funcao.id_funcao} className="form-group">
            <label htmlFor={`cota_${funcao.id_funcao}`}>{funcao.nome_funcao}</label>
            <input
              id={`cota_${funcao.id_funcao}`}
              type="number"
              min="0"
              max="20"
              value={cotas[funcao.id_funcao] || 0}
              onChange={(e) => handleCotaChange(funcao.id_funcao, e.target.value)}
            />
          </div>
        ))}
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-cancel">Cancelar</button>
        <button type="submit" className="btn-save">Salvar Cotas</button>
      </div>
    </form>
  );
}

export default FormCotas;