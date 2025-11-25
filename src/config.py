"""
Configurações e pesos do Algoritmo Genético.
"""

# ============================================================================
# PESOS DAS PENALIDADES E BONIFICAÇÕES
# ============================================================================

# Penalidades CRÍTICAS (subtraem da pontuação)
# Mantidas como hard constraints, porém em escala mais saudável
PESO_CONFLITO_PROFESSOR = 4000   # Professor com aulas simultâneas
PESO_CONFLITO_PERIODO = 4000     # Disciplinas do mesmo período no mesmo horário

# Penalidades de QUALIDADE DA GRADE - BLOCOS CONSECUTIVOS (PRIORIDADE MÁXIMA)
# Ainda prioritárias, mas sem ultrapassar exageradamente o resto
PESO_BLOCO_INCOMPLETO = 350      # AULAS ISOLADAS
PESO_OVERLOAD_SEQUENCIAL = 550   # Blocos com mais de 3 aulas seguidas

# Penalidades de QUALIDADE DA GRADE - Distribuição
PESO_FRAGMENTACAO = 160          # Quebras dentro do mesmo dia para uma disciplina
PESO_PULVERIZACAO_SEMANAL = 150  # Aulas muito espalhadas ao longo da semana
PESO_SALTO_TEMPORAL = 120        # Saltos exagerados (manhã e tarde) na mesma disciplina

# Penalidades de OTIMIZAÇÃO FINO (mais leves)
PESO_CONCENTRACAO = 60           # Muitas aulas da mesma disciplina no mesmo dia
PESO_LACUNA = 25                 # Buracos (gaps) na grade por período
PESO_SOBRECARGA_DIARIA = 180     # Dias com mais de 5 aulas (homogeneidade da grade)

# Bonificações (adicionam à pontuação) - RECOMPENSA ALTA POR BLOCOS IDEAIS
# Reduzido para manter bons blocos sem distorcer o restante da distribuição
PESO_AULAS_SEQUENCIAIS = 220     # Incentiva blocos ideais de 2-3 aulas consecutivas

# Limites/thresholds auxiliares
MIN_AULAS_SEQUENCIAIS_IDEAL = 2
MAX_AULAS_SEQUENCIAIS_IDEAL = 3
THRESHOLD_SALTO_TEMPORAL = 4     # Diferença de índices > 4 indica salto dentro do dia
MAX_AULAS_POR_DIA = 5            # Limite máximo de aulas por dia para um período

# ============================================================================
# CONFIGURAÇÕES DO ALGORITMO GENÉTICO
# ============================================================================

POPULATION_SIZE = 100           # Tamanho da população
NUM_GENERATIONS = 16750           # Número de gerações (maior exploração)
CROSSOVER_PROB = 0.7            # Probabilidade de crossover
MUTATION_PROB = 0.2             # Probabilidade de mutação
TOURNAMENT_SIZE = 3             # Tamanho do torneio para seleção
MUTATION_INDPB = 0.2            # Probabilidade de mutação por gene

# Pontuação base (antes das penalidades/bonificações)
BASE_SCORE = 10000

# Seed para reprodutibilidade
RANDOM_SEED = 13

# Limite máximo de aulas em sequência para bonificação
MAX_AULAS_SEQUENCIAIS = 3
