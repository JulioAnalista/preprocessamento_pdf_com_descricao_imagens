# LangExtract: Relatório Técnico Detalhado

## Sumário Executivo

O **LangExtract** é uma biblioteca Python desenvolvida pelo Google que utiliza Modelos de Linguagem de Grande Escala (LLMs) para extrair informações estruturadas de textos não estruturados. A biblioteca se destaca por sua capacidade de mapear precisamente as extrações ao texto fonte, garantir saídas estruturadas consistentes e processar documentos longos de forma otimizada.

## 1. Visão Geral e Objetivos

### 1.1 Propósito Principal
O LangExtract foi projetado para resolver o desafio de extrair informações estruturadas de documentos de texto não estruturados, como:
- Relatórios clínicos e notas médicas
- Documentos legais e contratos
- Artigos de notícias e literatura
- Relatórios técnicos e científicos
- Qualquer texto que contenha informações valiosas em formato não estruturado

### 1.2 Objetivos Principais
1. **Mapeamento Preciso**: Cada extração é mapeada para sua localização exata no texto fonte
2. **Saídas Estruturadas Confiáveis**: Garante esquemas de saída consistentes baseados em exemplos
3. **Processamento de Documentos Longos**: Supera limitações de contexto através de chunking inteligente
4. **Visualização Interativa**: Gera visualizações HTML para revisão e validação
5. **Flexibilidade de LLMs**: Suporta múltiplos provedores de modelos de linguagem
6. **Adaptabilidade**: Funciona em qualquer domínio usando apenas alguns exemplos

## 2. Arquitetura e Componentes Principais

### 2.1 Arquitetura Geral
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Entrada       │    │   Processamento  │    │     Saída       │
│   (Texto)       │───▶│   (LangExtract)  │───▶│  (Estruturada)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Visualização   │
                    │   (HTML Inter.)  │
                    └──────────────────┘
```

### 2.2 Componentes Core

#### 2.2.1 Sistema de Extração (`extraction.py`)
- **Função Principal**: `extract()` - API principal para extração
- **Parâmetros Principais**:
  - `text_or_documents`: Texto ou documentos para processar
  - `prompt_description`: Instruções de extração
  - `examples`: Exemplos para guiar o modelo
  - `model_id`: Identificador do modelo LLM
  - `max_char_buffer`: Tamanho máximo de chunk (padrão: 1000)
  - `extraction_passes`: Número de passadas para melhorar recall
  - `batch_length`: Tamanho do lote para processamento paralelo

#### 2.2.2 Sistema de Anotação (`annotation.py`)
- **Classe Principal**: `Annotator`
- **Responsabilidades**:
  - Tokenização do texto de entrada
  - Geração de prompts para o modelo de linguagem
  - Processamento em lotes para otimização
  - Resolução das saídas do modelo em anotações estruturadas
  - Suporte a múltiplas passadas de extração

#### 2.2.3 Sistema de Chunking (`chunking.py`)
- **Classe Principal**: `DocumentChunker`
- **Funcionalidades**:
  - Divisão inteligente de documentos longos
  - Preservação de contexto semântico
  - Quebra preferencial em limites de sentença
  - Suporte a diferentes tamanhos de buffer

#### 2.2.4 Sistema de Resolução (`resolver.py`)
- **Classe Principal**: `Resolver`
- **Capacidades**:
  - Parsing de saídas JSON/YAML do modelo
  - Alinhamento de extrações com texto fonte
  - Suporte a alinhamento fuzzy quando necessário
  - Ordenação e estruturação de extrações

### 2.3 Sistema de Providers

#### 2.3.1 Arquitetura de Providers
O LangExtract utiliza um sistema de providers baseado em padrões para suportar diferentes LLMs:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Model ID      │    │     Router       │    │    Provider     │
│ "gemini-2.5"    │───▶│   (Patterns)     │───▶│   Instance      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### 2.3.2 Providers Disponíveis
1. **Gemini** (`gemini.py`): Modelos Google Gemini
   - Padrões: `^gemini`
   - Prioridade: 10
   - Suporte nativo a schema constraints

2. **OpenAI** (`openai.py`): Modelos GPT da OpenAI
   - Padrões: `^gpt-4`, `^gpt-5`
   - Prioridade: 10
   - Requer instalação opcional: `pip install langextract[openai]`

3. **Azure OpenAI** (`azure_openai.py`): Modelos Azure OpenAI
   - Padrões: `^azure-gpt`, `^gpt-5-nano`, `^gpt-5-mini`, `^azure:`
   - Prioridade: 15 (maior que OpenAI regular)
   - Suporte a endpoints Azure personalizados

4. **Ollama** (`ollama.py`): Modelos locais via Ollama
   - Padrões: `^gemma`, `^llama`, `^mistral`, etc.
   - Prioridade: 10
   - Execução local sem necessidade de API keys

#### 2.3.3 Sistema de Descoberta
- **Entry Points**: Descoberta automática via `pyproject.toml`
- **Lazy Loading**: Providers carregados apenas quando necessários
- **Plugin System**: Suporte a providers de terceiros
- **Priority-based Resolution**: Resolução baseada em prioridades

## 3. Estruturas de Dados Principais

### 3.1 Classe `Extraction`
```python
@dataclasses.dataclass
class Extraction:
    extraction_class: str              # Tipo da extração
    extraction_text: str               # Texto extraído
    char_interval: CharInterval | None # Posição no texto
    alignment_status: AlignmentStatus  # Status do alinhamento
    extraction_index: int | None       # Índice da extração
    group_index: int | None           # Índice do grupo
    description: str | None           # Descrição opcional
    attributes: dict | None           # Atributos adicionais
