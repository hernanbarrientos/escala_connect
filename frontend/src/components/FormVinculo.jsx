// arquivo: frontend/src/components/FormVinculo.jsx (Versão com Edição)

import React, { useState, useEffect, useMemo } from 'react';
import Select from 'react-select';
import './FormVinculo.css';

function FormVinculo({ vinculo, voluntariosDisponiveis, onSave, onCancel }) {
  const [nome, setNome] = useState('');
  const [limite, setLimite] = useState(1);
  const [membrosSelecionados, setMembrosSelecionados] = useState([]);

  // Combina os voluntários sem grupo com os membros atuais do grupo (para o modo de edição)
  const options = useMemo(() => {
    const membrosAtuais = vinculo?.membros || [];
    const todosParaSelecao = [...voluntariosDisponiveis, ...membrosAtuais];
    // Remove duplicados
    const uniqueVoluntarios = Array.from(new Map(todosParaSelecao.map(item => [item.id_voluntario, item])).values());
    
    return uniqueVoluntarios.map(vol => ({
      value: vol.id_voluntario,
      label: vol.nome_voluntario
    }));
  }, [voluntariosDisponiveis, vinculo]);

  useEffect(() => {
    if (vinculo) { // Preenche o form se estiver editando
      setNome(vinculo.nome_grupo || '');
      setLimite(vinculo.limite_escalas_grupo || 1);
      // Pre-seleciona os membros atuais do grupo no seletor
      const membrosAtuaisFormatados = (vinculo.membros || []).map(m => ({
          value: m.id_voluntario,
          label: m.nome_voluntario
      }));
      setMembrosSelecionados(membrosAtuaisFormatados);
    } else { // Limpa o form para um novo
      setNome('');
      setLimite(1);
      setMembrosSelecionados([]);
    }
  }, [vinculo]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave({
      id_grupo: vinculo?.id_grupo,
      nome_grupo: nome,
      limite_escalas_grupo: limite,
      membros_ids: membrosSelecionados.map(m => m.value)
    });
  };

  return (
    <form onSubmit={handleSubmit} className="vinculo-form">
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="nome_grupo">Nome do Grupo</label>
          <input id="nome_grupo" type="text" value={nome} onChange={(e) => setNome(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="limite_grupo">Limite de escalas/mês</label>
          <input id="limite_grupo" type="number" min="1" max="5" value={limite} onChange={(e) => setLimite(parseInt(e.target.value))} required />
        </div>
      </div>
      <div className="form-group">
        <label>Membros do Grupo (2 a 4)</label>
        <Select
            isMulti
            options={options}
            value={membrosSelecionados}
            onChange={setMembrosSelecionados}
            className="react-select-container"
            classNamePrefix="react-select"
            placeholder="Selecione os voluntários..."
            noOptionsMessage={() => "Nenhum voluntário disponível"}
        />
      </div>
      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-cancel">Cancelar</button>
        <button type="submit" className="btn-save">Salvar</button>
      </div>
    </form>
  );
}

export default FormVinculo;