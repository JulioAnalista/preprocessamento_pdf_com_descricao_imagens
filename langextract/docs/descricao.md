# LangExtract - Descrição Detalhada do Projeto

## Visão Geral

O **LangExtract** é uma biblioteca Python desenvolvida pelo Google que utiliza Modelos de Linguagem de Grande Escala (LLMs) para extrair informações estruturadas de documentos de texto não estruturados. A biblioteca foi projetada para transformar textos complexos em dados organizados e estruturados, baseando-se em instruções definidas pelo usuário e exemplos de orientação.

## Objetivo Principal

O LangExtract resolve um problema fundamental na análise de texto: **como extrair informações específicas e estruturadas de grandes volumes de texto não estruturado de forma precisa e escalável**. A biblioteca é especialmente útil para:

- **Análise de documentos médicos**: Extração de medicamentos, dosagens, diagnósticos
- **Processamento de literatura**: Identificação de personagens, emoções, relacionamentos
- **Análise de relatórios**: Estruturação de informações técnicas e científicas
- **Processamento de documentos legais**: Extração de cláusulas, termos, entidades
- **Análise de conteúdo**: Organização de informações de qualquer domínio

## Principais Funcionalidades

### 1. **Extração Baseada em Exemplos (Few-Shot Learning)**
- Define tarefas de extração usando apenas alguns exemplos de alta qualidade
- Não requer treinamento ou fine-tuning de modelos
- Adapta-se a qualquer domínio através de exemplos específicos

### 2. **Mapeamento Preciso de Origem (Source Grounding)**
- Mapeia cada extração para sua localização exata no texto original
- Permite rastreabilidade completa e verificação visual
- Facilita a validação e auditoria dos resultados

### 3. **Processamento de Documentos Longos**
- Supera limitações de contexto através de estratégias otimizadas de chunking
- Processamento paralelo para melhor performance
- Múltiplas passadas de extração para maior recall

### 4. **Visualização Interativa**
- Gera visualizações HTML interativas e auto-contidas
- Permite exploração visual de milhares de entidades extraídas
- Destaque colorido por tipo de entidade com navegação intuitiva

### 5. **Suporte a Múltiplos Modelos**
- **Modelos em nuvem**: Gemini (Google), OpenAI GPT
- **Modelos locais**: Ollama para execução offline
- **Extensibilidade**: Sistema de plugins para novos provedores

### 6. **Saídas Estruturadas Confiáveis**
- Esquemas consistentes baseados em exemplos
- Geração controlada para garantir formato estruturado
- Suporte a formatos JSON e YAML

## Como Usar o LangExtract para Estruturar Textos

### Passo 1: Definir a Tarefa de Extração

```python
import langextract as lx
import textwrap

# Definir o prompt com instruções claras
prompt = textwrap.dedent("""\
    Extrair informações específicas do texto em ordem de aparição.
    Usar texto exato para extrações. Não parafrasear.
    Fornecer atributos significativos para cada entidade.""")
```

### Passo 2: Criar Exemplos de Orientação

```python
# Fornecer exemplos de alta qualidade
examples = [
    lx.data.ExampleData(
        text="Texto de exemplo aqui",
        extractions=[
            lx.data.Extraction(
                extraction_class="tipo_entidade",
                extraction_text="texto_exato_extraído",
                attributes={"atributo": "valor"}
            ),
            # Mais extrações...
        ]
    )
]
```

### Passo 3: Executar a Extração

```python
# Processar o texto
result = lx.extract(
    text_or_documents=seu_texto,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",  # Modelo recomendado
    extraction_passes=3,          # Múltiplas passadas para melhor recall
    max_workers=20,               # Processamento paralelo
    max_char_buffer=1000          # Tamanho do contexto
)
```

### Passo 4: Salvar e Visualizar Resultados

```python
# Salvar em formato JSONL
lx.io.save_annotated_documents([result], 
                              output_name="resultados.jsonl", 
                              output_dir=".")

# Gerar visualização interativa
html_content = lx.visualize("resultados.jsonl")
with open("visualizacao.html", "w") as f:
    if hasattr(html_content, 'data'):
        f.write(html_content.data)
    else:
        f.write(html_content)
```

## Casos de Uso Práticos

