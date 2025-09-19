import React, { useState, useEffect } from 'react';
import api from '../services/api';

const meses = { 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro" };

function FormIndisponibilidade({ voluntario }) {
  const [data, setData] = useState({ ano: new Date().getFullYear(), mes: new Date().getMonth() + 1 });
  const [eventos, setEventos] = useState([]);
  const [indisponiveis, setIndisponiveis] = useState(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchEventos = async () => {
      setLoading(true);
      try {
        const [resEventos, resIndisponiveis] = await Promise.all([
          api.get(`/voluntarios/${voluntario.id_voluntario}/eventos-disponiveis/${data.ano}/${data.mes}`),
          api.get(`/voluntarios/${voluntario.id_voluntario}/indisponibilidade/${data.ano}/${data.mes}`)
        ]);

        setEventos(resEventos.data);
        // O backend agora retorna uma lista de IDs de evento, não datas
        setIndisponiveis(new Set(resIndisponiveis.data)); 
      } catch (error) {
        console.error("Erro ao buscar dados de indisponibilidade:", error);
      }
      setLoading(false);
    };

    if (voluntario) {
      fetchEventos();
    }
  }, [voluntario, data]);

  const handleCheckboxChange = (id_evento) => {
    const newSelection = new Set(indisponiveis);
    if (newSelection.has(id_evento)) {
      newSelection.delete(id_evento);
    } else {
      newSelection.add(id_evento);
    }
    setIndisponiveis(newSelection);
  };
  
  const handleSave = async () => {
    try {
      await api.put(`/voluntarios/${voluntario.id_voluntario}/indisponibilidade/${data.ano}/${data.mes}`, {
        eventos_ids: Array.from(indisponiveis)
      });
      alert('Indisponibilidades salvas com sucesso!');
    } catch(err) {
      alert('Falha ao salvar indisponibilidades.');
    }
  };

  const eventosAgrupados = eventos.reduce((acc, evento) => {
    (acc[evento.nome_servico] = acc[evento.nome_servico] || []).push(evento);
    return acc;
  }, {});

  return (
    <div className="indisponibilidade-container">
      <h3>Indisponibilidade Específica no Mês</h3>
      <div className="indisponibilidade-header">
        <select value={data.mes} onChange={e => setData({ ...data, mes: parseInt(e.target.value) })}>
          {Object.entries(meses).map(([num, nome]) => <option key={num} value={num}>{nome}</option>)}
        </select>
        <select value={data.ano} onChange={e => setData({ ...data, ano: parseInt(e.target.value) })}>
          {[new Date().getFullYear(), new Date().getFullYear() + 1].map(ano => <option key={ano} value={ano}>{ano}</option>)}
        </select>
      </div>

      <p className="instrucao">Marque os eventos em que o voluntário <strong>NÃO</strong> poderá servir:</p>

      {loading ? <p>Carregando eventos...</p> : (
        <div className="servicos-list">
          {Object.keys(eventosAgrupados).length > 0 ? (
            Object.entries(eventosAgrupados).map(([nomeServico, eventosDoServico]) => (
              <div key={nomeServico} className="servico-group">
                <h4>{nomeServico}</h4>
                {eventosDoServico.sort((a,b) => new Date(a.data_evento) - new Date(b.data_evento)).map(evento => (
                  <div key={evento.id_evento} className="checkbox-item">
                    <input
                      type="checkbox"
                      id={`evento_${evento.id_evento}`}
                      checked={indisponiveis.has(evento.id_evento)}
                      onChange={() => handleCheckboxChange(evento.id_evento)}
                    />
                    <label htmlFor={`evento_${evento.id_evento}`}>
                      {new Date(evento.data_evento).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                    </label>
                  </div>
                ))}
              </div>
            ))
          ) : (
            <p>Não há eventos neste mês para os serviços em que este voluntário está disponível.</p>
          )}
        </div>
      )}
      
      <div className="form-actions">
        <button onClick={handleSave} className="btn-save">Salvar Indisponibilidades</button>
      </div>
    </div>
  );
}

export default FormIndisponibilidade;