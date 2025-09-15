// arquivo: frontend/src/components/FormVoluntario.jsx

import React, { useState, useEffect } from 'react';
import './FormVoluntario.css';

function FormVoluntario({ voluntario, allFuncoes, allServicos, onSave, onCancel }) {
  // Estados para cada campo do formulário
  const [nome, setNome] = useState('');
  const [limite, setLimite] = useState(2);
  const [nivel, setNivel] = useState('Iniciante');
  const [ativo, setAtivo] = useState(true);
  const [funcoesSelecionadas, setFuncoesSelecionadas] = useState(new Set());
  const [disponibilidadeSelecionada, setDisponibilidadeSelecionada] = useState(new Set());

  // useEffect para preencher o formulário quando estiver editando um voluntário
  useEffect(() => {
    if (voluntario) {
      setNome(voluntario.nome_voluntario || '');
      setLimite(voluntario.limite_escalas_mes || 2);
      setNivel(voluntario.nivel_experiencia || 'Iniciante');
      setAtivo(voluntario.ativo !== undefined ? voluntario.ativo : true);
      setFuncoesSelecionadas(new Set(voluntario.funcoes_ids || []));
      setDisponibilidadeSelecionada(new Set(voluntario.disponibilidade_ids || []));
    }
  }, [voluntario]);

  const handleFuncaoChange = (id_funcao) => {
    const newSelection = new Set(funcoesSelecionadas);
    if (newSelection.has(id_funcao)) {
      newSelection.delete(id_funcao);
    } else {
      newSelection.add(id_funcao);
    }
    setFuncoesSelecionadas(newSelection);
  };

  const handleDisponibilidadeChange = (id_servico) => {
    const newSelection = new Set(disponibilidadeSelecionada);
    if (newSelection.has(id_servico)) {
      newSelection.delete(id_servico);
    } else {
      newSelection.add(id_servico);
    }
    setDisponibilidadeSelecionada(newSelection);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave({
      id_voluntario: voluntario?.id_voluntario,
      nome_voluntario: nome,
      limite_escalas_mes: limite,
      nivel_experiencia: nivel,
      ativo: ativo,
      funcoes_ids: Array.from(funcoesSelecionadas),
      disponibilidade_ids: Array.from(disponibilidadeSelecionada),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="voluntario-form">
      {/* Dados Pessoais */}
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="nome_voluntario">Nome Completo</label>
          <input id="nome_voluntario" type="text" value={nome} onChange={(e) => setNome(e.target.value)} required />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="limite_escalas_mes">Limite de escalas/mês</label>
          <input id="limite_escalas_mes" type="number" min="1" max="10" value={limite} onChange={(e) => setLimite(parseInt(e.target.value))} required />
        </div>
        <div className="form-group">
          <label htmlFor="nivel_experiencia">Nível de Experiência</label>
          <select id="nivel_experiencia" value={nivel} onChange={(e) => setNivel(e.target.value)}>
            <option>Iniciante</option>
            <option>Intermediário</option>
            <option>Avançado</option>
          </select>
        </div>
      </div>
      
      {/* Funções e Disponibilidades */}
      <div className="form-row">
        <div className="form-group">
          <label>Funções que pode exercer</label>
          <div className="checkbox-group">
            {allFuncoes.map(funcao => (
              <div key={funcao.id_funcao} className="checkbox-item">
                <input type="checkbox" id={`funcao_${funcao.id_funcao}`} checked={funcoesSelecionadas.has(funcao.id_funcao)} onChange={() => handleFuncaoChange(funcao.id_funcao)} />
                <label htmlFor={`funcao_${funcao.id_funcao}`}>{funcao.nome_funcao}</label>
              </div>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label>Disponibilidade Padrão</label>
          <div className="checkbox-group">
            {allServicos.map(servico => (
              <div key={servico.id_servico} className="checkbox-item">
                <input type="checkbox" id={`servico_${servico.id_servico}`} checked={disponibilidadeSelecionada.has(servico.id_servico)} onChange={() => handleDisponibilidadeChange(servico.id_servico)} />
                <label htmlFor={`servico_${servico.id_servico}`}>{servico.nome_servico}</label>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="form-group-checkbox">
          <input id="ativo" type="checkbox" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} />
          <label htmlFor="ativo">Voluntário Ativo</label>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-cancel">Cancelar</button>
        <button type="submit" className="btn-save">Salvar</button>
      </div>
    </form>
  );
}

export default FormVoluntario;