### 1. **Análise de Documentos Médicos**
- **Extração de medicamentos**: Nome, dosagem, frequência, via de administração
- **Identificação de sintomas**: Descrição, intensidade, duração
- **Relacionamentos**: Medicamento → Condição, Sintoma → Diagnóstico

### 2. **Processamento de Literatura**
- **Personagens**: Nomes, estados emocionais, características
- **Relacionamentos**: Tipo de relação, contexto, intensidade
- **Elementos narrativos**: Emoções, metáforas, diálogos

### 3. **Análise de Relatórios Técnicos**
- **Dados quantitativos**: Valores, unidades, contexto
- **Procedimentos**: Etapas, resultados, observações
- **Conclusões**: Recomendações, limitações, próximos passos

### 4. **Processamento de Documentos Legais**
- **Cláusulas**: Tipo, condições, partes envolvidas
- **Datas e prazos**: Vencimentos, vigência, marcos
- **Entidades**: Pessoas, empresas, jurisdições

## Vantagens Competitivas

### 1. **Precisão e Rastreabilidade**
- Cada extração é mapeada para sua posição exata no texto
- Permite verificação manual e auditoria completa
- Reduz erros de interpretação e hallucinations

### 2. **Escalabilidade**
- Processa documentos de qualquer tamanho
- Paralelização automática para melhor performance
- Estratégias otimizadas para documentos longos

### 3. **Flexibilidade**
- Adapta-se a qualquer domínio sem retreinamento
- Suporte a múltiplos modelos e provedores
- Extensível através de sistema de plugins

### 4. **Facilidade de Uso**
- API simples e intuitiva
- Documentação abrangente com exemplos práticos
- Visualizações interativas para análise imediata

### 5. **Formato de Dados Padrão**
- Saída em JSONL (JSON Lines) para interoperabilidade
- Compatível com ferramentas de análise de dados
- Fácil integração com pipelines existentes

## Configuração e Requisitos

### Instalação
```bash
pip install langextract
```

### Configuração de API
```bash
# Variável de ambiente (recomendado)
export LANGEXTRACT_API_KEY="sua-chave-api"

# Ou arquivo .env
echo "LANGEXTRACT_API_KEY=sua-chave-api" >> .env
```

### Modelos Suportados
- **Gemini 2.5 Flash**: Recomendado para uso geral (velocidade + qualidade)
- **Gemini 2.5 Pro**: Para tarefas complexas que requerem raciocínio profundo
- **OpenAI GPT-4**: Alternativa robusta (requer configuração adicional)
- **Ollama**: Para execução local sem dependência de API

## Limitações e Considerações

### 1. **Custos de API**
- Modelos em nuvem cobram por token processado
- Múltiplas passadas aumentam o custo
- Considerar quotas Tier 2 para uso intensivo

### 2. **Dependência de Exemplos**
- Qualidade dos exemplos impacta diretamente nos resultados
- Requer conhecimento do domínio para criar bons exemplos
- Pode necessitar iteração para otimizar performance

### 3. **Limitações dos LLMs**
- Possibilidade de hallucinations em informações inferidas
- Dependente da qualidade do modelo escolhido
- Resultados podem variar entre execuções

## Exemplos Práticos Detalhados

### Exemplo 1: Extração de Informações de Artigos Científicos

