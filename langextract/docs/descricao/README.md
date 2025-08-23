# Documentação LangExtract - Português

Esta pasta contém documentação detalhada sobre o LangExtract em português, incluindo a implementação do provider Azure OpenAI.

## 📋 Índice da Documentação

### 📖 Documentos Principais

1. **[Relatório Técnico Detalhado](langextract_relatorio_detalhado.md)**
   - Visão geral completa do LangExtract
   - Arquitetura e componentes principais
   - Sistema de providers e descoberta
   - Estruturas de dados e fluxo de processamento
   - Funcionalidades avançadas
   - Sistema de visualização e I/O
   - Implementação Azure OpenAI

2. **[Exemplos Práticos Azure OpenAI](exemplos_praticos_azure_openai.md)**
   - Configuração inicial e setup
   - Exemplos de extração de entidades de notícias
   - Processamento em lote
   - Extração médica (demonstração)
   - Configurações avançadas
   - Dicas de otimização e troubleshooting

## 🎯 O que é o LangExtract?

O **LangExtract** é uma biblioteca Python desenvolvida pelo Google que utiliza Modelos de Linguagem de Grande Escala (LLMs) para extrair informações estruturadas de textos não estruturados.

### ✨ Principais Características

- **🎯 Mapeamento Preciso**: Cada extração é mapeada para sua localização exata no texto fonte
- **📊 Saídas Estruturadas**: Garante esquemas consistentes baseados em exemplos
- **📄 Documentos Longos**: Processa documentos extensos através de chunking inteligente
- **🎨 Visualização Interativa**: Gera HTML interativo para revisão das extrações
- **🔌 Multi-Provider**: Suporte a Gemini, OpenAI, Azure OpenAI, Ollama
- **🌐 Adaptável**: Funciona em qualquer domínio usando apenas alguns exemplos

## 🚀 Implementação Azure OpenAI

### 🆕 Novidades Implementadas

A implementação do provider Azure OpenAI adiciona:

- ✅ **Autenticação Azure**: Suporte completo a endpoints e chaves Azure
- ✅ **Modelos GPT-5**: Suporte aos modelos gpt-5-nano e gpt-5-mini
- ✅ **Configuração Flexível**: Via variáveis de ambiente ou código
- ✅ **Processamento Paralelo**: Otimizado para múltiplas chamadas
- ✅ **Padrões Inteligentes**: Reconhecimento automático de modelos Azure

### 🔧 Configuração Rápida

```bash
# 1. Instalar
pip install langextract python-dotenv

# 2. Configurar .env
echo "AZURE_OPENAI_API_KEY=sua-chave" >> .env
echo "AZURE_OPENAI_ENDPOINT=https://seu-endpoint.openai.azure.com/" >> .env

# 3. Usar
python -c "
import langextract as lx
from dotenv import load_dotenv
load_dotenv()

result = lx.extract(
    text_or_documents='Microsoft anunciou parceria com OpenAI.',
    prompt_description='Extrair empresas do texto.',
    examples=[],
    model_id='gpt-5-nano'
)
print(f'Extrações: {len(result.extractions)}')
"
```

## 📊 Casos de Uso

### 🏥 Área Médica
- Extração de medicamentos, dosagens e instruções
- Análise de relatórios radiológicos
- Processamento de notas clínicas

### ⚖️ Área Legal
- Análise de contratos e cláusulas
- Extração de precedentes jurídicos
- Compliance e regulamentações

### 📰 Análise de Notícias
- Identificação de pessoas, organizações e locais
- Extração de eventos e fatos
- Análise de sentimentos

### 🔬 Pesquisa Acadêmica
- Processamento de literatura científica
- Extração de citações e referências
- Análise de dados e estatísticas

## 🛠️ Arquitetura Técnica

### 🏗️ Componentes Principais

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

### 🔄 Fluxo de Processamento

1. **Tokenização** → Divisão do texto em tokens
2. **Chunking** → Quebra em pedaços processáveis
3. **Prompting** → Geração de prompts para LLM
4. **Inferência** → Processamento paralelo via LLM
5. **Resolução** → Parsing das respostas
6. **Alinhamento** → Mapeamento para texto original
7. **Visualização** → Geração de HTML interativo

### 🎛️ Sistema de Providers

| Provider | Padrões | Prioridade | Características |
|----------|---------|------------|-----------------|
| **Azure OpenAI** | `^gpt-5-nano`, `^azure-gpt` | 15 | Modelos Azure, alta prioridade |
| **OpenAI** | `^gpt-4`, `^gpt-5` | 10 | Modelos OpenAI padrão |
| **Gemini** | `^gemini` | 10 | Modelos Google, schema constraints |
| **Ollama** | `^llama`, `^gemma` | 10 | Modelos locais, sem API key |

## 📈 Performance e Otimização

### ⚡ Processamento Paralelo
- **Batch Processing**: Múltiplos chunks processados simultaneamente
- **Thread Pool**: Até 20 workers paralelos configuráveis
- **Rate Limiting**: Respeita limites das APIs

### 🎯 Qualidade de Extração
- **Múltiplas Passadas**: Até 3 passadas para melhor recall
- **Schema Constraints**: Saídas estruturadas garantidas
- **Alinhamento Fuzzy**: Correspondência aproximada quando necessário

### 📊 Métricas Típicas
- **Velocidade**: 15-50 caracteres/segundo (dependendo do modelo)
- **Precisão**: 85-95% (dependendo da qualidade dos exemplos)
- **Recall**: 80-90% (melhorado com múltiplas passadas)

## 🔍 Visualização Interativa

### 🎨 Características da Visualização
- **Animação**: Navegação sequencial pelas extrações
- **Cores**: Mapeamento automático por tipo de entidade
- **Tooltips**: Informações detalhadas ao passar o mouse
- **Controles**: Play/pause, navegação manual
- **Responsiva**: Adaptável a diferentes tamanhos de tela

### 📱 Formatos Suportados
- **HTML Interativo**: Para navegadores web
- **Jupyter Notebooks**: Integração nativa
- **GIF Otimizado**: Para documentação e apresentações

## 📚 Recursos Adicionais

### 🔗 Links Úteis
- **Repositório GitHub**: https://github.com/google/langextract
- **Documentação Oficial**: README.md principal
- **Exemplos Ollama**: `examples/ollama/`
- **Notebooks Jupyter**: `examples/notebooks/`

### 📖 Documentação Relacionada
- **CONTRIBUTING.md**: Guia para contribuições
- **Provider System**: `langextract/providers/README.md`
- **Medication Examples**: `docs/examples/medication_examples.md`

### 🎓 Pesquisa Acadêmica
O LangExtract é baseado em pesquisa publicada:
- **Paper**: "LLMs Accelerate Annotation for Medical Information Extraction"
- **Conferência**: Machine Learning for Health (ML4H), PMLR, 2023
- **arXiv**: https://arxiv.org/abs/2312.02296

## ⚠️ Avisos Importantes

### 🏥 Uso Médico
- Exemplos médicos são apenas para demonstração
- Não usar para diagnósticos ou conselhos médicos reais
- Sujeito aos termos de uso de IA para saúde

### 📄 Licença e Suporte
- **Licença**: Apache 2.0
- **Suporte**: Não é produto oficialmente suportado pelo Google
- **Contribuições**: Bem-vindas via GitHub

---

**Última Atualização**: Agosto 2025  
**Versão LangExtract**: 1.0.8  
**Provider Azure OpenAI**: Implementado e testado ✅