```

### 3.2 Classe `Document`
```python
@dataclasses.dataclass
class Document:
    text: str                         # Texto do documento
    document_id: str                  # ID único (auto-gerado)
    additional_context: str | None    # Contexto adicional
    tokenized_text: TokenizedText     # Texto tokenizado
```

### 3.3 Classe `AnnotatedDocument`
```python
@dataclasses.dataclass
class AnnotatedDocument:
    extractions: list[Extraction]     # Lista de extrações
    text: str | None                  # Texto original
    document_id: str                  # ID do documento
    tokenized_text: TokenizedText     # Texto tokenizado
```

## 4. Fluxo de Processamento Detalhado

### 4.1 Pipeline de Extração
```
1. Entrada de Texto
   ↓
2. Tokenização
   ↓
3. Chunking (se necessário)
   ↓
4. Geração de Prompts
   ↓
5. Inferência LLM (paralela)
   ↓
6. Resolução de Saídas
   ↓
7. Alinhamento com Texto
   ↓
8. Agregação de Resultados
   ↓
9. Saída Estruturada
```

### 4.2 Processamento de Chunks
1. **Divisão Inteligente**: Quebra em limites de sentença quando possível
2. **Preservação de Contexto**: Mantém contexto semântico entre chunks
3. **Processamento Paralelo**: Múltiplos chunks processados simultaneamente
4. **Agregação**: Resultados combinados e deduplicados

### 4.3 Sistema de Alinhamento
1. **Alinhamento Exato**: Correspondência perfeita de tokens
2. **Alinhamento Parcial**: Correspondência parcial quando texto é maior
3. **Alinhamento Fuzzy**: Correspondência aproximada com threshold
4. **Status de Alinhamento**: Rastreamento da qualidade do alinhamento

## 5. Funcionalidades Avançadas

### 5.1 Múltiplas Passadas de Extração
- **Objetivo**: Melhorar recall através de reprocessamento
- **Implementação**: Parâmetro `extraction_passes`
- **Benefício**: Encontra entidades que podem ter sido perdidas na primeira passada
- **Custo**: Aumenta uso de tokens e tempo de processamento

### 5.2 Processamento Paralelo
- **Parâmetro**: `max_workers` (padrão: 10)
- **Implementação**: `ThreadPoolExecutor` para chamadas de API
- **Benefício**: Reduz tempo total de processamento
- **Limitação**: Limitado por rate limits da API

### 5.3 Schema Constraints
- **Suporte**: Modelos compatíveis (Gemini)
- **Funcionalidade**: Força saída estruturada baseada em exemplos
- **Benefício**: Maior consistência e confiabilidade
- **Parâmetro**: `use_schema_constraints=True`

## 6. Sistema de Visualização

### 6.1 Capacidades de Visualização
- **HTML Interativo**: Visualização animada das extrações
- **Mapeamento Visual**: Destaque das extrações no texto original
- **Navegação**: Controles para navegar entre extrações
- **Tooltips**: Informações detalhadas sobre cada extração
- **Legenda**: Mapeamento de cores para tipos de extração

### 6.2 Funcionalidades da Visualização
```python
html_content = lx.visualize(
    data_source="results.jsonl",
    animation_speed=1.0,           # Velocidade da animação
    show_legend=True,              # Mostrar legenda
    gif_optimized=True             # Otimizado para GIFs
)
```

### 6.3 Componentes da Visualização
- **CSS Styling**: Estilos responsivos e interativos
- **JavaScript**: Controles de animação e navegação
- **Color Mapping**: Atribuição automática de cores
- **Context Display**: Exibição de contexto ao redor das extrações

## 7. Sistema de I/O

### 7.1 Formatos Suportados
- **Entrada**: Texto simples, URLs, CSV, Documentos
- **Saída**: JSONL (JSON Lines), estruturas Python
- **Visualização**: HTML interativo

### 7.2 Funcionalidades de I/O
```python
# Salvar resultados
lx.io.save_annotated_documents(
    annotated_documents=[result],
    output_name="results.jsonl",
    output_dir="./output"
)

