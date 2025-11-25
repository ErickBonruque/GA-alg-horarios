# Geração Automática de Horários com Algoritmo Genético

## Modelo de Dados

### Arquivo: `disciplinas.csv`

Contém as disciplinas que precisam ser alocadas na grade horária:

| Coluna           | Descrição                                      | Exemplo                  |
|------------------|------------------------------------------------|--------------------------|
| `periodo`        | Semestre (1, 2, 3 ou 4)                        | `1`                      |
| `codigo`         | Identificador único da disciplina              | `CC1AED1`                |
| `nome`           | Nome completo da disciplina                    | `Algoritmos e ED I`      |
| `carga_horaria`  | Carga horária total em horas                   | `90`                     |
| `professor`      | Nome do docente responsável                    | `Anderson Brilhador`     |
| `aulas_semanais` | Número de aulas por semana (cada aula = 50min) | `4`                      |

**Total:** 23 disciplinas distribuídas em 4 períodos.

### Arquivo: `horarios.csv`

Define os slots de tempo disponíveis para alocação:

| Coluna    | Descrição                          | Exemplo |
|-----------|------------------------------------|---------|
| `slot_id` | Identificador único do slot        | `1`     |
| `dia`     | Dia da semana (SEG, TER, QUA, etc.)| `SEG`   |
| `inicio`  | Hora de início (formato HH:MM)     | `07:30` |
| `fim`     | Hora de término (formato HH:MM)    | `08:20` |

**Total:** 45 slots (9 slots/dia × 5 dias úteis).

---

## Representação do Cromossomo

Cada **indivíduo** (solução candidata) é representado por uma **lista de inteiros**, onde cada inteiro corresponde a um `slot_id` válido de `horarios.csv`.

### Estrutura do Cromossomo

1. **Expansão por `aulas_semanais`**: Para cada disciplina, criamos tantos genes quantas forem suas `aulas_semanais`.
   - Exemplo: se "Algoritmos I" tem 4 aulas por semana, ocupará 4 posições no cromossomo.
   
2. **Cada gene = um slot_id**: O valor de cada gene indica em qual slot aquela aula está alocada.

3. **Ordem fixa**: O cromossomo segue a ordem das disciplinas em `disciplinas.csv`, expandidas por suas aulas semanais.

### Exemplo Simplificado

Suponha:
- Disciplina A (2 aulas/semana)
- Disciplina B (3 aulas/semana)

Um cromossomo possível seria: `[5, 12, 19, 23, 30]`

Interpretação:
- Aula 1 de A → slot 5 (segunda-feira, 13:00-13:50)
- Aula 2 de A → slot 12 (terça-feira, 10:20-11:10)
- Aula 1 de B → slot 19 (quarta-feira, 07:30-08:20)
- Aula 2 de B → slot 23 (quarta-feira, 13:00-13:50)
- Aula 3 de B → slot 30 (quinta-feira, 10:20-11:10)

---

## Função de Aptidão (Fitness)

A qualidade de cada cromossomo é avaliada por uma **função de aptidão multi-objetivo** que maximiza a pontuação (quanto maior, melhor). O sistema foi aprimorado com novas penalidades e métricas para produzir grades mais **homogêneas** e **naturais**.

Começamos com uma pontuação base de **10.000 pontos**, subtraímos penalidades por violações de restrições e adicionamos bonificações por características desejáveis.

### Hierarquia de Prioridades

As penalidades e bonificações são organizadas em níveis de prioridade:

1. **CRÍTICAS** (peso muito alto): Violações inaceitáveis
2. **QUALIDADE DA GRADE** (peso médio-alto): Características de uma grade bem estruturada
3. **OTIMIZAÇÕES** (peso leve): Refinamentos e melhorias adicionais
4. **BONIFICAÇÕES**: Recompensas por padrões desejáveis

---

### 1. PENALIDADES CRÍTICAS (Peso Muito Alto)

Estas penalidades têm **prioridade máxima** e devem ser evitadas a todo custo.

