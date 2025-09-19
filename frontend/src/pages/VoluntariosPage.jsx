// arquivo: frontend/src/pages/VoluntariosPage.jsx (CORRIGIDO)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormVoluntario from '../components/FormVoluntario';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import '../styles/ManagementPage.css';
import './VoluntariosPage.css';
import Spinner from '../components/Spinner';


function VoluntariosPage() {
  const [voluntarios, setVoluntarios] = useState([]);
  const [funcoes, setFuncoes] = useState([]);
  const [servicos, setServicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

// 1. NOVO STATE: Armazena o ID do voluntário que está a ser carregado
  const [loadingVoluntarioId, setLoadingVoluntarioId] = useState(null);

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [currentVoluntario, setCurrentVoluntario] = useState(null);

  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [volunteerToDelete, setVolunteerToDelete] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [showInactive, setShowInactive] = useState(false);

  // --- ESTADOS PARA INDISPONIBILIDADE (AGORA USADOS DENTRO DO MODAL) ---
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [indisponibilidades, setIndisponibilidades] = useState(new Set());

  useEffect(() => {
    fetchInitialData();
  }, [showInactive]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const idMinisterio = 1;
      const [resVoluntarios, resFuncoes, resServicos] = await Promise.all([
        api.get(`/ministerios/${idMinisterio}/voluntarios?inativos=${showInactive}`),
        api.get(`/ministerios/${idMinisterio}/funcoes`),
        api.get(`/ministerios/${idMinisterio}/servicos`)
      ]);
      setVoluntarios(resVoluntarios.data);
      setFuncoes(resFuncoes.data);
      setServicos(resServicos.data);
    } catch (err) {
      setError("Falha ao carregar dados iniciais.");
    } finally {
      setLoading(false);
    }
  };
  
  // Efeito para buscar indisponibilidades QUANDO O MODAL ABRE ou a data do calendário muda
  useEffect(() => {
    const fetchIndisponibilidades = async () => {
      if (currentVoluntario && isFormModalOpen) { // Só busca se o modal estiver aberto
        try {
          const ano = selectedDate.getFullYear();
          const mes = selectedDate.getMonth() + 1;
          const response = await api.get(`/voluntarios/${currentVoluntario.id_voluntario}/indisponibilidade/${ano}/${mes}`);
          const datasComoString = response.data.map(d => new Date(d + 'T00:00:00').toDateString());
          setIndisponibilidades(new Set(datasComoString));
        } catch (err) {
          console.error("Falha ao buscar indisponibilidades", err);
          setIndisponibilidades(new Set());
        }
      }
    };
    fetchIndisponibilidades();
  }, [currentVoluntario, selectedDate, isFormModalOpen]); // Depende da abertura do modal

  // Função para salvar as indisponibilidades
  const handleUpdateIndisponibilidade = async (newDatesSet) => {
    if (!currentVoluntario) return;
    const ano = selectedDate.getFullYear();
    const mes = selectedDate.getMonth() + 1;
    const datasParaEnviar = Array.from(newDatesSet).map(dateString => {
        const d = new Date(dateString);
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    });

    try {
      await api.put(`/voluntarios/${currentVoluntario.id_voluntario}/indisponibilidade/${ano}/${mes}`, {
        datas: datasParaEnviar
      });
      // Atualiza o estado local para refletir a mudança imediatamente
      setIndisponibilidades(newDatesSet);
    } catch(err) {
      setError("Falha ao salvar indisponibilidades.");
    }
  };
  
  // Função chamada ao clicar em uma data no calendário
  const handleDateClick = (date) => {
    const newSelection = new Set(indisponibilidades);
    const dateString = date.toDateString();
    if (newSelection.has(dateString)) {
      newSelection.delete(dateString);
    } else {
      newSelection.add(dateString);
    }
    // Chama a função que envia os dados para a API
    handleUpdateIndisponibilidade(newSelection);
  };

  const handleOpenAddModal = () => {
    setCurrentVoluntario(null);
    setSelectedDate(new Date()); // Reseta a data
    setIndisponibilidades(new Set()); // Limpa as indisponibilidades
    setIsFormModalOpen(true);
  };
  
  // 2. MODIFICADO: A função handleOpenEditModal agora controla o estado de loading
  const handleOpenEditModal = async (voluntario) => {
    setLoadingVoluntarioId(voluntario.id_voluntario); // Ativa o spinner para este ID
    try {
      const response = await api.get(`/voluntarios/${voluntario.id_voluntario}/detalhes`);
      setCurrentVoluntario(response.data);
      setSelectedDate(new Date());
      setIsFormModalOpen(true);
    } catch (err) {
      setError("Falha ao carregar detalhes do voluntário para edição.");
    } finally {
      setLoadingVoluntarioId(null); // Desativa o spinner no final (sucesso ou erro)
    }
  };

  const handleCloseFormModal = () => {
    setIsFormModalOpen(false);
    setCurrentVoluntario(null);
  };

  const handleSaveVoluntario = async (voluntarioData) => {
    try {
      const idMinisterio = 1;
      if (voluntarioData.id_voluntario) {
        await api.put(`/voluntarios/${voluntarioData.id_voluntario}`, voluntarioData);
      } else {
        await api.post(`/ministerios/${idMinisterio}/voluntarios`, voluntarioData);
      }
      handleCloseFormModal();
      await fetchInitialData();
    } catch (err) {
      setError("Falha ao salvar o voluntário.");
    }
  };
  
  const openConfirmModal = (voluntario) => {
    setVolunteerToDelete(voluntario);
    setIsConfirmModalOpen(true);
  };

  const closeConfirmModal = () => {
    setVolunteerToDelete(null);
    setIsConfirmModalOpen(false);
  };
  
  const handleConfirmDelete = async () => {
    if (!volunteerToDelete) return;
    const originalVolunteers = [...voluntarios];
    setVoluntarios(prev => prev.filter(v => v.id_voluntario !== volunteerToDelete.id_voluntario));
    closeConfirmModal();
    try {
      await api.delete(`/voluntarios/${volunteerToDelete.id_voluntario}`);
      await fetchInitialData(); 
    } catch(err) {
      setError("Falha ao inativar o voluntário. A alteração foi desfeita.");
      setVoluntarios(originalVolunteers);
    }
  };

  const filteredVoluntarios = voluntarios.filter(vol =>
    vol.nome_voluntario.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const displayedVoluntarios = itemsPerPage === -1 ? filteredVoluntarios : filteredVoluntarios.slice(0, itemsPerPage);
  
  // Função que estiliza os dias indisponíveis no calendário
  const tileClassName = ({ date, view }) => {
    if (view === 'month' && indisponibilidades.has(date.toDateString())) {
      return 'indisponivel'; // Classe CSS para dias indisponíveis
    }
    return null;
  };


  if (loading) return <Spinner text="Carregando voluntários..." />;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Gerenciar Voluntários</h1>
        <button onClick={handleOpenAddModal} className="add-btn">+ Adicionar Voluntário</button>
      </div>

      <div className="controls-bar">
        <input
          type="search"
          placeholder="Buscar por nome..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <div className="view-selector">
          <div className="checkbox-item">
            <input 
              type="checkbox" 
              id="show-inactive" 
              checked={showInactive} 
              onChange={(e) => setShowInactive(e.target.checked)} 
            />
            <label htmlFor="show-inactive">Mostrar inativos</label>
          </div>
          <label htmlFor="items-per-page">Mostrar:</label>
          <select id="items-per-page" value={itemsPerPage} onChange={(e) => setItemsPerPage(Number(e.target.value))}>
            <option value={10}>10 itens</option>
            <option value={25}>25 itens</option>
            <option value={50}>50 itens</option>
            <option value={-1}>Todos</option>
          </select>
        </div>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Nível</th>
            <th>Limite/Mês</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {displayedVoluntarios.map((vol) => (
            <tr key={vol.id_voluntario}>
              <td>{vol.nome_voluntario}</td>
              <td>{vol.nivel_experiencia}</td>
              <td>{vol.limite_escalas_mes}</td>
              <td>{vol.ativo ? 'Ativo' : 'Inativo'}</td>
              <td className="actions">
                {/* 3. MODIFICADO: Lógica condicional no botão de editar */}
                <button
                  onClick={() => handleOpenEditModal(vol)}
                  className="action-btn edit-btn"
                  title="Editar"
                  disabled={loadingVoluntarioId === vol.id_voluntario} // Desativa o botão durante o loading
                >
                  {loadingVoluntarioId === vol.id_voluntario ? (
                    <div className="spinner-inline"></div> // Mostra o spinner se o ID corresponder
                  ) : (
                    '✏️' // Mostra o ícone de lápis caso contrário
                  )}
                </button>
                {/* O botão de inativar permanece o mesmo */}
                {vol.ativo && <button onClick={() => openConfirmModal(vol)} className="action-btn delete-btn" title="Inativar">🗑️</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal 
        isOpen={isFormModalOpen} 
        onClose={handleCloseFormModal}
        title={currentVoluntario ? "Editar Voluntário" : "Adicionar Novo Voluntário"}
      >
        <FormVoluntario 
          voluntario={currentVoluntario}
          allFuncoes={funcoes}
          allServicos={servicos}
          onSave={handleSaveVoluntario}
          onCancel={handleCloseFormModal}
        />
        
        {/* --- LÓGICA DE INDISPONIBILIDADE CORRIGIDA E INTEGRADA AO MODAL --- */}
        {currentVoluntario && (
          <div className="indisponibilidade-container">
            <h3>Indisponibilidade no Mês</h3>
            <p className="instrucao">Clique nos dias em que o voluntário NÃO poderá servir. A alteração é salva automaticamente.</p>
            <Calendar
              onChange={setSelectedDate} // Altera a data de visualização do calendário
              value={selectedDate}
              onClickDay={handleDateClick} // Ação ao clicar em um dia
              tileClassName={({ date, view }) => 
                view === 'month' && indisponibilidades.has(date.toDateString()) ? 'react-calendar__tile--active' : null
              }
              onActiveStartDateChange={({ activeStartDate }) => setSelectedDate(activeStartDate)}
            />
          </div>
        )}
      </Modal>

      <Modal isOpen={isConfirmModalOpen} onClose={closeConfirmModal} title="Confirmar Ação">
        <div>
          <p>Você tem certeza que deseja <strong>INATIVAR</strong> o voluntário <strong>{volunteerToDelete?.nome_voluntario}</strong>?</p>
          <p>Ele não será mais incluído na geração automática de escalas.</p>
          <div className="form-actions">
            <button onClick={closeConfirmModal} className="btn-cancel">Cancelar</button>
            <button onClick={handleConfirmDelete} className="btn-save" style={{backgroundColor: '#ff4b4b'}}>Sim, Inativar</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default VoluntariosPage;