# Carregar resultados
documents = lx.io.load_annotated_documents_jsonl("results.jsonl")
```

## 8. Casos de Uso e Aplicações

### 8.1 Área Médica
- **Extração de Medicamentos**: Nomes, dosagens, frequências
- **Relatórios Radiológicos**: Achados, diagnósticos
- **Notas Clínicas**: Sintomas, tratamentos, resultados

### 8.2 Área Legal
- **Contratos**: Cláusulas, datas, partes envolvidas
- **Documentos Jurídicos**: Precedentes, citações
- **Compliance**: Regulamentações, requisitos

### 8.3 Análise de Notícias
- **Entidades**: Pessoas, organizações, locais
- **Eventos**: Datas, fatos, relacionamentos
- **Sentimentos**: Análise de tom e contexto

### 8.4 Pesquisa Acadêmica
- **Literatura Científica**: Métodos, resultados, conclusões
- **Citações**: Referências, autores
- **Dados**: Estatísticas, métricas

## 9. Vantagens e Limitações

### 9.1 Vantagens
1. **Precisão de Mapeamento**: Localização exata das extrações
2. **Flexibilidade**: Adaptável a qualquer domínio
3. **Escalabilidade**: Processa documentos longos eficientemente
4. **Visualização**: Interface intuitiva para revisão
5. **Multi-provider**: Suporte a diferentes LLMs
6. **Open Source**: Código aberto com licença Apache 2.0

### 9.2 Limitações
1. **Dependência de LLMs**: Qualidade depende do modelo usado
2. **Custos de API**: Uso intensivo pode ser custoso
3. **Latência**: Processamento pode ser lento para documentos grandes
4. **Qualidade dos Exemplos**: Resultados dependem da qualidade dos exemplos fornecidos
5. **Rate Limits**: Limitado por restrições das APIs dos provedores

## 10. Configuração e Uso

### 10.1 Instalação
```bash
# Instalação básica
pip install langextract

# Com suporte OpenAI
pip install langextract[openai]

# Instalação completa
pip install langextract[all]
```

### 10.2 Configuração de API Keys
```bash
# Variável de ambiente
export LANGEXTRACT_API_KEY="sua-chave-aqui"

# Arquivo .env
echo "LANGEXTRACT_API_KEY=sua-chave-aqui" >> .env

# Azure OpenAI
export AZURE_OPENAI_API_KEY="sua-chave-azure"
export AZURE_OPENAI_ENDPOINT="https://seu-endpoint.openai.azure.com/"
```

### 10.3 Exemplo Básico de Uso
```python
import langextract as lx

# Definir prompt e exemplos
prompt = "Extrair pessoas, organizações e locais do texto."
examples = [
    lx.data.ExampleData(
        text="João Silva trabalha na Microsoft em São Paulo.",
        extractions=[
            lx.data.Extraction("pessoa", "João Silva"),
            lx.data.Extraction("organização", "Microsoft"),
            lx.data.Extraction("local", "São Paulo")
        ]
    )
]

