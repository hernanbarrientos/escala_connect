// arquivo: frontend/src/pages/VinculosPage.jsx (Versão com Carga Sequencial)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormVinculo from '../components/FormVinculo';
import '../styles/ManagementPage.css';

function VinculosPage() {
  const [grupos, setGrupos] = useState([]);
  const [voluntariosSemGrupo, setVoluntariosSemGrupo] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentVinculo, setCurrentVinculo] = useState(null);

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
  
  const handleDeleteVinculo = async (id_grupo) => {
      if (window.confirm("Tem certeza que deseja excluir este grupo? Os voluntários ficarão sem vínculo.")) {
          try {
              await api.delete(`/grupos/${id_grupo}`);
              await fetchData();
          } catch (err) {
              setError("Falha ao excluir o vínculo.");
          }
      }
  };

  if (loading) return <p>Carregando...</p>;
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
                <button onClick={() => handleDeleteVinculo(grupo.id_grupo)} className="action-btn delete-btn" title="Excluir">🗑️</button>
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
    </div>
  );
}

export default VinculosPage;