```python
import langextract as lx
import textwrap

# Definir prompt para artigos científicos
prompt = textwrap.dedent("""\
    Extrair informações estruturadas de artigos científicos:
    - Metodologias utilizadas
    - Resultados quantitativos
    - Conclusões principais
    - Limitações do estudo
    Usar texto exato, não parafrasear.""")

# Exemplo de orientação
examples = [
    lx.data.ExampleData(
        text="O estudo utilizou análise estatística ANOVA (p<0.05) em 150 participantes. Os resultados mostraram melhoria de 23% no grupo experimental. Limitação: amostra pequena.",
        extractions=[
            lx.data.Extraction(
                extraction_class="metodologia",
                extraction_text="análise estatística ANOVA (p<0.05)",
                attributes={"tipo": "estatística", "significancia": "p<0.05"}
            ),
            lx.data.Extraction(
                extraction_class="amostra",
                extraction_text="150 participantes",
                attributes={"tamanho": "150", "tipo": "participantes"}
            ),
            lx.data.Extraction(
                extraction_class="resultado",
                extraction_text="melhoria de 23% no grupo experimental",
                attributes={"valor": "23%", "grupo": "experimental", "tipo": "melhoria"}
            ),
            lx.data.Extraction(
                extraction_class="limitacao",
                extraction_text="amostra pequena",
                attributes={"categoria": "metodológica"}
            )
        ]
    )
]

# Processar artigo científico
texto_artigo = """
Nosso estudo empregou metodologia de ensaio clínico randomizado duplo-cego
com 300 pacientes divididos em dois grupos. Utilizamos análise de regressão
logística (OR=2.1, IC95%: 1.3-3.4) para avaliar os dados. Os resultados
indicaram redução significativa de 35% nos sintomas do grupo tratamento
comparado ao placebo. A principal limitação foi o período de seguimento
de apenas 6 meses.
"""

result = lx.extract(
    text_or_documents=texto_artigo,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash"
)
```

### Exemplo 2: Análise de Contratos Legais

```python
# Prompt para contratos
prompt_contrato = textwrap.dedent("""\
    Extrair elementos essenciais de contratos:
    - Partes envolvidas
    - Valores monetários
    - Datas e prazos
    - Obrigações e responsabilidades
    - Cláusulas especiais""")

examples_contrato = [
    lx.data.ExampleData(
        text="A Empresa XYZ Ltda. pagará R$ 50.000,00 até 30/12/2024 pela prestação de serviços de consultoria, conforme cláusula de confidencialidade.",
        extractions=[
            lx.data.Extraction(
                extraction_class="parte",
                extraction_text="Empresa XYZ Ltda.",
                attributes={"tipo": "contratante", "natureza": "pessoa_juridica"}
            ),
            lx.data.Extraction(
                extraction_class="valor",
                extraction_text="R$ 50.000,00",
                attributes={"moeda": "BRL", "valor_numerico": "50000"}
            ),
            lx.data.Extraction(
                extraction_class="prazo",
                extraction_text="até 30/12/2024",
                attributes={"data_limite": "2024-12-30", "tipo": "pagamento"}
            ),
            lx.data.Extraction(
                extraction_class="servico",
                extraction_text="prestação de serviços de consultoria",
                attributes={"categoria": "consultoria"}
            ),
            lx.data.Extraction(
                extraction_class="clausula",
                extraction_text="cláusula de confidencialidade",
                attributes={"tipo": "confidencialidade"}
            )
        ]
    )
]
```

### Exemplo 3: Processamento de Relatórios Médicos

```python
# Prompt para relatórios médicos
prompt_medico = textwrap.dedent("""\
    Extrair informações clínicas de relatórios médicos:
    - Sintomas apresentados
    - Exames realizados
    - Diagnósticos
    - Tratamentos prescritos
    - Medicações com dosagens""")

examples_medico = [
    lx.data.ExampleData(
        text="Paciente apresenta cefaleia intensa há 3 dias. Realizado TC de crânio sem alterações. Diagnóstico: enxaqueca. Prescrito Sumatriptana 50mg VO se necessário.",
        extractions=[
            lx.data.Extraction(
                extraction_class="sintoma",
                extraction_text="cefaleia intensa há 3 dias",
                attributes={"intensidade": "intensa", "duracao": "3 dias", "tipo": "cefaleia"}
            ),
            lx.data.Extraction(
                extraction_class="exame",
                extraction_text="TC de crânio",
                attributes={"tipo": "tomografia", "resultado": "sem alterações"}
            ),
            lx.data.Extraction(
                extraction_class="diagnostico",
                extraction_text="enxaqueca",
                attributes={"categoria": "neurológico"}
            ),
            lx.data.Extraction(
                extraction_class="medicamento",
                extraction_text="Sumatriptana 50mg VO se necessário",
                attributes={"nome": "Sumatriptana", "dose": "50mg", "via": "VO", "frequencia": "se necessário"}
            )
        ]
    )
]
```

## Técnicas Avançadas de Uso

### 1. **Extração com Múltiplas Passadas**
Para documentos complexos, use múltiplas passadas para aumentar o recall:

