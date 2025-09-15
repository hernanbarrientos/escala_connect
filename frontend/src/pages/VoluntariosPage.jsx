// arquivo: frontend/src/pages/VoluntariosPage.jsx (Versão Final 100% Completa)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormVoluntario from '../components/FormVoluntario';
import '../styles/ManagementPage.css';

function VoluntariosPage() {
  // Estados para os dados principais da página
  const [voluntarios, setVoluntarios] = useState([]);
  const [funcoes, setFuncoes] = useState([]);
  const [servicos, setServicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados para controlar o Modal de formulário
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [currentVoluntario, setCurrentVoluntario] = useState(null);

  // Estados para controlar o Modal de confirmação
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [volunteerToDelete, setVolunteerToDelete] = useState(null);

  // Estados para a funcionalidade de Busca e Paginação
  const [searchTerm, setSearchTerm] = useState('');
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [showInactive, setShowInactive] = useState(false);

  // Efeito que busca os dados iniciais quando a página carrega ou o filtro de inativos muda
  useEffect(() => {
    fetchInitialData();
  }, [showInactive]);

  // Função principal para buscar todos os dados necessários para a página
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

  // --- Funções Handler para as Ações de CRUD ---

  const handleOpenAddModal = () => {
    setCurrentVoluntario(null);
    setIsFormModalOpen(true);
  };
  
  const handleOpenEditModal = async (voluntario) => {
    try {
      const response = await api.get(`/voluntarios/${voluntario.id_voluntario}/detalhes`);
      setCurrentVoluntario(response.data);
      setIsFormModalOpen(true);
    } catch (err) {
      setError("Falha ao carregar detalhes do voluntário para edição.");
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
      await fetchInitialData(); // Recarrega os dados após salvar
    } catch (err) {
      setError("Falha ao salvar o voluntário. Verifique o console do backend para mais detalhes.");
    }
  };
  
  // Funções para controlar o modal de confirmação de inativação
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
    
    // Atualização Otimista: remove o voluntário da lista na tela imediatamente
    setVoluntarios(prev => prev.filter(v => v.id_voluntario !== volunteerToDelete.id_voluntario));
    closeConfirmModal();

    try {
      // Em segundo plano, envia a requisição para a API
      await api.delete(`/voluntarios/${volunteerToDelete.id_voluntario}`);
      // Se a API funcionou, ótimo. A tela já está atualizada.
      // Opcional: recarregar dados para garantir consistência total.
      await fetchInitialData(); 
    } catch(err) {
      // Se a API falhar, desfaz a alteração na tela e mostra um erro.
      setError("Falha ao inativar o voluntário. A alteração foi desfeita.");
      setVoluntarios(originalVolunteers); // Restaura a lista original
    }
  };


  // Lógica para filtrar e paginar os voluntários que serão exibidos na tabela
  const filteredVoluntarios = voluntarios.filter(vol =>
    vol.nome_voluntario.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const displayedVoluntarios = itemsPerPage === -1 ? filteredVoluntarios : filteredVoluntarios.slice(0, itemsPerPage);

  if (loading) return <p>Carregando...</p>;
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
                <button onClick={() => handleOpenEditModal(vol)} className="action-btn edit-btn" title="Editar">✏️</button>
                {vol.ativo && <button onClick={() => openConfirmModal(vol)} className="action-btn delete-btn" title="Inativar">🗑️</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal do Formulário de Edição/Criação */}
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
      </Modal>

      {/* Modal de Confirmação para Inativar */}
      <Modal
        isOpen={isConfirmModalOpen}
        onClose={closeConfirmModal}
        title="Confirmar Ação"
      >
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