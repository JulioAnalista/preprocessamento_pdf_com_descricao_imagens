#!/usr/bin/env python3
"""
Teste completo do LangExtract com Azure OpenAI em processo jurídico.
Extrai informações estruturadas do processo 07059645120258070012.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar LangExtract
import langextract as lx

def carregar_texto_processo():
    """Carrega o texto do processo jurídico."""
    caminho_arquivo = "docs/examples/processos/07059645120258070012/processo_07059645120258070012.md"
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            texto = f.read()
        print(f"✅ Arquivo carregado: {len(texto)} caracteres")
        return texto
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return None

def criar_exemplos_juridicos():
    """Cria exemplos para guiar a extração de dados jurídicos."""
    
    exemplos = [
        lx.data.ExampleData(
            text="João Silva, CPF 123.456.789-00, nascido em 01/01/1980, residente na Rua A, 123, foi vítima de ameaça praticada por Maria Santos em 15/03/2023.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="João Silva",
                    attributes={
                        "nome": "João Silva",
                        "cpf": "123.456.789-00",
                        "data_nascimento": "01/01/1980",
                        "endereco": "Rua A, 123",
                        "papel": "vítima"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="pessoa",
                    extraction_text="Maria Santos",
                    attributes={
                        "nome": "Maria Santos",
                        "papel": "autora"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="crime",
                    extraction_text="ameaça",
                    attributes={
                        "tipo": "ameaça",
                        "data": "15/03/2023"
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="Processo nº 1234567-89.2023.8.07.0001 da 1ª Vara Criminal de Brasília. Delegacia: 5ª DP. Inquérito 456/2023.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="processo",
                    extraction_text="1234567-89.2023.8.07.0001",
                    attributes={
                        "numero": "1234567-89.2023.8.07.0001",
                        "vara": "1ª Vara Criminal de Brasília"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="procedimento",
                    extraction_text="Inquérito 456/2023",
                    attributes={
                        "tipo": "Inquérito",
                        "numero": "456/2023",
                        "delegacia": "5ª DP"
                    }
                )
            ]
        )
    ]
    
    return exemplos

def extrair_dados_processo(texto):
    """Extrai dados estruturados do processo jurídico."""
    
    print("🔍 Iniciando extração de dados do processo jurídico...")
    
    # Prompt detalhado para extração jurídica
    prompt = """
    Extrair informações estruturadas de processo jurídico incluindo:
    
    PESSOAS ENVOLVIDAS:
    - Nome completo, CPF, RG, data de nascimento, endereço
    - Papel no processo (vítima, autor, testemunha, autoridade)
    - Dados familiares (pai, mãe, filhos)
    
    DADOS PROCESSUAIS:
    - Número do processo, ocorrência, protocolo
    - Delegacia, vara, juizado responsável
    - Datas importantes (fatos, comunicação, decisões)
    - Tipo de procedimento (inquérito, medida protetiva, etc.)
    
    CRIMES E INFRAÇÕES:
    - Tipos de crime (ameaça, injúria, difamação, etc.)
    - Lei aplicável (Lei Maria da Penha, Código Penal)
    - Circunstâncias e local dos fatos
    
    AUTORIDADES:
    - Delegados, escrivães, promotores, juízes
    - Matrícula e função
    
    MEDIDAS E DECISÕES:
    - Medidas protetivas solicitadas e deferidas
    - Despachos e decisões judiciais
    - Encaminhamentos (Conselho Tutelar, MP, etc.)
    
    MENORES ENVOLVIDOS:
    - Nomes, idades, situação de risco
    - Medidas de proteção específicas
    """
    
    # Exemplos para guiar o modelo
    exemplos = criar_exemplos_juridicos()
    
    try:
        # Executar extração com Azure OpenAI
        resultado = lx.extract(
            text_or_documents=texto,
            prompt_description=prompt,
            examples=exemplos,
            model_id='gpt-5-nano',  # Usa Azure OpenAI automaticamente
            max_char_buffer=2000,   # Chunks maiores para contexto jurídico
            batch_length=10,        # Processamento em lotes
            extraction_passes=2     # Múltiplas passadas para melhor recall
            # Nota: gpt-5-nano só suporta temperature padrão (1.0)
        )
        
        print(f"✅ Extração concluída: {len(resultado.extractions)} extrações encontradas")
        return resultado
        
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        return None

def salvar_resultados(resultado, diretorio_output):
    """Salva os resultados da extração."""
    
    # Criar diretório se não existir
    os.makedirs(diretorio_output, exist_ok=True)
    
    # Salvar dados estruturados
    arquivo_jsonl = os.path.join(diretorio_output, "extractions.jsonl")
    lx.io.save_annotated_documents([resultado], output_name="extractions.jsonl", output_dir=diretorio_output)
    print(f"✅ Dados salvos em: {arquivo_jsonl}")
    
    # Gerar visualização HTML
    try:
        html_content = lx.visualize(arquivo_jsonl, animation_speed=1.5, show_legend=True)
        arquivo_html = os.path.join(diretorio_output, "visualizacao_processo.html")
        
        with open(arquivo_html, 'w', encoding='utf-8') as f:
            if hasattr(html_content, 'data'):
                f.write(html_content.data)
            else:
                f.write(html_content)
        
        print(f"✅ Visualização salva em: {arquivo_html}")
        
    except Exception as e:
        print(f"⚠️ Erro ao gerar visualização: {e}")
    
    # Salvar relatório em texto
    arquivo_relatorio = os.path.join(diretorio_output, "relatorio_extractions.txt")
    gerar_relatorio_texto(resultado, arquivo_relatorio)
    print(f"✅ Relatório salvo em: {arquivo_relatorio}")

def gerar_relatorio_texto(resultado, arquivo_relatorio):
    """Gera relatório em texto das extrações."""
    
    with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE EXTRAÇÃO - PROCESSO JURÍDICO\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Processo: 07059645120258070012\n")
        f.write(f"Total de extrações: {len(resultado.extractions)}\n\n")
        
        # Agrupar extrações por classe
        extractions_por_classe = {}
        for extraction in resultado.extractions:
            classe = extraction.extraction_class
            if classe not in extractions_por_classe:
                extractions_por_classe[classe] = []
            extractions_por_classe[classe].append(extraction)
        
        # Escrever por categoria
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

def exibir_resumo_extractions(resultado):
    """Exibe resumo das extrações na tela."""
    
    print("\n" + "=" * 60)
    print("RESUMO DAS EXTRAÇÕES")
    print("=" * 60)
    
    # Contar por classe
    classes_count = {}
    for extraction in resultado.extractions:
        classe = extraction.extraction_class
        classes_count[classe] = classes_count.get(classe, 0) + 1
    
    print(f"\nTotal de extrações: {len(resultado.extractions)}")
    print("\nPor categoria:")
    for classe, count in sorted(classes_count.items()):
        print(f"  • {classe}: {count}")
    
    print("\n" + "-" * 60)
    print("PRIMEIRAS 10 EXTRAÇÕES:")
    print("-" * 60)
    
    for i, extraction in enumerate(resultado.extractions[:10], 1):
        print(f"\n{i}. [{extraction.extraction_class.upper()}] {extraction.extraction_text}")
        
        if extraction.attributes:
            # Mostrar apenas os 3 primeiros atributos para não poluir
            attrs_mostrar = list(extraction.attributes.items())[:3]
            for key, value in attrs_mostrar:
                print(f"   → {key}: {value}")
            if len(extraction.attributes) > 3:
                print(f"   → ... e mais {len(extraction.attributes) - 3} atributos")

def main():
    """Função principal."""
    
    print("TESTE LANGEXTRACT COM AZURE OPENAI - PROCESSO JURÍDICO")
    print("=" * 60)
    
    # Verificar configuração
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("Configure no arquivo .env ou como variáveis de ambiente.")
        return False
    
    print("✅ Configuração Azure OpenAI encontrada")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    
    # Carregar texto do processo
    texto_processo = carregar_texto_processo()
    if not texto_processo:
        return False
    
    # Extrair dados
    resultado = extrair_dados_processo(texto_processo)
    if not resultado:
        return False
    
    # Exibir resumo
    exibir_resumo_extractions(resultado)
    
    # Salvar resultados
    diretorio_output = "docs/examples/processos/07059645120258070012/output"
    salvar_resultados(resultado, diretorio_output)
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print(f"📁 Resultados salvos em: {diretorio_output}")
    print("📊 Arquivos gerados:")
    print("   • extractions.jsonl - Dados estruturados")
    print("   • visualizacao_processo.html - Visualização interativa")
    print("   • relatorio_extractions.txt - Relatório em texto")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