#### 1.1. **Conflito de Professor** (peso: -4000 por conflito)
- **Descrição**: Um mesmo professor não pode dar aula em dois locais diferentes no mesmo horário.
- **Detecção**: Identificamos se algum professor aparece mais de uma vez no mesmo `slot_id`.
- **Exemplo**: Professor "João" ministrando "Cálculo" e "Álgebra" simultaneamente no slot 15.
- **Impacto**: CRÍTICO - Impossível de executar na prática.

#### 1.2. **Conflito de Período** (peso: -4000 por conflito)
- **Descrição**: Disciplinas do mesmo período não podem ter aulas simultâneas (alunos não podem estar em dois lugares ao mesmo tempo).
- **Detecção**: Verificamos se há duas ou mais disciplinas do mesmo `periodo` alocadas ao mesmo `slot_id`.
- **Exemplo**: "Algoritmos I" (1º período) e "Lógica" (1º período) marcadas para o slot 8.
- **Impacto**: CRÍTICO - Violação física de capacidade.

---

### 2. PENALIDADES DE QUALIDADE DA GRADE (Peso Médio-Alto)

Estas penalidades buscam criar uma grade **homogênea** e **natural**, favorecendo blocos consecutivos ideais.

#### 2.1. **Blocos Incompletos** (peso: -350 por aula isolada)
- **Descrição**: Penaliza fortemente aulas isoladas que não formam blocos consecutivos.
- **Conceito**: Uma aula é considerada "isolada" quando não está conectada a outras aulas da mesma disciplina.
- **Exemplo RUIM**: Algoritmos com 1 aula às 07:30, outra às 11:10 e outra às 15:50 (3 aulas isoladas).
- **Exemplo BOM**: Algoritmos com 3 aulas consecutivas 07:30, 08:20, 09:10 (1 bloco, zero aulas isoladas).
- **Benefício**: Força formação de blocos de 2-3 aulas, melhorando aproveitamento pedagógico.

#### 2.2. **Overload Sequencial** (peso: -550 por bloco excessivo)
- **Descrição**: Penaliza blocos com **MAIS de 3 aulas consecutivas** da mesma disciplina.
- **Razão**: Mais de 3 aulas seguidas causa fadiga e reduz absorção de conteúdo.
- **Exemplo RUIM**: 4 ou 5 aulas seguidas de Algoritmos (bloco muito longo).
- **Exemplo BOM**: Blocos de 2 ou 3 aulas seguidas (dentro do ideal).
- **Benefício**: Evita sobrecarga cognitiva mantendo blocos produtivos.

#### 2.3. **Fragmentação de Disciplinas** (peso: -160 por quebra)
- **Descrição**: Penaliza quando as aulas da mesma disciplina no mesmo dia ficam **muito fragmentadas** (não consecutivas).
- **Conceito**: "Quebras" ocorrem quando há gaps entre aulas da mesma disciplina no mesmo dia.
- **Exemplo RUIM**: Algoritmos com aulas nos slots 1, 3, 7 (duas quebras - muita fragmentação).
- **Exemplo BOM**: Algoritmos com aulas nos slots 1, 2, 3 (sem quebras - bloco consecutivo).
- **Benefício**: Facilita o planejamento e reduz tempo de retomada de conteúdo.

#### 2.4. **Pulverização Semanal** (peso: -150 por violação)
- **Descrição**: Penaliza disciplinas com aulas **muito espalhadas** ao longo da semana sem necessidade.
- **Métrica**: Razão entre dias utilizados e total de aulas (quanto mais próximo de 1.0, mais pulverizado).
- **Exemplo RUIM**: 4 aulas em 4 dias diferentes (pulverização = 1.0 - muito espalhado).
- **Exemplo BOM**: 4 aulas em 2 dias (pulverização = 0.5 - bem concentrado).
- **Limiar**: Penaliza se pulverização > 0.75.
- **Benefício**: Cria padrões mais previsíveis e facilita memorização pelos alunos.