```python
result = lx.extract(
    text_or_documents=documento_complexo,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash",
    extraction_passes=5,  # 5 passadas independentes
    max_workers=30,       # Processamento paralelo
    max_char_buffer=800   # Contexto menor para maior precisão
)
```

### 2. **Processamento de URLs Diretas**
Processe documentos diretamente de URLs:

```python
result = lx.extract(
    text_or_documents="https://exemplo.com/documento.txt",
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash"
)
```

### 3. **Análise de Resultados**
Analise os resultados extraídos:

```python
# Contar tipos de entidades
from collections import Counter
tipos_entidades = Counter(e.extraction_class for e in result.extractions)
print("Distribuição de entidades:", tipos_entidades)

# Agrupar por atributos
entidades_por_categoria = {}
for extração in result.extractions:
    if extração.attributes and 'categoria' in extração.attributes:
        categoria = extração.attributes['categoria']
        if categoria not in entidades_por_categoria:
            entidades_por_categoria[categoria] = []
        entidades_por_categoria[categoria].append(extração)
```

## Integração com Outras Ferramentas

### 1. **Pandas para Análise de Dados**
```python
import pandas as pd
import json

# Carregar resultados JSONL
with open('resultados.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Converter para DataFrame
extractions_data = []
for doc in data:
    for ext in doc['extractions']:
        extractions_data.append({
            'classe': ext['extraction_class'],
            'texto': ext['extraction_text'],
            'posicao_inicio': ext['char_interval']['start_pos'],
            'posicao_fim': ext['char_interval']['end_pos'],
            'atributos': ext.get('attributes', {})
        })

df = pd.DataFrame(extractions_data)
```

### 2. **Jupyter Notebooks**
O LangExtract funciona perfeitamente em Jupyter Notebooks com visualizações inline:

```python
# Em uma célula do Jupyter
result = lx.extract(...)
lx.visualize(result)  # Exibe visualização interativa inline
```

### 3. **APIs e Microserviços**
```python
from flask import Flask, request, jsonify
import langextract as lx

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract_api():
    data = request.json
    result = lx.extract(
        text_or_documents=data['text'],
        prompt_description=data['prompt'],
        examples=data['examples'],
        model_id=data.get('model_id', 'gemini-2.5-flash')
    )

    return jsonify({
        'extractions': [
            {
                'class': e.extraction_class,
                'text': e.extraction_text,
                'attributes': e.attributes,
                'position': {
                    'start': e.char_interval.start_pos,
                    'end': e.char_interval.end_pos
                }
            }
            for e in result.extractions
        ]
    })
```

## Melhores Práticas

### 1. **Design de Prompts Eficazes**
- Seja específico sobre o que extrair
- Use linguagem clara e objetiva
- Inclua instruções sobre formato e ordem
- Especifique se deve usar texto exato ou permitir paráfrases

### 2. **Criação de Exemplos de Qualidade**
- Use exemplos representativos do domínio
- Inclua casos edge e variações
- Mantenha consistência nos atributos
- Teste com diferentes complexidades

### 3. **Otimização de Performance**
- Ajuste `max_char_buffer` baseado na complexidade do texto
- Use `max_workers` apropriado para sua infraestrutura
- Considere custos vs. qualidade ao escolher número de passadas
- Monitore uso de tokens para controlar custos

### 4. **Validação e Qualidade**
- Sempre revise uma amostra dos resultados
- Use visualizações para identificar padrões e erros
- Implemente validações automáticas quando possível
- Mantenha logs de performance e qualidade

## Conclusão

O LangExtract representa uma solução robusta e flexível para extração de informações estruturadas de textos não estruturados. Sua combinação de precisão, escalabilidade e facilidade de uso o torna uma ferramenta valiosa para pesquisadores, desenvolvedores e profissionais que precisam processar e estruturar grandes volumes de texto de forma eficiente e confiável.

A biblioteca democratiza o acesso a técnicas avançadas de processamento de linguagem natural, permitindo que usuários sem expertise em machine learning possam extrair insights valiosos de seus documentos através de uma interface simples e intuitiva.

Com suporte a múltiplos modelos, visualizações interativas e formato de dados padrão, o LangExtract se posiciona como uma ferramenta essencial para qualquer workflow que envolva análise e estruturação de texto em escala.
