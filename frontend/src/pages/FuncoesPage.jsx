// arquivo: frontend/src/pages/FuncoesPage.jsx (Versão Padronizada e Completa)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormFuncao from '../components/FormFuncao'; // Importa o novo formulário
import '../styles/ManagementPage.css'; // Importa o novo CSS padrão
import Spinner from '../components/Spinner';

function FuncoesPage() {
  const [funcoes, setFuncoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados para controlar o modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentFuncao, setCurrentFuncao] = useState(null);

  useEffect(() => {
    fetchFuncoes();
  }, []);

  const fetchFuncoes = async () => {
    try {
      setLoading(true);
      const idMinisterio = 1; // Virá do login no futuro
      const response = await api.get(`/ministerios/${idMinisterio}/funcoes`);
      setFuncoes(response.data);
    } catch (err) {
      setError("Falha ao buscar dados da API.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveFuncao = async (funcaoData) => {
    try {
      const idMinisterio = 1;
      if (funcaoData.id_funcao) {
        // Se tem ID, é uma atualização (PUT)
        await api.put(`/funcoes/${funcaoData.id_funcao}`, funcaoData);
      } else {
        // Se não tem ID, é uma criação (POST)
        await api.post(`/ministerios/${idMinisterio}/funcoes`, funcaoData);
      }
      handleCloseModal();
      await fetchFuncoes(); // Recarrega a lista
    } catch (err) {
      setError("Falha ao salvar a função.");
    }
  };

  const handleDeleteFuncao = async (id_funcao) => {
    if (window.confirm("Tem certeza que deseja excluir esta função?")) {
      try {
        await api.delete(`/funcoes/${id_funcao}`);
        await fetchFuncoes(); // Recarrega a lista
      } catch (err) {
        setError("Falha ao excluir a função.");
      }
    }
  };

  const handleOpenAddModal = () => {
    setCurrentFuncao(null);
    setIsModalOpen(true);
  };
  
  const handleOpenEditModal = (funcao) => {
    setCurrentFuncao(funcao);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentFuncao(null);
  };

  if (loading) return <Spinner text="Carregando voluntários..." />;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Gerenciar Funções</h1>
        <button onClick={handleOpenAddModal} className="add-btn">+ Adicionar Nova Função</button>
      </div>

      {/* MUDANÇA: A tabela agora tem as novas colunas */}
      <table className="data-table">
        <thead>
          <tr>
            <th>Nome da Função</th>
            {/* NOVA COLUNA */}
            <th>Tipo</th>
            {/* NOVA COLUNA */}
            <th>Prioridade</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {funcoes.map((funcao) => (
            <tr key={funcao.id_funcao}>
              <td>{funcao.nome_funcao}</td>
              {/* NOVO DADO SENDO EXIBIDO */}
              <td>{funcao.tipo_funcao}</td>
              {/* NOVO DADO SENDO EXIBIDO */}
              <td>{funcao.prioridade_alocacao}</td>
              <td className="actions">
                <button onClick={() => handleOpenEditModal(funcao)} className="action-btn edit-btn" title="Editar">✏️</button>
                <button onClick={() => handleDeleteFuncao(funcao.id_funcao)} className="action-btn delete-btn" title="Excluir">🗑️</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <Modal 
        isOpen={isModalOpen} 
        onClose={handleCloseModal}
        title={currentFuncao ? "Editar Função" : "Adicionar Nova Função"}
      >
        <FormFuncao 
          funcao={currentFuncao}
          onSave={handleSaveFuncao}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  );
}

export default FuncoesPage;