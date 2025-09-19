// CÓDIGO COMPLETO PARA frontend/src/pages/GerarEscalaPage.jsx

import React, { useState, useEffect, useMemo } from 'react';
import api from '../services/api';
import Spinner from '../components/Spinner';
import '../styles/ManagementPage.css';
import './GerarEscalaPage.css';

const meses = { 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro" };
const anos = [new Date().getFullYear(), new Date().getFullYear() + 1];
const getSlotKey = (item) => `${item.id_evento}-${item.id_funcao}-${item.funcao_instancia}`;

function GerarEscalaPage() {
    const [selectedMes, setSelectedMes] = useState(new Date().getMonth() + 1);
    const [selectedAno, setSelectedAno] = useState(new Date().getFullYear());
    const [escala, setEscala] = useState([]);
    const [voluntarios, setVoluntarios] = useState([]);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [creatingEvents, setCreatingEvents] = useState(false); 
    const [error, setError] = useState(null);
    const [editingSlotKey, setEditingSlotKey] = useState(null);
    const [availableVolunteers, setAvailableVolunteers] = useState([]);

    useEffect(() => {
        fetchData();
    }, [selectedMes, selectedAno]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const idMinisterio = 1;
            const [resEscala, resVoluntarios] = await Promise.all([
                api.get(`/ministerios/${idMinisterio}/escala/${selectedAno}/${selectedMes}`),
                api.get(`/ministerios/${idMinisterio}/voluntarios?inativos=false`)
            ]);
            setEscala(resEscala.data);
            setVoluntarios(resVoluntarios.data);
        } catch (err) {
            setError("Falha ao buscar dados. Tente gerar uma nova escala.");
            setEscala([]);
        } finally {
            setLoading(false);
        }
    };

    // --- NOVA FUNÇÃO PARA CRIAR EVENTOS ---
    const handleCreateEvents = async () => {
        if (!window.confirm(`Tem certeza que deseja criar os eventos para ${meses[selectedMes]}/${selectedAno}? Eventos existentes para este mês serão substituídos.`)) {
            return;
        }
        setCreatingEvents(true);
        setError(null);
        try {
            const idMinisterio = 1; // Virá do contexto de usuário
            await api.post(`/ministerios/${idMinisterio}/eventos/criar`, {
                ano: selectedAno,
                mes: selectedMes,
            });
            alert('Eventos criados com sucesso! Você já pode definir as indisponibilidades.');
        } catch (err) {
            setError("Ocorreu um erro ao criar os eventos.");
        } finally {
            setCreatingEvents(false);
        }
    };

    const handleDownloadPdf = async () => {
        try {
            const idMinisterio = 1; // Do contexto
            const response = await api.get(
                `/ministerios/${idMinisterio}/escala/${selectedAno}/${selectedMes}/pdf`,
                { responseType: 'blob' } // Importante: diz ao axios para tratar a resposta como um arquivo
            );
            
            // Cria um link temporário para o download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `escala_${selectedAno}_${selectedMes}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);

        } catch (error) {
            setError("Falha ao gerar o PDF.");
        }
    };


    const handleGerarEscala = async () => {
        if (!window.confirm(`Tem certeza que deseja gerar uma nova escala para ${meses[selectedMes]}/${selectedAno}? A escala atual (se existir) será apagada.`)) {
            return;
        }
        setGenerating(true);
        setError(null);
        try {
            const idMinisterio = 1;
            await api.post(`/ministerios/${idMinisterio}/escala/gerar`, {
                ano: selectedAno,
                mes: selectedMes,
            });
            await fetchData();
        } catch (err) {
            setError("Ocorreu um erro ao gerar a escala.");
        } finally {
            setGenerating(false);
        }
    };

    const handleEditSlot = async (item) => {
        if (editingSlotKey) return;
        try {
            // ALTERAÇÃO: Chama o novo endpoint inteligente
            const response = await api.get(`/escala/vaga-elegiveis`, {
                params: {
                    id_funcao: item.id_funcao,
                    id_evento: item.id_evento
                }
            });

            // Adiciona o voluntário atual à lista, caso ele precise ser re-selecionado
            const currentVolunteerInList = response.data.some(v => v.id_voluntario === item.id_voluntario);
            let finalVolunteerList = response.data;
            if (item.id_voluntario && !currentVolunteerInList) {
                finalVolunteerList.unshift({ id_voluntario: item.id_voluntario, nome_voluntario: item.nome_voluntario });
            }
            
            setAvailableVolunteers(finalVolunteerList);
            setEditingSlotKey(getSlotKey(item));
        } catch (err) {
            setError("Falha ao buscar voluntários elegíveis para esta vaga.");
        }
    };

    const handleUpdateSlot = async (e, item) => {
        const novoVoluntarioId = e.target.value ? parseInt(e.target.value) : null;
        const vagaParaAtualizar = {
            id_evento: item.id_evento,
            id_funcao: item.id_funcao,
            funcao_instancia: item.funcao_instancia,
            id_voluntario: novoVoluntarioId,
        };
        try {
            await api.put(`/escala/vaga`, vagaParaAtualizar);
            setEditingSlotKey(null);
            await fetchData();
        } catch (err) {
            setError("Falha ao atualizar a vaga.");
            setEditingSlotKey(null);
        }
    };

    const escalaAgrupadaPorServico = useMemo(() => {
        if (!escala || escala.length === 0) return {};
        return escala.reduce((acc, item) => {
            const servicoKey = item.nome_servico;
            const eventoKey = item.id_evento;
            if (!acc[servicoKey]) {
                acc[servicoKey] = {};
            }
            if (!acc[servicoKey][eventoKey]) {
                acc[servicoKey][eventoKey] = {
                    id_evento: item.id_evento,
                    nome_servico: item.nome_servico,
                    dia: new Date(item.data_evento).getUTCDate(),
                    data_completa: item.data_evento,
                    equipe: []
                };
            }
            acc[servicoKey][eventoKey].equipe.push({ ...item });
            return acc;
        }, {});
    }, [escala]);

    const voluntarioContagemMap = useMemo(() => {
        const contagem = escala.reduce((acc, item) => {
            if (item.id_voluntario) {
                acc[item.id_voluntario] = (acc[item.id_voluntario] || 0) + 1;
            }
            return acc;
        }, {});

        const mapa = {};
        voluntarios.forEach(vol => {
            mapa[vol.id_voluntario] = {
                escalado_vezes: contagem[vol.id_voluntario] || 0,
                limite: vol.limite_escalas_mes
            };
        });
        return mapa;
    }, [escala, voluntarios]);

    const voluntariosNaoEscalados = useMemo(() => {
        return voluntarios
            .filter(vol => !(voluntarioContagemMap[vol.id_voluntario]?.escalado_vezes > 0))
            .sort((a,b) => a.nome_voluntario.localeCompare(b.nome_voluntario));
    }, [voluntarios, voluntarioContagemMap]);

    const renderContent = () => {
        if (loading || generating) {
            return <Spinner text={generating ? "O algoritmo está trabalhando... Isso pode levar alguns segundos." : "Carregando escala..."} />;
        }
        if (error) { return <p className="error-message">{error}</p>; }
        if (Object.keys(escalaAgrupadaPorServico).length === 0) {
            return <div className="spinner-container"><p>Nenhuma escala encontrada. Selecione o período e clique em "Gerar Escala Automática".</p></div>;
        }
        const ordemServicos = ["Domingo Manhã", "Domingo Noite", "Quinta-feira"];
        const servicosOrdenados = Object.keys(escalaAgrupadaPorServico).sort((a,b) => ordemServicos.indexOf(a) - ordemServicos.indexOf(b));

        return (
            <div>
                {servicosOrdenados.map(nomeServico => (
                    <div key={nomeServico} className="servico-row">
                        <div className="servico-row-header">{nomeServico}</div>
                        <div className="escala-grid">
                            {Object.values(escalaAgrupadaPorServico[nomeServico]).sort((a,b) => a.dia - b.dia).map(evento => (
                                <div key={evento.id_evento} className="evento-card">
                                    <div className="evento-card-header">
                                        <h3>{new Date(evento.data_completa).toLocaleDateString('pt-BR', {weekday: 'long', timeZone: 'UTC'})}</h3>
                                        <span className="data">{evento.dia}</span>
                                    </div>
                                    <div>
                                        {[...evento.equipe].sort((a, b) => {
                                            const ordemFuncoes = ['Líder', 'Líder de Escala', 'Store', 'Apoio'];
                                            const prioridadeA = ordemFuncoes.indexOf(a.nome_funcao);
                                            const prioridadeB = ordemFuncoes.indexOf(b.nome_funcao);
                                            return (prioridadeA === -1 ? 99 : prioridadeA) - (prioridadeB === -1 ? 99 : prioridadeB);
                                        }).map((item, index) => {
                                            const currentSlotKey = getSlotKey(item);
                                            const contagem = voluntarioContagemMap[item.id_voluntario];
                                            const sobrecarregado = contagem && contagem.escalado_vezes > contagem.limite;

                                            return (
                                                <div key={currentSlotKey} className="escala-item">
                                                    <span className="escala-item-funcao">{item.nome_funcao.replace('Líder de Escala', 'Líder')}:</span>
                                                    {editingSlotKey === currentSlotKey ? (
                                                        <select className="escala-item-select" value={item.id_voluntario || ''} onChange={(e) => handleUpdateSlot(e, item)} onBlur={() => setEditingSlotKey(null)} autoFocus>
                                                            <option value="">-- VAGO --</option>
                                                            {availableVolunteers.map(vol => (<option key={vol.id_voluntario} value={vol.id_voluntario}>{vol.nome_voluntario}</option>))}
                                                        </select>
                                                    ) : (
                                                        <span onClick={() => handleEditSlot(item)} className="escala-item-voluntario editable" style={{ color: sobrecarregado ? '#ff4b4b' : 'inherit' }}>
                                                            {item.nome_voluntario || '-- VAGO --'}
                                                            {contagem && item.nome_voluntario && ` (${contagem.escalado_vezes}/${contagem.limite})`}
                                                        </span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
                <h2 className="contagem-header">Voluntários Não Escalados Neste Mês</h2>
                {voluntariosNaoEscalados.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Nome do Voluntário</th>
                                <th>Nível</th>
                                <th>Limite (Mês)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {voluntariosNaoEscalados.map(vol => (
                                <tr key={vol.id_voluntario}>
                                    <td>{vol.nome_voluntario}</td>
                                    <td>{vol.nivel_experiencia}</td>
                                    <td>{vol.limite_escalas_mes}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="spinner-container" style={{padding: '2rem'}}>
                        <p>✅ Ótimo! Todos os voluntários disponíveis foram escalados pelo menos uma vez.</p>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div>
            <h1>Gerar e Visualizar Escala</h1>
            <div className="escala-controls">
                <select value={selectedMes} onChange={(e) => setSelectedMes(Number(e.target.value))} disabled={generating}>
                    {Object.entries(meses).map(([num, nome]) => <option key={num} value={num}>{nome}</option>)}
                </select>
                <select value={selectedAno} onChange={(e) => setSelectedAno(Number(e.target.value))} disabled={generating}>
                    {anos.map(ano => <option key={ano} value={ano}>{ano}</option>)}
                </select>
                                {/* --- NOVO BOTÃO ADICIONADO AQUI --- */}
                <button onClick={handleCreateEvents} disabled={loading || creatingEvents} className="add-btn" style={{backgroundColor: '#17a2b8'}}>
                    {creatingEvents ? 'Criando...' : 'Criar Eventos do Mês'}
                </button>
                <button onClick={handleGerarEscala} disabled={loading || generating} className="add-btn">
                    {generating ? 'Gerando...' : 'Gerar Escala Automática'}
                </button>
                {/* --- BOTÃO DE PDF ADICIONADO AQUI --- */}
                <button 
                    onClick={handleDownloadPdf} 
                    disabled={escala.length === 0 || loading || generating} 
                    className="add-btn" 
                    style={{backgroundColor: '#6c757d'}} // Um cinza para diferenciar
                >
                    Baixar PDF
                </button>
            </div>
            {renderContent()}
        </div>
    );
}

export default GerarEscalaPage;