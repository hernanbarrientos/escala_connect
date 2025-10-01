// arquivo: frontend/src/pages/VoluntariosPage.jsx (Versão Final Completa)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormVoluntario from '../components/FormVoluntario';
import FormIndisponibilidade from '../components/FormIndisponibilidade';
import ActionFeedbackModal from '../components/ActionFeedbackModal';
import Spinner from '../components/Spinner';
import '../styles/ManagementPage.css';
import './VoluntariosPage.css';

function VoluntariosPage() {
  const [voluntarios, setVoluntarios] = useState([]);
  const [funcoes, setFuncoes] = useState([]);
  const [servicos, setServicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [currentVoluntario, setCurrentVoluntario] = useState(null);

  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [volunteerToDelete, setVolunteerToDelete] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [showInactive, setShowInactive] = useState(false);

  // State para controlar o spinner do botão de edição
  const [loadingVoluntarioId, setLoadingVoluntarioId] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, [showInactive]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const idMinisterio = 1; // Virá do login no futuro
      
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

  const handleOpenAddModal = () => {
    setCurrentVoluntario(null);
    setIsFormModalOpen(true);
  };
  
  const handleOpenEditModal = async (voluntario) => {
    setLoadingVoluntarioId(voluntario.id_voluntario);
    try {
      const response = await api.get(`/voluntarios/${voluntario.id_voluntario}/detalhes`);
      setCurrentVoluntario(response.data);
      setIsFormModalOpen(true);
    } catch (err) {
      setError("Falha ao carregar detalhes do voluntário para edição.");
    } finally {
      setLoadingVoluntarioId(null);
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
      setError("Falha ao salvar o voluntário. Verifique o console do backend para mais detalhes.");
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
    try {
      await api.delete(`/voluntarios/${volunteerToDelete.id_voluntario}`);
    } catch(err) {
      setError("Falha ao inativar o voluntário.");
      throw err; // Lança o erro para o ActionFeedbackModal saber que falhou
    }
  };

  const filteredVoluntarios = voluntarios.filter(vol =>
    vol.nome_voluntario.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const displayedVoluntarios = itemsPerPage === -1 ? filteredVoluntarios : filteredVoluntarios.slice(0, itemsPerPage);

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
                <button
                  onClick={() => handleOpenEditModal(vol)}
                  className="action-btn edit-btn"
                  title="Editar"
                  disabled={loadingVoluntarioId === vol.id_voluntario}
                >
                  {loadingVoluntarioId === vol.id_voluntario ? (
                    <div className="spinner-inline"></div>
                  ) : (
                    '✏️'
                  )}
                </button>
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
        {currentVoluntario && <FormIndisponibilidade voluntario={currentVoluntario} />}
      </Modal>

      <ActionFeedbackModal
        isOpen={isConfirmModalOpen}
        onClose={closeConfirmModal}
        title="Confirmar Ação"
        confirmationMessage={`Você tem certeza que deseja INATIVAR o voluntário "${volunteerToDelete?.nome_voluntario}"? Ele não será mais incluído na geração automática de escalas.`}
        action={handleConfirmDelete}
        onSuccess={fetchInitialData}
      />
    </div>
  );
}

export default VoluntariosPage;