#### 2.5. **Saltos Temporais** (peso: -120 por salto)
- **Descrição**: Penaliza quando a mesma disciplina tem aulas em **horários muito distantes** no mesmo dia.
- **Threshold**: Considera "salto" quando há distância > 4 slots entre primeira e última aula do dia.
- **Exemplo RUIM**: Algoritmos com aulas às 07:30 e 16:40 (distância de 9 slots).
- **Exemplo BOM**: Algoritmos com aulas às 07:30 e 09:10 (distância de 2 slots).
- **Benefício**: Evita desconforto para professores e alunos, facilita deslocamento.

---

### 3. PENALIDADES DE OTIMIZAÇÃO (Peso Leve)

Penalidades complementares para refinamento da grade.

#### 3.1. **Concentração Excessiva** (peso: -60 por violação)
- **Descrição**: Evita colocar **todas** as aulas de uma disciplina no mesmo dia (sobrecarga pontual).
- **Detecção**: Penaliza quando uma disciplina tem mais de 2 aulas no mesmo dia.
- **Exemplo**: "Engenharia de Software" (4 aulas) com todas as 4 aulas na segunda-feira.

#### 3.2. **Lacunas (Buracos)** (peso: -25 por buraco)
- **Descrição**: Evita deixar slots vazios entre aulas do **mesmo período** no mesmo dia.
- **Detecção**: Para cada dia e período, conta-se quantos slots ficam vazios entre a primeira e última aula.
- **Exemplo**: Período 1 tem aulas nos slots 1, 2 e 5 de segunda → slots 3 e 4 vazios = 2 buracos.
- **Benefício**: Minimiza tempo ocioso dos alunos.

#### 3.3. **Sobrecarga Diária** (peso: -180 por excesso)
- **Descrição**: Penaliza períodos com **mais de 5 aulas no mesmo dia**.
- **Objetivo**: Garantir distribuição homogênea da carga horária ao longo da semana.
- **Detecção**: Para cada período e dia, conta-se o número de aulas. Se > 5, penaliza o excesso.
- **Exemplo RUIM**: 1º período com 7 aulas na segunda-feira (excesso de 2 aulas).
- **Exemplo BOM**: 1º período com distribuição de 4-5 aulas por dia.
- **Benefício**: Evita dias muito sobrecarregados e outros muito vazios.

---

### 4. BONIFICAÇÕES

#### 4.1. **Blocos Consecutivos Ideais** (peso: +220 por bloco)
- **Descrição**: Bonifica quando aulas da mesma disciplina formam **blocos consecutivos de 2-3 aulas**.
- **Bloco Ideal**: 2 ou 3 aulas seguidas (não mais que 3).
- **Exemplo**: "Algoritmos I" com aulas nos slots 1, 2, 3 (07:30, 08:20, 09:10).
- **Bonificação**: 1 bloco ideal × 220 pontos = +220.
- **Benefício**: 
  - Professores podem desenvolver tópicos mais complexos sem fragmentação
  - Reduz tempo de retomada de conteúdo
  - Melhora a dinâmica da aula
  - Facilita atividades práticas que requerem mais tempo

---

### Fórmula Final

```
fitness = 10000 
          - (conflitos_professor × 4000)        # CRÍTICO
          - (conflitos_periodo × 4000)           # CRÍTICO
          - (blocos_incompletos × 350)           # Qualidade (aulas isoladas)
          - (overload_sequencial × 550)          # Qualidade (blocos muito longos)
          - (fragmentacao × 160)                 # Qualidade (quebras no dia)
          - (pulverizacao_semanal × 150)         # Qualidade (espalhamento semanal)
          - (saltos_temporais × 120)             # Qualidade (saltos temporais)
          - (sobrecarga_diaria × 180)            # Otimização (mais de 5 aulas/dia)
          - (concentrações × 60)                 # Otimização (mesma disciplina no dia)
          - (lacunas × 25)                       # Otimização (gaps na grade)
          + (blocos_consecutivos_ideais × 220)   # Bonificação
```

