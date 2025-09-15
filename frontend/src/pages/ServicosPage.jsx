// arquivo: frontend/src/pages/ServicosPage.jsx (Versão Final com CRUD e Gestão de Cotas)

import { useState, useEffect } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import FormServico from '../components/FormServico';
import FormCotas from '../components/FormCotas';
import '../styles/ManagementPage.css';

function ServicosPage() {
  // Estados para dados da página
  const [servicos, setServicos] = useState([]);
  const [allFuncoes, setAllFuncoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados para controlar o Modal de Adicionar/Editar Serviço
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentServico, setCurrentServico] = useState(null);
  
  // Estados para controlar o Modal de Cotas
  const [isCotasModalOpen, setIsCotasModalOpen] = useState(false);
  const [selectedServicoForCotas, setSelectedServicoForCotas] = useState(null);

  // Busca os dados iniciais (serviços e funções) quando a página carrega
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const idMinisterio = 1; // Virá do login no futuro
      const [resServicos, resFuncoes] = await Promise.all([
        api.get(`/ministerios/${idMinisterio}/servicos`),
        api.get(`/ministerios/${idMinisterio}/funcoes`)
      ]);
      setServicos(resServicos.data);
      setAllFuncoes(resFuncoes.data);
    } catch (err) {
      setError("Falha ao carregar dados iniciais.");
    } finally {
      setLoading(false);
    }
  };
  
  // --- Funções para controlar o Modal de Serviço ---
  const handleOpenAddModal = () => {
    setCurrentServico(null);
    setIsModalOpen(true);
  };
  
  const handleOpenEditModal = (servico) => {
    setCurrentServico(servico);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentServico(null);
  };

  const handleSaveServico = async (servicoData) => {
    const idMinisterio = 1;
    try {
      if (servicoData.id_servico) {
        // Se tem ID, é uma atualização (PUT)
        await api.put(`/servicos/${servicoData.id_servico}`, servicoData);
      } else {
        // Se não tem ID, é uma criação (POST)
        await api.post(`/ministerios/${idMinisterio}/servicos`, servicoData);
      }
      fetchInitialData(); // Recarrega a lista de serviços
      handleCloseModal();
    } catch (err) {
      setError("Falha ao salvar o serviço.");
    }
  };

  const handleDeleteServico = async (id_servico) => {
    if (window.confirm("Tem certeza que deseja excluir este serviço? Esta ação é irreversível.")) {
      try {
        await api.delete(`/servicos/${id_servico}`);
        fetchInitialData(); // Recarrega a lista
      } catch (err) {
        setError("Falha ao excluir o serviço.");
      }
    }
  };

  // --- Funções para controlar o Modal de Cotas ---
  const handleOpenCotasModal = (servico) => {
    setSelectedServicoForCotas(servico);
    setIsCotasModalOpen(true);
  };

  const handleCloseCotasModal = () => {
    setIsCotasModalOpen(false);
    setSelectedServicoForCotas(null);
  };

  const handleSaveCotas = async (id_servico, cotas) => {
    try {
      await api.put(`/servicos/${id_servico}/cotas`, { cotas });
      handleCloseCotasModal();
    } catch (err) {
      setError("Falha ao salvar as cotas.");
    }
  };

  const diasSemana = { 0: "Domingo", 1: "Segunda-feira", 2: "Terça-feira", 3: "Quarta-feira", 4: "Quinta-feira", 5: "Sexta-feira", 6: "Sábado" };

  if (loading) return <p>Carregando...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Gerenciar Serviços</h1>
        <button onClick={handleOpenAddModal} className="add-btn">+ Adicionar Novo Serviço</button>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Nome do Serviço</th>
            <th>Dia da Semana</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {servicos.map((servico) => (
            <tr key={servico.id_servico}>
              <td>{servico.nome_servico}</td>
              <td>{diasSemana[servico.dia_da_semana]}</td>
              <td>{servico.ativo ? 'Ativo' : 'Inativo'}</td>
              <td className="actions">
                <button onClick={() => handleOpenCotasModal(servico)} className="action-btn" title="Gerenciar Vagas/Cotas">📊</button>
                <button onClick={() => handleOpenEditModal(servico)} className="action-btn edit-btn" title="Editar">✏️</button>
                <button onClick={() => handleDeleteServico(servico.id_servico)} className="action-btn delete-btn" title="Excluir">🗑️</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal de Adicionar/Editar Serviço */}
      <Modal 
        isOpen={isModalOpen} 
        onClose={handleCloseModal}
        title={currentServico ? "Editar Serviço" : "Adicionar Novo Serviço"}
      >
        <FormServico 
          servico={currentServico}
          onSave={handleSaveServico}
          onCancel={handleCloseModal}
        />
      </Modal>

      {/* Modal para Gerenciar as Cotas */}
      <Modal 
        isOpen={isCotasModalOpen} 
        onClose={handleCloseCotasModal} 
        title={`Gerenciar Vagas para "${selectedServicoForCotas?.nome_servico}"`}
      >
        <FormCotas 
          servico={selectedServicoForCotas}
          allFuncoes={allFuncoes}
          onSave={handleSaveCotas}
          onCancel={handleCloseCotasModal}
        />
      </Modal>
    </div>
  );
}

export default ServicosPage;