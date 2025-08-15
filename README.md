# 📄 Pré-processamento de PDF com Descrição de Imagens

Uma aplicação web completa para pré-processamento inteligente de documentos PDF, com foco em extração de conteúdo e geração automática de descrições de imagens usando IA.

## 🎯 Objetivo

Esta aplicação foi desenvolvida para facilitar o pré-processamento de documentos PDF complexos, especialmente documentos administrativos e técnicos, preparando-os para sistemas de Retrieval-Augmented Generation (GraphRAG). O sistema oferece:

- **Extração completa de conteúdo**: Texto, imagens, tabelas e metadados
- **Descrição automática de imagens**: Utilizando Azure OpenAI para gerar descrições detalhadas
- **Interface web intuitiva**: Visualização WYSIWYG dos PDFs usando PDF.js
- **Base de conhecimento**: Sistema de indexação e busca semântica
- **Exportação estruturada**: Artefatos organizados para integração com sistemas RAG

## ✨ Funcionalidades Principais

### 📤 Upload e Visualização
- Upload de arquivos PDF através de interface web
- Visualização página por página usando PDF.js integrado
- Preview em tempo real do documento

### 🔍 Extração Inteligente
- **Texto**: Extração completa do texto com preservação de estrutura
- **Imagens**: Extração e catalogação de todas as imagens do documento
- **Tabelas**: Detecção e extração de tabelas estruturadas
- **Metadados**: Informações do documento (autor, data, propriedades)

### 🤖 Descrição Automática de Imagens
- Integração com Azure OpenAI (GPT-4 Vision)
- Descrições contextualizadas em português brasileiro
- Metadados estruturados (tipo de mapa, região, legenda, escala, cores)
- Armazenamento em base de dados SQLite

### 📊 Base de Conhecimento
- Sistema de indexação semântica
- Busca por similaridade usando embeddings
- Grafo de conhecimento para relacionamentos entre documentos
- API para consultas e recuperação de informações

### 📦 Exportação e Integração
- Geração de arquivos ZIP com todos os artefatos
- Estrutura padronizada para integração com GraphRAG
- Exportação de dados em formato CSV
- APIs RESTful para integração externa

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web moderno e performático
- **PyMuPDF (fitz)**: Extração de texto, imagens e metadados
- **pdfplumber**: Extração avançada de tabelas
- **SQLite**: Base de dados para armazenamento
- **Azure OpenAI**: IA para descrição de imagens
- **Uvicorn**: Servidor ASGI de alta performance

### Frontend
- **HTML5/CSS3/JavaScript**: Interface web responsiva
- **PDF.js**: Visualização nativa de PDFs no browser
- **Módulos ES6**: Arquitetura moderna do frontend

### IA e Processamento
- **OpenAI GPT-4 Vision**: Descrição automática de imagens
- **Embeddings**: Indexação semântica para busca
- **Processamento de linguagem natural**: Análise de conteúdo

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Conta Azure OpenAI (para descrição de imagens)

### Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/JulioAnalista/preprocessamento_pdf_com_descricao_imagens.git
cd preprocessamento_pdf_com_descricao_imagens
```

2. **Instale as dependências**
```bash
pip install fastapi uvicorn python-multipart pdfplumber python-slugify openai
```

3. **Configure as variáveis de ambiente**
```bash
export AZURE_OPENAI_ENDPOINT="sua_url_azure"
export AZURE_OPENAI_API_KEY="sua_chave_api"
export AZURE_OPENAI_API_VERSION="2025-01-01-preview"
export AZURE_OPENAI_CHAT_MODEL="gpt-4.1-nano"
```

4. **Execute o servidor**
```bash
uvicorn app:app --reload --port 8099
```

5. **Acesse a aplicação**
```
http://127.0.0.1:8099/
```

## 📋 Como Usar

### 1. Upload de PDF
- Acesse a interface web
- Clique em "Escolher arquivo" e selecione um PDF
- Aguarde o upload ser concluído

### 2. Visualização e Extração
- Visualize o PDF página por página
- Clique em "Extrair" para processar o documento
- Acompanhe o progresso da extração

### 3. Análise dos Resultados
- **Aba Texto**: Visualize o texto extraído
- **Aba Imagens**: Veja as imagens com descrições automáticas
- **Aba Tabelas**: Examine as tabelas estruturadas
- **Aba Metadados**: Informações do documento

### 4. Download dos Artefatos
- Clique em "Baixar artefatos (.zip)"
- Obtenha todos os dados processados organizados

## 📁 Estrutura do Projeto

```
pdf_preproc/
├── app.py                 # Servidor principal FastAPI
├── db.py                  # Gerenciamento da base de dados
├── image_caption.py       # Descrição automática de imagens
├── graph_kb.py           # Base de conhecimento e grafo
├── indexers.py           # Indexação e busca semântica
├── export_images_csv.py  # Exportação de dados
├── utils/
│   └── pdf_extractor.py  # Extração de conteúdo PDF
├── static/               # Interface web
│   ├── index.html
│   ├── main.js
│   ├── styles.css
│   └── pdfjs/           # PDF.js integrado
├── docs/                # Documentação detalhada
├── tests/               # Testes automatizados
├── tools/               # Ferramentas auxiliares
├── uploads/             # PDFs enviados
├── extracted/           # Conteúdo extraído
└── public/              # Arquivos públicos (ZIPs)
```

## 🔧 APIs Disponíveis

### Upload e Processamento
- `POST /api/upload` - Upload de PDF
- `GET /api/pdf/{file_id}` - Servir PDF
- `POST /api/extract/{file_id}` - Extrair conteúdo
- `GET /api/image/{file_id}/{image_name}` - Servir imagens

### Base de Conhecimento
- `POST /api/kb/index` - Indexar documento
- `GET /api/kb/search` - Busca semântica
- `GET /api/kb/graph` - Visualizar grafo

### Descrição de Imagens
- `POST /api/images/describe` - Descrever imagens
- `GET /api/images/descriptions` - Listar descrições

## 🧪 Testes

Execute os testes automatizados:

```bash
# Testes unitários
python -m pytest tests/

# Testes de integração
python tests/test_api_integration.py

# Relatórios de teste
python tests/run_final_report.py
```

## 📊 Casos de Uso Testados

- **Documentos administrativos**: Anteprojetos, minutas, relatórios
- **Documentos técnicos**: Manuais, especificações, plantas
- **Documentos com mapas**: Plantas urbanas, zoneamentos, cartografia
- **Documentos tabulares**: Relatórios financeiros, planilhas complexas

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Julio Silveira**
- Email: julio.silveira@gmail.com
- GitHub: [@JulioAnalista](https://github.com/JulioAnalista)

## 🙏 Agradecimentos

- Comunidade FastAPI pela excelente documentação
- Equipe do PDF.js pelo viewer integrado
- Azure OpenAI pelos modelos de IA avançados
- Comunidade Python pelas bibliotecas de processamento de PDF

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no repositório!

