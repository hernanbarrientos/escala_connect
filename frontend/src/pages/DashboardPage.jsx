import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Spinner from '../components/Spinner';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import './DashboardPage.css';

ChartJS.register(ArcElement, Tooltip, Legend, Title, CategoryScale, LinearScale, BarElement);



function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const idMinisterio = 1;
        const response = await api.get(`/ministerios/${idMinisterio}/dashboard`);
        setData(response.data);
      } catch (error) {
        console.error("Falha ao buscar dados do dashboard", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const calcularDiasInativo = (dataString) => {
  if (!dataString) return null;
  const dataInativacao = new Date(dataString);
  const hoje = new Date();
  const diffTime = Math.abs(hoje - dataInativacao);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
  return diffDays;
};

  // Otimização: useMemo evita que os dados do gráfico sejam recalculados a cada renderização
  const pieChartData = useMemo(() => {
    if (!data?.grafico_niveis) return null;
    return {
      labels: Object.keys(data.grafico_niveis),
      datasets: [{
        data: Object.values(data.grafico_niveis),
        backgroundColor: ['#0d47a1', '#1976d2', '#42a5f5'],
        borderColor: '#262730', // Cor de fundo do card
        borderWidth: 2,
      }],
    };
  }, [data]);

  const barChartData = useMemo(() => {
    if (!data?.grafico_funcoes) return null;
    return {
      labels: Object.keys(data.grafico_funcoes),
      datasets: [{
        label: 'Nº de Voluntários',
        data: Object.values(data.grafico_funcoes),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        borderRadius: 3,
      }],
    };
  }, [data]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom', 
        labels: {
          color: '#a0a3bd',
          padding: 20, // Aumenta o espaço entre o gráfico e a legenda
          boxWidth: 15, // Define a largura da caixa de cor
        }
      }
    }
  };

  const barChartOptions = {
    ...chartOptions,
    plugins: {
        legend: { display: false } // Desliga a legenda para o gráfico de barras
    },
    scales: {
        y: {
            beginAtZero: true, // Garante que o eixo Y comece no zero
            ticks: { color: '#a0a3bd' },
            grid: { color: 'rgba(160, 163, 189, 0.2)' }
        },
        x: {
            ticks: { color: '#a0a3bd' },
            grid: { display: false }
        }
    }
  };

  if (loading) return <Spinner text="Carregando dados do dashboard..." />;
  if (!data) return <p className="error-message">Não foi possível carregar os dados do dashboard.</p>;

  return (
    <div>
      <h1>Painel do Ministério</h1>
      <p className="subtitle">Bem-vindo(a) ao seu painel de controle. Aqui você tem uma visão geral da sua equipe e escalas.</p>

      <h2 className="section-title">Visão Geral do Mês Atual</h2>
      <div className="kpi-grid">
        <div className="kpi-card"><span>👥</span><div><h3>{data.kpis.voluntarios_ativos}</h3><p>Voluntários Ativos</p></div></div>
        <div className="kpi-card"><span>🔗</span><div><h3>{data.kpis.grupos}</h3><p>Grupos (Vínculos)</p></div></div>
        <div className="kpi-card"><span>🗓️</span><div><h3>{data.kpis.eventos_mes}</h3><p>Eventos no Mês</p></div></div>
        <div className="kpi-card"><span>🎯</span><div><h3>{data.kpis.vagas_mes}</h3><p>Total de Vagas no Mês</p></div></div>
      </div>

      <h2 className="section-title">Análise da Equipe</h2>
      <div className="charts-grid">
        <div className="chart-container">
          <h3>Distribuição por Nível de Experiência</h3>
          {pieChartData && <Pie data={pieChartData} options={chartOptions} />}
        </div>
        <div className="chart-container">
          <h3>Nº de Voluntários Aptos por Função</h3>
          {barChartData && <Bar data={barChartData} options={barChartOptions} />}
        </div>
      </div>
      
      <div className="atencao-grid">
        <div className="atencao-card">
          <h3>Voluntários Inativos</h3>
          {data.pontos_atencao.voluntarios_inativos.length > 0 ? (
            <>
              <div className="warning-box">
                Você possui {data.pontos_atencao.voluntarios_inativos.length} voluntário(s) inativo(s).
              </div>
              <ul>
                {data.pontos_atencao.voluntarios_inativos.map((vol, index) => {
                  // AQUI ESTAVA O ERRO: O frontend recebia um objeto 'vol' e tentava imprimir direto.
                  // Agora acessamos vol.nome e vol.data corretamente.
                  const dias = calcularDiasInativo(vol.data);
                  
                  return (
                    <li key={index} className="inactive-item">
                      <span className="name">{vol.nome}</span>
                      {dias !== null && (
                        <span style={{ marginLeft: '10px', color: '#ff6b6b', fontSize: '0.85em', fontWeight: 'bold' }}>
                          ({dias} {dias === 1 ? 'dia' : 'dias'} off)
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </>
          ) : (
            <div className="success-box">Ótimo! Nenhum voluntário inativo.</div>
          )}
          <button onClick={() => navigate('/voluntarios')} className="manage-btn">Gerenciar voluntários</button>
        </div>
        
        <div className="atencao-card">
          <h3>Pontos de Atenção</h3>
          {data.pontos_atencao.voluntarios_sem_funcao.length > 0 ? (
            <div className="error-box">
              <p><strong>Voluntários ATIVOS sem função definida:</strong></p>
              <ul>
                {data.pontos_atencao.voluntarios_sem_funcao.map(nome => <li key={nome}>{nome}</li>)}
              </ul>
            </div>
          ) : (
            <div className="success-box">Todos os voluntários ativos possuem pelo menos uma função.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;