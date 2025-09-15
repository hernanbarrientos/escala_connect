// arquivo: frontend/src/components/FormServico.jsx

import React, { useState, useEffect } from 'react';
import './FormServico.css';

const diasSemana = { 0: "Domingo", 1: "Segunda-feira", 2: "Terça-feira", 3: "Quarta-feira", 4: "Quinta-feira", 5: "Sexta-feira", 6: "Sábado" };

function FormServico({ servico, onSave, onCancel }) {
  const [nome, setNome] = useState('');
  const [dia, setDia] = useState(0); // 0 para Domingo
  const [ativo, setAtivo] = useState(true);

  useEffect(() => {
    if (servico) {
      setNome(servico.nome_servico || '');
      setDia(servico.dia_da_semana || 0);
      setAtivo(servico.ativo !== undefined ? servico.ativo : true);
    }
  }, [servico]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave({
      id_servico: servico?.id_servico,
      nome_servico: nome,
      dia_da_semana: dia,
      ativo: ativo
    });
  };

  return (
    <form onSubmit={handleSubmit} className="servico-form">
      <div className="form-group">
        <label htmlFor="nome_servico">Nome do Serviço</label>
        <input
          id="nome_servico"
          type="text"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="dia_da_semana">Dia da Semana</label>
        <select
          id="dia_da_semana"
          value={dia}
          onChange={(e) => setDia(parseInt(e.target.value))}
        >
          {Object.entries(diasSemana).map(([value, name]) => (
            <option key={value} value={value}>{name}</option>
          ))}
        </select>
      </div>
      {servico && (
        <div className="form-group-checkbox">
          <input
            id="ativo"
            type="checkbox"
            checked={ativo}
            onChange={(e) => setAtivo(e.target.checked)}
          />
          <label htmlFor="ativo">Serviço Ativo</label>
        </div>
      )}
      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-cancel">Cancelar</button>
        <button type="submit" className="btn-save">Salvar</button>
      </div>
    </form>
  );
}

export default FormServico;