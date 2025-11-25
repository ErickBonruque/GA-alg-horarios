# Outputs do Algoritmo Genético

Esta pasta contém os resultados das execuções do algoritmo genético de geração de horários.

## Estrutura

Cada execução cria uma pasta com timestamp: `run_YYYYMMDD_HHMMSS/`

### Arquivos gerados por execução:

- **`execution_summary.json`**: Resumo geral da execução
  - Timestamp, tempo de execução
  - Configurações do algoritmo
  - Pontuações dos top 3 horários
  - Histórico de fitness (melhor e médio por geração)
  - Análise de convergência
  - Estatísticas gerais

- **`top_individuals.pkl`**: Dados binários (pickle) contendo:
  - Top 3 cromossomos/indivíduos
  - Disciplinas expandidas
  - Mapeamento de slots
  - Disciplinas únicas
  - (Para análise posterior e geração de relatórios)

- **`fitness_history.csv`**: Histórico de evolução em formato CSV
  - Colunas: generation, best_fitness, avg_fitness
  - Útil para análise e plotagem

- **`schedule_rank_1.json`**: Detalhes do 1º melhor horário
- **`schedule_rank_2.json`**: Detalhes do 2º melhor horário
- **`schedule_rank_3.json`**: Detalhes do 3º melhor horário

Cada arquivo `schedule_rank_N.json` contém:
- Ranking e pontuação de fitness
- Detalhes do fitness (penalidades, bonificações)
- Cromossomo completo
- Horário decodificado (lista de aulas alocadas)

## Uso

Estes dados podem ser usados posteriormente para:
- Gerar relatórios detalhados
- Comparar diferentes execuções
- Analisar a evolução do algoritmo
- Visualizar e exportar os melhores horários
