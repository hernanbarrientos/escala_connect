// arquivo: frontend/src/components/FormFuncao.jsx

import React, { useState, useEffect } from 'react';
import '../styles/ManagementPage.css'; // Reutiliza o estilo que você já tem

function FormFuncao({ funcao, onSave, onCancel }) {
  // MUDANÇA: Usar um objeto para guardar todos os dados do formulário
  const [formData, setFormData] = useState({
    nome_funcao: '',
    tipo_funcao: 'PRINCIPAL', // Valor padrão para novas funções
    prioridade_alocacao: 10,  // Valor padrão para novas funções
  });

  // MUDANÇA: useEffect agora preenche o objeto formData
  useEffect(() => {
    if (funcao) {
      // Se está editando, carrega os dados da função existente
      setFormData({
        id_funcao: funcao.id_funcao,
        nome_funcao: funcao.nome_funcao || '',
        tipo_funcao: funcao.tipo_funcao || 'PRINCIPAL',
        prioridade_alocacao: funcao.prioridade_alocacao || 10,
      });
    } else {
      // Se está adicionando, reseta para os valores padrão
      setFormData({
        nome_funcao: '',
        tipo_funcao: 'PRINCIPAL',
        prioridade_alocacao: 10,
      });
    }
  }, [funcao]);

  // MUDANÇA: Função genérica para lidar com todas as mudanças nos inputs
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // MUDANÇA: Envia o objeto formData completo
    onSave(formData);
  };

  return (
    // O formulário agora tem 3 campos
    <form onSubmit={handleSubmit} className="servico-form">
      {/* Campo Nome da Função (continua igual) */}
      <div className="form-group">
        <label htmlFor="nome_funcao">Nome da Função</label>
        <input
          id="nome_funcao"
          name="nome_funcao" // 'name' é importante para o handleChange
          type="text"
          value={formData.nome_funcao}
          onChange={handleChange}
          required
          autoFocus
        />
      </div>

      {/* NOVO CAMPO: Tipo da Função */}
      <div className="form-group">
        <label htmlFor="tipo_funcao">Tipo da Função</label>
        <select
          id="tipo_funcao"
          name="tipo_funcao" // 'name' é importante para o handleChange
          value={formData.tipo_funcao}
          onChange={handleChange}
          required
        >
          <option value="PRINCIPAL">Principal</option>
          <option value="APOIO">Apoio</option>
          <option value="ESPECIALISTA">Especialista</option>
        </select>
        <small>Define a categoria da função na geração da escala.</small>
      </div>

      {/* NOVO CAMPO: Prioridade de Alocação */}
      <div className="form-group">
        <label htmlFor="prioridade_alocacao">Prioridade de Alocação</label>
        <input
          id="prioridade_alocacao"
          name="prioridade_alocacao" // 'name' é importante para o handleChange
          type="number"
          value={formData.prioridade_alocacao}
          onChange={handleChange}
          required
        />
        <small>Menor número = maior prioridade (ex: 1 é alocado antes de 10).</small>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-cancel">Cancelar</button>
        <button type="submit" className="btn-save">Salvar</button>
      </div>
    </form>
  );
}

export default FormFuncao;