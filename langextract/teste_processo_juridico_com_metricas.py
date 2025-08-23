#!/usr/bin/env python3
"""
Teste LangExtract com Azure OpenAI - Processo 07115040420258070005
Com métricas detalhadas de tempo e performance.
"""

import os
import sys
import time
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

class MedidorPerformance:
    """Classe para medir performance detalhada."""
    
    def __init__(self):
        self.metricas: List[MetricaTempo] = []
        self.inicio_total = time.time()
        self.dados_processo = {}
    
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
    
    def relatorio_performance(self) -> Dict[str, Any]:
        """Gera relatório completo de performance."""
        tempo_total = self.tempo_total()
        
        relatorio = {
            'tempo_total_segundos': tempo_total,
            'tempo_total_formatado': str(timedelta(seconds=int(tempo_total))),
            'inicio_processamento': datetime.fromtimestamp(self.inicio_total).strftime('%H:%M:%S'),
            'fim_processamento': datetime.now().strftime('%H:%M:%S'),
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

def carregar_texto_processo(medidor: MedidorPerformance) -> str:
    """Carrega o texto do processo jurídico com medição de tempo."""
    metrica = medidor.iniciar_metrica("Carregamento do arquivo")
    
    caminho_arquivo = "docs/examples/processos/07115040420258070005/processo_07115040420258070005.md"
    
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

def criar_exemplos_juridicos_otimizados(medidor: MedidorPerformance) -> List:
    """Cria exemplos otimizados para o segundo processo."""
    metrica = medidor.iniciar_metrica("Criação de exemplos")
    
    exemplos = [
        lx.data.ExampleData(
            text="NAYANE ARAÚJO NERES DURÃES, CPF 043.726.801-20, RG 2958179, nascida em 30/01/1994, manteve relacionamento com STENIO em 2022.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="NAYANE ARAÚJO NERES DURÃES",
                    attributes={
                        "nome": "NAYANE ARAÚJO NERES DURÃES",
                        "cpf": "043.726.801-20",
                        "rg": "2958179",
                        "data_nascimento": "30/01/1994",
                        "papel": "vítima"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="STENIO",
                    attributes={
                        "nome": "STENIO",
                        "papel": "autor"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="relacionamento",
                    extraction_text="relacionamento em 2022",
                    attributes={
                        "tipo": "relacionamento amoroso",
                        "periodo": "2022",
                        "duracao": "três meses"
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="Ocorrência 8460/2025-16ª DP, Protocolo 2215813/2025, Delegado WAINER AUGUSTO MELO FILEMON.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="ocorrencia",
                    extraction_text="8460/2025-16ª DP",
                    attributes={
                        "numero": "8460/2025",
                        "delegacia": "16ª DP"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="protocolo",
                    extraction_text="2215813/2025",
                    attributes={
                        "numero": "2215813/2025"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="autoridade",
                    extraction_text="WAINER AUGUSTO MELO FILEMON",
                    attributes={
                        "nome": "WAINER AUGUSTO MELO FILEMON",
                        "cargo": "Delegado de Polícia"
                    }
                )
            ]
        )
    ]
    
    medidor.finalizar_metrica(metrica)
    return exemplos

def extrair_dados_processo_otimizado(texto: str, medidor: MedidorPerformance):
    """Extrai dados do processo com configurações otimizadas."""
    metrica_total = medidor.iniciar_metrica("Extração completa (LangExtract)")
    
    print("🔍 Iniciando extração otimizada do processo jurídico...")
    
    # Prompt otimizado para o segundo processo
    prompt = """
    Extrair informações estruturadas de processo jurídico de violência doméstica incluindo:
    
    PESSOAS ENVOLVIDAS:
    - Nome completo, CPF, RG, data de nascimento, endereço
    - Papel no processo (vítima, autor, testemunha, autoridade)
    - Dados familiares (pai, mãe, filhos, relacionamentos)
    - Profissão, estado civil, naturalidade
    
    DADOS PROCESSUAIS:
    - Número do processo, ocorrência, protocolo
    - Delegacia, vara, juizado responsável
    - Datas importantes (declarações, comunicações, decisões)
    - Tipo de procedimento (termo de declaração, medida protetiva)
    
    CRIMES E COMPORTAMENTOS:
    - Perseguição, monitoramento, controle
    - Violação de medida protetiva
    - Perturbação, intimidação
    - Uso abusivo de direito de visitação
    
    AUTORIDADES E FUNCIONÁRIOS:
    - Delegados, escrivães, promotores
    - Matrícula e função específica
    
    MEDIDAS PROTETIVAS:
    - Medidas solicitadas e deferidas
    - Distância mínima estabelecida
    - Proibições de contato e aproximação
    
    RELACIONAMENTOS E CONTEXTO:
    - Relacionamento anterior e atual
    - Guarda de criança
    - Questões familiares envolvidas
    
    COMUNICAÇÕES E MENSAGENS:
    - Mensagens de WhatsApp ou outros meios
    - Conteúdo das comunicações
    - Padrões de comportamento abusivo
    """
    
    # Criar exemplos otimizados
    metrica_exemplos = medidor.iniciar_metrica("Preparação de exemplos")
    exemplos = criar_exemplos_juridicos_otimizados(medidor)
    medidor.finalizar_metrica(metrica_exemplos)
    
    try:
        # Configurações otimizadas para o segundo processo
        metrica_langextract = medidor.iniciar_metrica("Chamada LangExtract API")
        
        resultado = lx.extract(
            text_or_documents=texto,
            prompt_description=prompt,
            examples=exemplos,
            model_id='gpt-5-nano',  # Azure OpenAI
            max_char_buffer=1800,   # Chunks otimizados
            batch_length=12,        # Lotes maiores
            extraction_passes=2,    # Múltiplas passadas
            max_workers=15          # Mais paralelização
        )
        
        medidor.finalizar_metrica(metrica_langextract)
        
        # Armazenar dados da extração
        medidor.dados_processo.update({
            'total_extractions': len(resultado.extractions),
            'chunks_processados': medidor.dados_processo['tamanho_caracteres'] // 1800 + 1,
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

def salvar_resultados_com_metricas(resultado, medidor: MedidorPerformance, diretorio_output: str):
    """Salva resultados e métricas de performance."""
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
        html_content = lx.visualize(arquivo_jsonl, animation_speed=1.2, show_legend=True)
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
    
    import json
    with open(arquivo_performance, 'w', encoding='utf-8') as f:
        json.dump(relatorio_performance, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Métricas salvas em: {arquivo_performance}")
    
    # Salvar relatório em texto
    arquivo_relatorio = os.path.join(diretorio_output, "relatorio_extractions.txt")
    gerar_relatorio_texto_com_metricas(resultado, relatorio_performance, arquivo_relatorio)
    print(f"✅ Relatório salvo em: {arquivo_relatorio}")
    
    medidor.finalizar_metrica(metrica)

def gerar_relatorio_texto_com_metricas(resultado, metricas: Dict, arquivo_relatorio: str):
    """Gera relatório em texto com métricas de performance."""
    
    with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE EXTRAÇÃO COM MÉTRICAS - PROCESSO JURÍDICO\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Processo: 07115040420258070005\n")
        f.write(f"Total de extrações: {len(resultado.extractions)}\n\n")
        
        # Seção de métricas de performance
        f.write("MÉTRICAS DE PERFORMANCE\n")
        f.write("-" * 30 + "\n")
        f.write(f"Tempo total: {metricas['tempo_total_formatado']}\n")
        f.write(f"Início: {metricas['inicio_processamento']}\n")
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
        f.write("\n")
        
        # Escrever extrações por categoria
        for classe, extractions in sorted(extractions_por_classe.items()):
            f.write(f"\n{classe.upper()}\n")
            f.write("-" * 30 + "\n")
            
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

def exibir_metricas_tempo_real(medidor: MedidorPerformance):
    """Exibe métricas em tempo real."""
    relatorio = medidor.relatorio_performance()
    
    print("\n" + "=" * 70)
    print("📊 MÉTRICAS DE PERFORMANCE EM TEMPO REAL")
    print("=" * 70)
    
    print(f"⏱️  Tempo total: {relatorio['tempo_total_formatado']}")
    print(f"📄 Arquivo: {relatorio['tamanho_caracteres']:,} caracteres ({relatorio['tamanho_kb']:.1f} KB)")
    print(f"🔍 Extrações: {relatorio.get('total_extractions', 'Processando...')}")
    print(f"⚡ Velocidade: {relatorio.get('velocidade_chars_por_segundo', 0):.1f} chars/segundo")
    
    print(f"\n📈 TEMPO POR ETAPA:")
    for metrica in relatorio['metricas_detalhadas']:
        print(f"  • {metrica['etapa']}: {metrica['duracao_formatada']} ({metrica['percentual_tempo_total']:.1f}%)")

def main():
    """Função principal com medição completa de performance."""
    
    print("TESTE LANGEXTRACT COM AZURE OPENAI + MÉTRICAS DETALHADAS")
    print("Processo: 07115040420258070005")
    print("=" * 70)
    
    # Inicializar medidor de performance
    medidor = MedidorPerformance()
    
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
    resultado = extrair_dados_processo_otimizado(texto_processo, medidor)
    if not resultado:
        return False
    
    # Exibir métricas em tempo real
    exibir_metricas_tempo_real(medidor)
    
    # Salvar resultados com métricas
    diretorio_output = "docs/examples/processos/07115040420258070005/output"
    salvar_resultados_com_metricas(resultado, medidor, diretorio_output)
    
    # Relatório final
    tempo_total = medidor.tempo_total()
    print("\n" + "=" * 70)
    print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    print(f"⏱️  Tempo total: {str(timedelta(seconds=int(tempo_total)))}")
    print(f"📊 Total de extrações: {len(resultado.extractions)}")
    print(f"⚡ Performance: {len(texto_processo)/tempo_total:.1f} chars/segundo")
    print(f"📁 Resultados salvos em: {diretorio_output}")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