# Executar extração
result = lx.extract(
    text_or_documents="Maria Costa é CEO da Google no Rio de Janeiro.",
    prompt_description=prompt,
    examples=examples,
    model_id="gpt-5-nano"  # Usa Azure OpenAI automaticamente
)

# Visualizar resultados
html_content = lx.visualize(result)
```

## 11. Conclusão

O LangExtract representa uma solução robusta e flexível para extração de informações estruturadas de textos não estruturados. Sua arquitetura modular, suporte a múltiplos provedores de LLM, e capacidades avançadas de visualização o tornam uma ferramenta valiosa para pesquisadores, desenvolvedores e organizações que precisam processar grandes volumes de texto de forma eficiente e precisa.

A implementação do provider Azure OpenAI adiciona mais uma opção poderosa ao ecossistema, permitindo que usuários aproveitem os modelos mais recentes da Microsoft/OpenAI através da infraestrutura Azure, com benefícios de segurança, compliance e integração empresarial.

## 12. Implementação Azure OpenAI

### 12.1 Características Específicas
A implementação do provider Azure OpenAI no LangExtract inclui:

#### 12.1.1 Funcionalidades Implementadas
- **Autenticação Azure**: Suporte completo a chaves de API e endpoints Azure
- **Modelos Suportados**: gpt-5-nano, gpt-5-mini, e padrões azure-*
- **Configuração Flexível**: Suporte a variáveis de ambiente e configuração manual
- **Processamento Paralelo**: Otimizado para múltiplas chamadas simultâneas
- **Tratamento de Erros**: Mensagens específicas para erros Azure

#### 12.1.2 Configuração Azure OpenAI
```python
# Via variáveis de ambiente (.env)
AZURE_OPENAI_API_KEY=sua-chave-azure
AZURE_OPENAI_ENDPOINT=https://seu-endpoint.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-03-01-preview

# Via código Python
from langextract.providers.azure_openai import AzureOpenAILanguageModel

model = AzureOpenAILanguageModel(
    model_id='gpt-5-nano',
    deployment_name='gpt-5-nano-sf',
    api_key='sua-chave',
    azure_endpoint='https://seu-endpoint.openai.azure.com/',
    api_version='2025-03-01-preview'
)
```

#### 12.1.3 Padrões de Modelo Suportados
- `gpt-5-nano`: Modelo nano da série GPT-5
- `gpt-5-mini`: Modelo mini da série GPT-5
- `azure-gpt-*`: Qualquer modelo com prefixo azure-gpt
- `azure:*`: Qualquer modelo com prefixo azure:

#### 12.1.4 Exemplo de Uso Completo
```python
import langextract as lx
from dotenv import load_dotenv

# Carregar configurações do .env
load_dotenv()

# Extração usando Azure OpenAI
result = lx.extract(
    text_or_documents="Microsoft anunciou parceria com OpenAI em Redmond.",
    prompt_description="Extrair empresas, locais e eventos do texto.",
    examples=[
        lx.data.ExampleData(
            text="Google lançou produto em Mountain View.",
            extractions=[
                lx.data.Extraction("empresa", "Google"),
                lx.data.Extraction("local", "Mountain View"),
                lx.data.Extraction("evento", "lançou produto")
            ]
        )
    ],
    model_id="gpt-5-nano"  # Automaticamente usa Azure OpenAI
)

# Resultados
for extraction in result.extractions:
    print(f"{extraction.extraction_class}: {extraction.extraction_text}")
```

### 12.2 Vantagens do Azure OpenAI
1. **Segurança Empresarial**: Compliance com padrões corporativos
2. **Integração Azure**: Fácil integração com outros serviços Azure
3. **Controle de Custos**: Melhor controle e previsibilidade de custos
4. **Suporte Técnico**: Suporte empresarial da Microsoft
5. **Disponibilidade Regional**: Deployments em diferentes regiões

---

**Versão**: 1.0.8
**Licença**: Apache 2.0
**Desenvolvedor**: Google LLC
**Documentação**: https://github.com/google/langextract
**Data do Relatório**: Agosto 2025