**Objetivo**: Maximizar essa pontuação. Com as bonificações, é possível ultrapassar 10.000 pontos. Valores acima de 9.000 indicam excelentes soluções.

---

### Tabela Completa de Pesos

| Componente                    | Tipo        | Peso  | Prioridade     | Arquivo            |
|-------------------------------|-------------|-------|----------------|--------------------|
| Conflito de Professor         | Penalidade  | -4000 | CRÍTICA        | `src/config.py`    |
| Conflito de Período           | Penalidade  | -4000 | CRÍTICA        | `src/config.py`    |
| Blocos Incompletos (isolados) | Penalidade  | -350  | Alta           | `src/config.py`    |
| Overload Sequencial (>3)      | Penalidade  | -550  | Alta           | `src/config.py`    |
| Fragmentação de Disciplinas   | Penalidade  | -160  | Alta           | `src/config.py`    |
| Pulverização Semanal          | Penalidade  | -150  | Alta           | `src/config.py`    |
| Saltos Temporais              | Penalidade  | -120  | Alta           | `src/config.py`    |
| Sobrecarga Diária (>5 aulas)  | Penalidade  | -180  | Média          | `src/config.py`    |
| Concentração Excessiva        | Penalidade  | -60   | Média          | `src/config.py`    |
| Lacunas (Buracos)             | Penalidade  | -25   | Baixa          | `src/config.py`    |
| Blocos Consecutivos Ideais    | Bonificação | +220  | Desejável      | `src/config.py`    |

---

### Funções Auxiliares Implementadas

Para suportar as novas penalidades, foram implementadas funções auxiliares didáticas:

#### `get_daily_distribution()`
Retorna a distribuição de aulas por disciplina e dia, convertendo horários em índices numéricos para facilitar análises.

#### `count_consecutive_blocks()`
Conta e classifica blocos de aulas consecutivas:
- **Blocos ideais**: 2-3 aulas seguidas
- **Blocos overload**: 4+ aulas seguidas
- **Aulas isoladas**: Aulas únicas sem sequência

#### `compute_discipline_daily_spread()`
Calcula métricas de fragmentação e pulverização:
- Dias utilizados
- Total de aulas
- Fragmentação média por dia (número de quebras)
- Razão de pulverização (dias/aulas)

#### `compute_temporal_jump_penalty()`
Detecta saltos temporais exagerados:
- Número de saltos detectados
- Maior distância entre aulas no mesmo dia
- Lista de dias onde há saltos

---

### Ajuste de Pesos e Calibração

Os pesos foram calibrados para criar uma **hierarquia clara de prioridades**:

1. **Conflitos críticos** (4000): Violações absolutas que impossibilitam a execução.
2. **Qualidade estrutural** (120-550): Penalidades que afetam significativamente a usabilidade da grade.
3. **Otimizações** (25-180): Refinamentos que melhoram a experiência, mas não são críticos.
4. **Bonificações** (220): Recompensas por padrões ideais.

**Personalização**: Você pode ajustar todos os pesos no arquivo `src/config.py` para priorizar diferentes objetivos conforme as necessidades da instituição.

---

## Configuração do Algoritmo Genético

Utilizamos a biblioteca **DEAP** (Distributed Evolutionary Algorithms in Python) para implementar o AG. Abaixo os principais parâmetros e operadores:

### Parâmetros

| Parâmetro               | Valor Padrão | Descrição                                           |
|-------------------------|--------------|-----------------------------------------------------|
| **Tamanho da População**| 100          | Número de indivíduos (soluções) por geração         |
| **Número de Gerações**  | 16750        | Quantas iterações de evolução executar              |
| **Probabilidade Crossover** | 0.7      | Chance de dois indivíduos cruzarem genes (70%)      |
| **Probabilidade Mutação**   | 0.2      | Chance de um gene sofrer mutação aleatória (20%)    |
| **Tamanho do Torneio**  | 3            | Número de indivíduos competindo na seleção          |
| **Elitismo (Hall of Fame)** | 3        | Preserva os 3 melhores indivíduos de cada geração   |

