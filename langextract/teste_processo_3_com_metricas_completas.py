#!/usr/bin/env python3
"""
Teste LangExtract com Azure OpenAI - Processo 07624573620258070016
Com métricas detalhadas e comparação com processos anteriores.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar LangExtract
import langextract as lx

@dataclass
class MetricaTempo:
    """Classe para armazenar métricas de tempo."""
    nome: str
    inicio: float
    fim: float = 0.0
    duracao: float = 0.0
    
    def finalizar(self):
        """Finaliza a medição de tempo."""
        self.fim = time.time()
        self.duracao = self.fim - self.inicio
        return self.duracao

class MedidorPerformanceCompleto:
    """Classe para medir performance detalhada com comparações."""
    
    def __init__(self, processo_numero: str):
        self.processo_numero = processo_numero
        self.metricas: List[MetricaTempo] = []
        self.inicio_total = time.time()
        self.dados_processo = {}
        self.inicio_tarefa_completa = time.time()  # Para medir tempo total da tarefa
    
    def iniciar_metrica(self, nome: str) -> MetricaTempo:
        """Inicia uma nova métrica de tempo."""
        metrica = MetricaTempo(nome=nome, inicio=time.time())
        self.metricas.append(metrica)
        print(f"⏱️  Iniciando: {nome}")
        return metrica
    
    def finalizar_metrica(self, metrica: MetricaTempo):
        """Finaliza uma métrica de tempo."""
        duracao = metrica.finalizar()
        print(f"✅ Concluído: {metrica.nome} - {duracao:.2f}s")
        return duracao
    
    def tempo_total(self) -> float:
        """Calcula o tempo total decorrido."""
        return time.time() - self.inicio_total
    
    def tempo_tarefa_completa(self) -> float:
        """Calcula o tempo total da tarefa completa."""
        return time.time() - self.inicio_tarefa_completa
    
    def relatorio_performance(self) -> Dict[str, Any]:
        """Gera relatório completo de performance."""
        tempo_total = self.tempo_total()
        tempo_tarefa = self.tempo_tarefa_completa()
        
        relatorio = {
            'processo_numero': self.processo_numero,
            'tempo_total_segundos': tempo_total,
            'tempo_total_formatado': str(timedelta(seconds=int(tempo_total))),
            'tempo_tarefa_completa_segundos': tempo_tarefa,
            'tempo_tarefa_completa_formatado': str(timedelta(seconds=int(tempo_tarefa))),
            'inicio_processamento': datetime.fromtimestamp(self.inicio_total).strftime('%H:%M:%S'),
            'fim_processamento': datetime.now().strftime('%H:%M:%S'),
            'inicio_tarefa': datetime.fromtimestamp(self.inicio_tarefa_completa).strftime('%H:%M:%S'),
            'metricas_detalhadas': []
        }
        
        for metrica in self.metricas:
            if metrica.duracao > 0:
                relatorio['metricas_detalhadas'].append({
                    'etapa': metrica.nome,
                    'duracao_segundos': metrica.duracao,
                    'duracao_formatada': f"{metrica.duracao:.2f}s",
                    'percentual_tempo_total': (metrica.duracao / tempo_total) * 100
                })
        
        # Adicionar dados do processo
        relatorio.update(self.dados_processo)
        
        return relatorio

def carregar_texto_processo(medidor: MedidorPerformanceCompleto) -> str:
    """Carrega o texto do processo jurídico com medição de tempo."""
    metrica = medidor.iniciar_metrica("Carregamento do arquivo")
    
    caminho_arquivo = "docs/examples/processos/07624573620258070016/processo_07624573620258070016.md"
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            texto = f.read()
        
        # Armazenar dados do processo
        medidor.dados_processo.update({
            'arquivo': caminho_arquivo,
            'tamanho_caracteres': len(texto),
            'tamanho_linhas': texto.count('\n') + 1,
            'tamanho_kb': len(texto.encode('utf-8')) / 1024
        })
        
        print(f"📄 Arquivo carregado: {len(texto):,} caracteres ({len(texto.encode('utf-8'))/1024:.1f} KB)")
        medidor.finalizar_metrica(metrica)
        return texto
        
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        medidor.finalizar_metrica(metrica)
        return None

def criar_exemplos_juridicos_processo3(medidor: MedidorPerformanceCompleto) -> List:
    """Cria exemplos otimizados para o terceiro processo (violência contra menor)."""
    metrica = medidor.iniciar_metrica("Criação de exemplos")
    
    exemplos = [
        lx.data.ExampleData(
            text="RAISSA DOS SANTOS, natural de PLANALTINA - GO, nascida em 17/12/1997, com 27 anos, RG 3662605 SSP/DF, CPF 070.416.951-74, endereço QR 05, CJ A, LOTE 07, BURITIZINHO - SOBRADINHO II, DF.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="RAISSA DOS SANTOS",
                    attributes={
                        "nome": "RAISSA DOS SANTOS",
                        "naturalidade": "PLANALTINA - GO",
                        "data_nascimento": "17/12/1997",
                        "idade": "27 anos",
                        "rg": "3662605",
                        "orgao_expedidor": "SSP/DF",
                        "cpf": "070.416.951-74",
                        "endereco": "QR 05, CJ A, LOTE 07, BURITIZINHO - SOBRADINHO II, DF",
                        "papel": "comunicante"
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="Ocorrência 3673/2025-35ª DP, Protocolo 1744347/2025, Delegado RAFAEL LAURE MIRANDA, Escrivão ALEX YUZO MOROGUMA.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="ocorrencia",
                    extraction_text="3673/2025-35ª DP",
                    attributes={
                        "numero": "3673/2025",
                        "delegacia": "35ª DP"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="protocolo",
                    extraction_text="1744347/2025",
                    attributes={
                        "numero": "1744347/2025"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="autoridade",
                    extraction_text="RAFAEL LAURE MIRANDA",
                    attributes={
                        "nome": "RAFAEL LAURE MIRANDA",
                        "cargo": "Delegado de Polícia"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="autoridade",
                    extraction_text="ALEX YUZO MOROGUMA",
                    attributes={
                        "nome": "ALEX YUZO MOROGUMA",
                        "cargo": "Escrivão de Polícia",
                        "matricula": "0230676X"
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="KYARA DOS SANTOS, menor de idade, vítima de violência doméstica praticada por MARIA DO PERPÉTUO SOCORRO VERÍSSIMO DOS SANTOS, sua genitora.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="KYARA DOS SANTOS",
                    attributes={
                        "nome": "KYARA DOS SANTOS",
                        "idade": "menor de idade",
                        "papel": "vítima"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="MARIA DO PERPÉTUO SOCORRO VERÍSSIMO DOS SANTOS",
                    attributes={
                        "nome": "MARIA DO PERPÉTUO SOCORRO VERÍSSIMO DOS SANTOS",
                        "papel": "autora",
                        "relacao": "genitora"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="crime",
                    extraction_text="violência doméstica",
                    attributes={
                        "tipo": "violência doméstica",
                        "contexto": "contra menor de idade"
                    }
                )
            ]
        )
    ]
    
    medidor.finalizar_metrica(metrica)
    return exemplos

def extrair_dados_processo3_otimizado(texto: str, medidor: MedidorPerformanceCompleto):
    """Extrai dados do terceiro processo com configurações otimizadas."""
    metrica_total = medidor.iniciar_metrica("Extração completa (LangExtract)")
    
    print("🔍 Iniciando extração otimizada do terceiro processo jurídico...")
    
    # Prompt otimizado para o terceiro processo (violência contra menor)
    prompt = """
    Extrair informações estruturadas de processo jurídico de violência doméstica contra menor incluindo:
    
    PESSOAS ENVOLVIDAS:
    - Nome completo, CPF, RG, data de nascimento, endereço
    - Papel no processo (vítima, comunicante, autor, autoridade)
    - Dados familiares (pai, mãe, irmãos, relacionamentos)
    - Profissão, estado civil, naturalidade, idade
    - Situação de menores de idade
    
    DADOS PROCESSUAIS:
    - Número do processo, ocorrência, protocolo
    - Delegacia, vara, juizado responsável
    - Datas importantes (declarações, comunicações, decisões)
    - Tipo de procedimento (termo de declaração, medida protetiva)
    - Mandados e intimações
    
    CRIMES E COMPORTAMENTOS:
    - Violência física contra menor
    - Maus-tratos e agressões
    - Violência verbal e psicológica
    - Ambiente familiar hostil
    - Padrões de comportamento abusivo
    
    AUTORIDADES E FUNCIONÁRIOS:
    - Delegados, escrivães, promotores
    - Conselheiros tutelares
    - Oficiais de justiça
    - Matrícula e função específica
    
    MEDIDAS PROTETIVAS:
    - Medidas solicitadas e deferidas
    - Afastamento do agressor
    - Proteção de menor de idade
    - Acolhimento familiar
    
    CONSELHO TUTELAR:
    - Intervenção do Conselho Tutelar
    - Conselheiros envolvidos
    - Encaminhamentos realizados
    
    COMUNICAÇÕES E MENSAGENS:
    - Mensagens de texto ou WhatsApp
    - Conteúdo das comunicações
    - Relatos de violência
    - Contatos telefônicos
    
    CONTEXTO FAMILIAR:
    - Estrutura familiar
    - Relacionamentos entre membros
    - Histórico de violência
    - Ambiente doméstico
    """
    
    # Criar exemplos otimizados
    metrica_exemplos = medidor.iniciar_metrica("Preparação de exemplos")
    exemplos = criar_exemplos_juridicos_processo3(medidor)
    medidor.finalizar_metrica(metrica_exemplos)
    
    try:
        # Configurações otimizadas baseadas nos testes anteriores
        metrica_langextract = medidor.iniciar_metrica("Chamada LangExtract API")
        
        resultado = lx.extract(
            text_or_documents=texto,
            prompt_description=prompt,
            examples=exemplos,
            model_id='gpt-5-nano',  # Azure OpenAI
            max_char_buffer=1600,   # Chunks ainda menores para melhor performance
            batch_length=15,        # Lotes maiores
            extraction_passes=2,    # Múltiplas passadas
            max_workers=18          # Mais paralelização
        )
        
        medidor.finalizar_metrica(metrica_langextract)
        
        # Armazenar dados da extração
        medidor.dados_processo.update({
            'total_extractions': len(resultado.extractions),
            'chunks_processados': medidor.dados_processo['tamanho_caracteres'] // 1600 + 1,
            'velocidade_chars_por_segundo': medidor.dados_processo['tamanho_caracteres'] / metrica_langextract.duracao
        })
        
        print(f"✅ Extração concluída: {len(resultado.extractions)} extrações encontradas")
        medidor.finalizar_metrica(metrica_total)
        return resultado
        
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        medidor.finalizar_metrica(metrica_langextract)
        medidor.finalizar_metrica(metrica_total)
        return None

def salvar_resultados_com_metricas_completas(resultado, medidor: MedidorPerformanceCompleto, diretorio_output: str):
    """Salva resultados e métricas de performance completas."""
    metrica = medidor.iniciar_metrica("Salvamento de resultados")
    
    # Criar diretório
    os.makedirs(diretorio_output, exist_ok=True)
    
    # Salvar dados estruturados
    arquivo_jsonl = os.path.join(diretorio_output, "extractions.jsonl")
    lx.io.save_annotated_documents([resultado], output_name="extractions.jsonl", output_dir=diretorio_output)
    print(f"✅ Dados salvos em: {arquivo_jsonl}")
    
    # Gerar visualização HTML
    try:
        metrica_viz = medidor.iniciar_metrica("Geração de visualização HTML")
        html_content = lx.visualize(arquivo_jsonl, animation_speed=1.0, show_legend=True)
        arquivo_html = os.path.join(diretorio_output, "visualizacao_processo.html")
        
        with open(arquivo_html, 'w', encoding='utf-8') as f:
            if hasattr(html_content, 'data'):
                f.write(html_content.data)
            else:
                f.write(html_content)
        
        medidor.finalizar_metrica(metrica_viz)
        print(f"✅ Visualização salva em: {arquivo_html}")
        
    except Exception as e:
        print(f"⚠️ Erro ao gerar visualização: {e}")
    
    # Salvar relatório de performance
    relatorio_performance = medidor.relatorio_performance()
    arquivo_performance = os.path.join(diretorio_output, "metricas_performance.json")
    
    with open(arquivo_performance, 'w', encoding='utf-8') as f:
        json.dump(relatorio_performance, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Métricas salvas em: {arquivo_performance}")
    
    # Salvar relatório em texto
    arquivo_relatorio = os.path.join(diretorio_output, "relatorio_extractions.txt")
    gerar_relatorio_texto_completo(resultado, relatorio_performance, arquivo_relatorio)
    print(f"✅ Relatório salvo em: {arquivo_relatorio}")
    
    medidor.finalizar_metrica(metrica)

def gerar_relatorio_texto_completo(resultado, metricas: Dict, arquivo_relatorio: str):
    """Gera relatório em texto com métricas completas."""
    
    with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE EXTRAÇÃO COM MÉTRICAS COMPLETAS - PROCESSO JURÍDICO\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Processo: {metricas['processo_numero']}\n")
        f.write(f"Total de extrações: {len(resultado.extractions)}\n\n")
        
        # Seção de métricas de performance
        f.write("MÉTRICAS DE PERFORMANCE COMPLETAS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Tempo total processamento: {metricas['tempo_total_formatado']}\n")
        f.write(f"Tempo total da tarefa: {metricas['tempo_tarefa_completa_formatado']}\n")
        f.write(f"Início tarefa: {metricas['inicio_tarefa']}\n")
        f.write(f"Início processamento: {metricas['inicio_processamento']}\n")
        f.write(f"Fim: {metricas['fim_processamento']}\n")
        f.write(f"Tamanho do arquivo: {metricas['tamanho_caracteres']:,} caracteres ({metricas['tamanho_kb']:.1f} KB)\n")
        f.write(f"Chunks processados: {metricas.get('chunks_processados', 'N/A')}\n")
        f.write(f"Velocidade: {metricas.get('velocidade_chars_por_segundo', 0):.1f} chars/segundo\n\n")
        
        # Métricas detalhadas por etapa
        f.write("TEMPO POR ETAPA\n")
        f.write("-" * 30 + "\n")
        for metrica in metricas['metricas_detalhadas']:
            f.write(f"{metrica['etapa']}: {metrica['duracao_formatada']} ({metrica['percentual_tempo_total']:.1f}%)\n")
        f.write("\n")
        
        # Agrupar extrações por classe
        extractions_por_classe = {}
        for extraction in resultado.extractions:
            classe = extraction.extraction_class
            if classe not in extractions_por_classe:
                extractions_por_classe[classe] = []
            extractions_por_classe[classe].append(extraction)
        
        # Estatísticas por categoria
        f.write("ESTATÍSTICAS POR CATEGORIA\n")
        f.write("-" * 30 + "\n")
        for classe, extractions in sorted(extractions_por_classe.items()):
            f.write(f"{classe}: {len(extractions)} extrações\n")
        f.write(f"\nTOTAL DE CATEGORIAS: {len(extractions_por_classe)}\n\n")
        
        # Escrever extrações por categoria
        for classe, extractions in sorted(extractions_por_classe.items()):
            f.write(f"\n{classe.upper()}\n")
            f.write("-" * 40 + "\n")
            
            for i, extraction in enumerate(extractions, 1):
                f.write(f"\n{i}. {extraction.extraction_text}\n")
                
                if extraction.attributes:
                    for key, value in extraction.attributes.items():
                        f.write(f"   • {key}: {value}\n")
                
                if extraction.char_interval:
                    start = extraction.char_interval.start_pos
                    end = extraction.char_interval.end_pos
                    f.write(f"   • Posição no texto: {start}-{end}\n")
                
                f.write(f"   • Status alinhamento: {extraction.alignment_status}\n")

def exibir_metricas_tempo_real_completas(medidor: MedidorPerformanceCompleto):
    """Exibe métricas completas em tempo real."""
    relatorio = medidor.relatorio_performance()
    
    print("\n" + "=" * 80)
    print("📊 MÉTRICAS DE PERFORMANCE COMPLETAS EM TEMPO REAL")
    print("=" * 80)
    
    print(f"📋 Processo: {relatorio['processo_numero']}")
    print(f"⏱️  Tempo total da tarefa: {relatorio['tempo_tarefa_completa_formatado']}")
    print(f"⏱️  Tempo processamento: {relatorio['tempo_total_formatado']}")
    print(f"📄 Arquivo: {relatorio['tamanho_caracteres']:,} caracteres ({relatorio['tamanho_kb']:.1f} KB)")
    print(f"🔍 Extrações: {relatorio.get('total_extractions', 'Processando...')}")
    print(f"⚡ Velocidade: {relatorio.get('velocidade_chars_por_segundo', 0):.1f} chars/segundo")
    
    print(f"\n📈 TEMPO POR ETAPA:")
    for metrica in relatorio['metricas_detalhadas']:
        print(f"  • {metrica['etapa']}: {metrica['duracao_formatada']} ({metrica['percentual_tempo_total']:.1f}%)")

def main():
    """Função principal com medição completa de performance."""
    
    print("TESTE LANGEXTRACT COM AZURE OPENAI - PROCESSO 3 + MÉTRICAS COMPLETAS")
    print("Processo: 07624573620258070016")
    print("=" * 80)
    
    # Inicializar medidor de performance
    medidor = MedidorPerformanceCompleto("07624573620258070016")
    
    # Verificar configuração
    metrica_config = medidor.iniciar_metrica("Verificação de configuração")
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        return False
    
    print("✅ Configuração Azure OpenAI encontrada")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    medidor.finalizar_metrica(metrica_config)
    
    # Carregar texto do processo
    texto_processo = carregar_texto_processo(medidor)
    if not texto_processo:
        return False
    
    # Extrair dados com métricas
    resultado = extrair_dados_processo3_otimizado(texto_processo, medidor)
    if not resultado:
        return False
    
    # Exibir métricas em tempo real
    exibir_metricas_tempo_real_completas(medidor)
    
    # Salvar resultados com métricas
    diretorio_output = "docs/examples/processos/07624573620258070016/output"
    salvar_resultados_com_metricas_completas(resultado, medidor, diretorio_output)
    
    # Relatório final
    tempo_total_tarefa = medidor.tempo_tarefa_completa()
    tempo_processamento = medidor.tempo_total()
    
    print("\n" + "=" * 80)
    print("🎉 TESTE PROCESSO 3 CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print(f"⏱️  Tempo total da tarefa: {str(timedelta(seconds=int(tempo_total_tarefa)))}")
    print(f"⏱️  Tempo processamento: {str(timedelta(seconds=int(tempo_processamento)))}")
    print(f"📊 Total de extrações: {len(resultado.extractions)}")
    print(f"⚡ Performance: {len(texto_processo)/tempo_processamento:.1f} chars/segundo")
    print(f"📁 Resultados salvos em: {diretorio_output}")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
