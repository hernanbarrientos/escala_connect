// arquivo: frontend/src/pages/VinculosPage.jsx (Versão com Carga Sequencial)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormVinculo from '../components/FormVinculo';
import '../styles/ManagementPage.css';
import Spinner from '../components/Spinner';
import ActionFeedbackModal from '../components/ActionFeedbackModal';

function VinculosPage() {
  const [grupos, setGrupos] = useState([]);
  const [voluntariosSemGrupo, setVoluntariosSemGrupo] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentVinculo, setCurrentVinculo] = useState(null);

    // States para o modal de confirmação
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [grupoToDelete, setGrupoToDelete] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  // << FUNÇÃO ALTERADA PARA CARREGAMENTO SEQUENCIAL >>
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null); // Limpa erros anteriores
      const idMinisterio = 1;

      // 1. Busca os grupos primeiro
      const resGrupos = await api.get(`/ministerios/${idMinisterio}/grupos`);
      setGrupos(resGrupos.data);
      
      // 2. Depois, busca os voluntários sem grupo
      const resVoluntarios = await api.get(`/ministerios/${idMinisterio}/voluntarios-sem-grupo`);
      setVoluntariosSemGrupo(resVoluntarios.data);

    } catch (err) {
      setError("Falha ao carregar dados dos vínculos. Verifique o console do backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAddModal = () => {
    setCurrentVinculo(null);
    setIsModalOpen(true);
  };
  
  const handleOpenEditModal = async (grupo) => {
    try {
      const response = await api.get(`/grupos/${grupo.id_grupo}/detalhes`);
      setCurrentVinculo(response.data);
      setIsModalOpen(true);
    } catch (err) {
      setError("Falha ao carregar detalhes do grupo para edição.");
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentVinculo(null);
  };
  
  const handleSaveVinculo = async (vinculoData) => {
    const idMinisterio = 1;
    try {
      if (vinculoData.id_grupo) {
        await api.put(`/grupos/${vinculoData.id_grupo}`, vinculoData);
      } else {
        await api.post(`/ministerios/${idMinisterio}/grupos`, vinculoData);
      }
      handleCloseModal();
      await fetchData(); // Recarrega todos os dados
    } catch (err) {
      setError("Falha ao salvar o vínculo.");
    }
  };
  
// Função que abre o modal de confirmação
  const handleDeleteClick = (grupo) => {
    setGrupoToDelete(grupo);
    setIsConfirmModalOpen(true);
  };
  
  // Ação de exclusão
  const handleDeleteVinculo = async () => {
    if (!grupoToDelete) return;
    try {
      await api.delete(`/grupos/${grupoToDelete.id_grupo}`);
    } catch (err) {
      setError("Falha ao excluir o vínculo.");
      throw err;
    }
  };

  if (loading) return <Spinner text="Carregando vínculos..." />;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Gerenciar Vínculos (Grupos)</h1>
        <button onClick={handleOpenAddModal} className="add-btn">+ Adicionar Novo Grupo</button>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Nome do Grupo</th>
            <th>Membros</th>
            <th>Limite/Mês</th>
            <th className="actions">Ações</th>
          </tr>
        </thead>
        <tbody>
          {grupos.map((grupo) => (
            <tr key={grupo.id_grupo}>
              <td>{grupo.nome_grupo}</td>
              <td>{grupo.membros}</td>
              <td>{grupo.limite_escalas_grupo}</td>
              <td className="actions">
                <button onClick={() => handleOpenEditModal(grupo)} className="action-btn edit-btn" title="Editar">✏️</button>
                <button onClick={() => handleDeleteClick(grupo)} className="action-btn delete-btn" title="Excluir">🗑️</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal isOpen={isModalOpen} onClose={handleCloseModal} title={currentVinculo ? "Editar Grupo" : "Adicionar Novo Grupo"}>
        <FormVinculo 
            vinculo={currentVinculo}
            voluntariosDisponiveis={voluntariosSemGrupo}
            onSave={handleSaveVinculo}
            onCancel={handleCloseModal}
        />
      </Modal>

      <ActionFeedbackModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        title="Confirmar Exclusão"
        confirmationMessage={`Tem certeza que deseja excluir o grupo "${grupoToDelete?.nome_grupo}"? Os voluntários ficarão sem vínculo.`}
        action={handleDeleteVinculo}
        onSuccess={fetchData} // Recarrega os dados após o sucesso
      />
    </div>
  );
}

export default VinculosPage;