### Operadores Genéticos

#### **Seleção: Torneio (Tournament Selection)**
- Seleciona indivíduos para reprodução através de competições.
- Em cada torneio, escolhemos aleatoriamente 3 indivíduos e selecionamos o melhor (maior fitness).
- **Vantagem**: Pressão seletiva ajustável (tamanho do torneio) + diversidade preservada.

#### **Cruzamento: Two-Point Crossover**
- Escolhe dois pontos de corte aleatórios no cromossomo.
- Troca o segmento entre os dois pontos entre os pais, gerando dois filhos.
- **Exemplo**:
  ```
  Pai1:  [1, 2, | 3, 4, 5 | 6, 7]
  Pai2:  [8, 9, | 10, 11, 12 | 13, 14]
  ↓
  Filho1: [1, 2, | 10, 11, 12 | 6, 7]
  Filho2: [8, 9, | 3, 4, 5 | 13, 14]
  ```

#### **Mutação: Uniform Integer Mutation**
- Para cada gene, com probabilidade `indpb=0.2`, substitui o slot_id atual por outro válido aleatório.
- **Função**: Introduzir diversidade e escapar de ótimos locais.
- **Exemplo**: Gene com valor 5 pode ser mutado para 23 aleatoriamente.

#### **Hall of Fame**
- Mantém uma cópia dos melhores indivíduos encontrados ao longo de todas as gerações.
- Garante que a melhor solução nunca seja perdida, mesmo que a população atual piore.

---

## Bibliotecas Utilizadas

| Biblioteca   | Função                                                                 |
|--------------|------------------------------------------------------------------------|
| **pandas**   | Leitura e manipulação dos arquivos CSV                                 |
| **numpy**    | Operações vetorizadas, geração de números aleatórios                   |
| **deap**     | Framework de algoritmos genéticos (população, crossover, mutação, etc.)|
| **tabulate** | Exibição de tabelas formatadas no console (opcional)                   |
| **rich**     | Logs coloridos e barra de progresso no terminal (opcional)             |
| **matplotlib**| Geração de gráficos de evolução do fitness (opcional)                  |

**Nota**: As bibliotecas `tabulate`, `rich` e `matplotlib` são opcionais. Se não estiverem instaladas, o programa funciona com saídas mais simples.

---

## Como Usar

### 1. Instalar Dependências

Certifique-se de ter Python 3.8+ instalado. Então, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

**Conteúdo de `requirements.txt`:**
```
pandas>=2.0.0
numpy>=1.24.0
deap>=1.4.0
tabulate>=0.9.0
rich>=13.0.0
matplotlib>=3.7.0
```

### 2. Executar o Programa

No diretório raiz do projeto, execute:

```bash
python main.py
```

### 3. Interpretar a Saída

O programa exibirá:

1. **Log de Progresso**: Informações de cada geração (melhor fitness, fitness médio)
   ```
   Geração 1/500 | Melhor: 7850 | Média: 6420
   Geração 2/500 | Melhor: 8100 | Média: 6890
   ...
   ```

2. **Melhor Solução Encontrada**: Fitness final e estatísticas
   ```
   ╔══════════════════════════════════════╗
   ║   MELHOR HORÁRIO ENCONTRADO          ║
   ║   Fitness: 9250                      ║
   ╚══════════════════════════════════════╝
   ```

3. **Grade Horária por Período**: Tabela organizada por dia e horário
   ```
   ┌─────────┬──────────┬──────────────────────┬──────────────────┐
   │ Período │ Dia      │ Horário              │ Disciplina       │
   ├─────────┼──────────┼──────────────────────┼──────────────────┤
   │ 1       │ SEG      │ 07:30 - 08:20        │ Lógica Matemática│
   │ 1       │ SEG      │ 08:20 - 09:10        │ Algoritmos I     │
   ...
   ```

4. **Arquivo HTML (opcional)**: `horario_final.html` com a grade em formato de tabela HTML

5. **Gráfico de Evolução (opcional)**: `fitness_evolution.png` mostrando como o fitness melhorou ao longo das gerações

### 4. Verificar Qualidade

- **Fitness > 9000**: Excelente! Poucos ou nenhum conflito crítico
- **Fitness 8000-9000**: Bom, mas pode ter algumas lacunas ou concentrações
- **Fitness < 8000**: Solução subótima, considere aumentar o número de gerações

---

## Como Estender

### Ajustar Pesos das Penalidades e Bonificações

No arquivo `src/config.py`, localize as constantes:

```python
# Penalidades CRÍTICAS
PESO_CONFLITO_PROFESSOR = 4000  # Prioridade máxima
PESO_CONFLITO_PERIODO = 4000

# Penalidades de QUALIDADE DA GRADE
PESO_BLOCO_INCOMPLETO = 350      # Aulas isoladas
PESO_OVERLOAD_SEQUENCIAL = 550   # Blocos muito longos
PESO_FRAGMENTACAO = 160          # Quebras no mesmo dia
PESO_PULVERIZACAO_SEMANAL = 150  # Espalhamento semanal
PESO_SALTO_TEMPORAL = 120        # Saltos temporais

# Penalidades de OTIMIZAÇÃO
PESO_SOBRECARGA_DIARIA = 180     # Mais de 5 aulas/dia
PESO_CONCENTRACAO = 60           # Mesma disciplina no dia
PESO_LACUNA = 25                 # Buracos (gaps)

# Bonificações
PESO_AULAS_SEQUENCIAIS = 220     # Blocos ideais 2-3 aulas
MIN_AULAS_SEQUENCIAIS_IDEAL = 2  # Mínimo para bloco ideal
MAX_AULAS_SEQUENCIAIS_IDEAL = 3  # Máximo para bloco ideal
THRESHOLD_SALTO_TEMPORAL = 4     # Número de slots considerado "salto"
MAX_AULAS_POR_DIA = 5            # Limite para sobrecarga
```

Modifique os valores para priorizar diferentes objetivos. Por exemplo:
- Aumentar `PESO_FRAGMENTACAO` para 250 tornará o algoritmo mais agressivo em eliminar fragmentação.
- Reduzir `PESO_CONCENTRACAO` para 40 relaxará a distribuição das aulas ao longo da semana.
- Aumentar `PESO_AULAS_SEQUENCIAIS` para 300 priorizará ainda mais blocos consecutivos ideais.
- Alterar `MAX_AULAS_SEQUENCIAIS_IDEAL` para 2 limitará blocos ideais a apenas 2 aulas.
- Reduzir `THRESHOLD_SALTO_TEMPORAL` para 3 tornará a detecção de saltos mais rigorosa.

### Adicionar Nova Restrição

Para adicionar uma nova penalidade (ex: capacidade de sala), siga este padrão:

1. **Criar função de penalidade**:
   ```python
   def penalidade_capacidade(individual, disciplinas, capacidades):
       """Penaliza alocações em salas com capacidade insuficiente."""
       penalidade = 0
       for gene, disciplina in zip(individual, disciplinas_expandidas):
           sala = obter_sala_do_slot(gene)
           if capacidades[sala] < disciplina.alunos:
               penalidade += 1
       return penalidade * 200  # Peso da penalidade
   ```

2. **Integrar na função de fitness**:
   ```python
   fitness = BASE_SCORE - ... - penalidade_capacidade(...)
   ```

### Ajustar Parâmetros do AG

No arquivo `src/config.py`:

```python
POPULATION_SIZE = 100      # Tamanho da população
NUM_GENERATIONS = 16750    # Número de gerações
CROSSOVER_PROB = 0.7       # Probabilidade de crossover
MUTATION_PROB = 0.2        # Probabilidade de mutação
TOURNAMENT_SIZE = 3        # Tamanho do torneio
MUTATION_INDPB = 0.2       # Probabilidade de mutação por gene
```

**Dica**: Se o fitness estagnar cedo, aumente a taxa de mutação para aumentar a exploração.

---

## Estrutura do Projeto

```
trabalho_algoritmo_genetico/
├── CSVs/
│   ├── disciplinas.csv          # Dados das disciplinas
│   └── horarios.csv              # Slots de tempo disponíveis
├── src/
│   ├── __init__.py               # Inicialização do pacote
│   ├── config.py                 # Pesos e configurações do AG
│   ├── models.py                 # Dataclasses (Disciplina, Slot)
│   ├── data_loader.py            # Carregamento e validação dos CSVs
│   ├── chromosome.py             # Template do cromossomo
│   ├── fitness.py                # Funções de penalidade e bonificação
│   ├── genetic_algorithm.py     # Configuração e execução do DEAP
│   ├── decoder.py                # Decodificação de cromossomos
│   └── visualization.py          # Impressão, HTML e gráficos
├── main.py                       # Ponto de entrada principal
├── requirements.txt              # Dependências Python
├── README.md                     # Documentação
├── horario_final.html           # Saída: grade em HTML (gerado)
└── fitness_evolution.png        # Saída: gráfico de evolução (gerado)
```

### Descrição dos Módulos

#### `src/config.py`
Centraliza todas as configurações do algoritmo:
- Pesos das penalidades e bonificações
- Parâmetros do AG (tamanho da população, gerações, etc.)
- Seed para reprodutibilidade

#### `src/models.py`
Define as estruturas de dados:
- `Disciplina`: Representa uma disciplina com período, código, nome, professor, etc.
- `Slot`: Representa um slot de tempo (dia, horário de início e fim)

#### `src/data_loader.py`
Responsável por:
- Carregar os arquivos CSV
- Validar colunas obrigatórias
- Criar objetos `Disciplina` e `Slot`
- Detectar erros (arquivos faltando, dados malformados)

#### `src/chromosome.py`
Funções para manipular o cromossomo:
- `build_chromosome_template()`: Expande disciplinas por aulas semanais
- `create_slot_mapping()`: Cria dicionário de mapeamento slot_id → Slot

#### `src/fitness.py`
Implementa a função de aptidão com arquitetura aprimorada:
- **Funções auxiliares** (didáticas):
  - `get_daily_distribution()`: Distribuição de aulas por dia
  - `count_consecutive_blocks()`: Contagem de blocos consecutivos
  - `compute_discipline_daily_spread()`: Métricas de fragmentação/pulverização
  - `compute_temporal_jump_penalty()`: Detecção de saltos temporais
- **Penalidades críticas**: conflito de professor, período
- **Penalidades de qualidade**: fragmentação, pulverização, saltos temporais
- **Penalidades de otimização**: concentração, lacunas, overload sequencial
- **Bonificações**: blocos consecutivos ideais (2-3 aulas)
- `evaluate_fitness()`: Calcula fitness total multi-objetivo

#### `src/genetic_algorithm.py`
Configura e executa o DEAP:
- `setup_deap_toolbox()`: Registra operadores (seleção, crossover, mutação)
- `run_genetic_algorithm()`: Loop evolutivo principal

#### `src/decoder.py`
Converte soluções em formato legível:
- `decode_schedule()`: Transforma cromossomo em lista de aulas
- `get_fitness_details()`: Retorna breakdown detalhado do fitness com TODAS as novas métricas:
  - Penalidades críticas
  - Penalidades de qualidade da grade
  - Penalidades de otimização
  - Bonificações
  - Estatísticas de blocos (ideais, overload, isoladas)

#### `src/visualization.py`
Gera saídas visuais:
- `print_schedule()`: Tabela formatada no terminal
- `export_html()`: Grade horária em HTML responsivo
- `plot_fitness_evolution()`: Gráfico de convergência do AG

#### `main.py`
Orquestra todo o processo:
1. Carrega dados
2. Constrói cromossomo
3. Configura AG
4. Executa evolução
5. Decodifica melhor solução
6. Gera saídas (terminal, HTML, gráfico)
7. Valida resultado
