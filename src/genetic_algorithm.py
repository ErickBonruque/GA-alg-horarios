"""
Configuração e execução do Algoritmo Genético usando DEAP.
"""

import random
import multiprocessing
from typing import List, Dict, Tuple
from deap import base, creator, tools, algorithms

from .models import Disciplina, Slot
from .fitness import evaluate_fitness
from .config import (
    POPULATION_SIZE,
    NUM_GENERATIONS,
    CROSSOVER_PROB,
    MUTATION_PROB,
    TOURNAMENT_SIZE,
    MUTATION_INDPB
)

# Verificar se rich está disponível
try:
    from rich.console import Console
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def setup_deap_toolbox(
    chromosome_size: int,
    valid_slot_ids: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot],
    disciplinas_unicas: List[Disciplina]
) -> base.Toolbox:
    """
    Configura o toolbox do DEAP com os operadores genéticos.
    """
    # Criar classes de fitness e indivíduo (apenas uma vez)
    if not hasattr(creator, "FitnessMax"):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMax)
    
    toolbox = base.Toolbox()
    
    # Registro de funções
    toolbox.register("attr_slot", random.choice, valid_slot_ids)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_slot, n=chromosome_size)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Operadores genéticos
    toolbox.register("evaluate", evaluate_fitness,
                     expanded_disciplines=expanded_disciplines,
                     slot_mapping=slot_mapping,
                     disciplinas_unicas=disciplinas_unicas)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt,
                     low=min(valid_slot_ids),
                     up=max(valid_slot_ids),
                     indpb=MUTATION_INDPB)
    toolbox.register("select", tools.selTournament, tournsize=TOURNAMENT_SIZE)
    
    return toolbox


def run_genetic_algorithm(
    toolbox: base.Toolbox,
    population_size: int = POPULATION_SIZE,
    num_generations: int = NUM_GENERATIONS,
    cxpb: float = CROSSOVER_PROB,
    mutpb: float = MUTATION_PROB
) -> Tuple[List[int], List[float], List[float], List, List[float]]:
    """
    Executa o algoritmo genético e retorna o melhor indivíduo e os top 3.
    
    Returns:
        Tupla contendo: melhor indivíduo, histórico de fitness máximo, histórico de fitness médio,
                       lista com top 3 indivíduos, lista com top 3 fitnesses
    """
    # Inicializar população
    population = toolbox.population(n=population_size)
    
    # Estatísticas
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda x: sum(v[0] for v in x) / len(x))
    stats.register("max", lambda x: max(v[0] for v in x))
    
    # Hall da Fama - manter top 3 indivíduos
    hof = tools.HallOfFame(3)
    
    # Histórico de fitness
    best_fitness_history = []
    avg_fitness_history = []
    
    # Configurar Multiprocessing
    # Usa todos os núcleos disponíveis da CPU
    pool = multiprocessing.Pool()
    toolbox.register("map", pool.map)
    
    try:
        # Avaliação inicial da população usando processamento paralelo
        fitnesses = toolbox.map(toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        
        hof.update(population)
        
        if HAS_RICH:
            console.print("\n[bold cyan]Iniciando evolução (com processamento paralelo)...[/bold cyan]\n")
        else:
            print("\nIniciando evolução (com processamento paralelo)...\n")
        
        for gen in range(1, num_generations + 1):
            offspring = toolbox.select(population, len(population))
            offspring = list(map(toolbox.clone, offspring))
            
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < cxpb:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
            
            for mutant in offspring:
                if random.random() < mutpb:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
            
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            
            # Avaliação paralela dos novos indivíduos
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            population[:] = offspring
            hof.update(population)
            
            record = stats.compile(population)
            best_fitness_history.append(record['max'])
            avg_fitness_history.append(record['avg'])
            
            if gen % 10 == 0 or gen == 1:
                if HAS_RICH:
                    console.print(
                        f"Geração {gen:3d}/{num_generations} | "
                        f"Melhor: [bold green]{record['max']:.0f}[/bold green] | "
                        f"Média: [yellow]{record['avg']:.0f}[/yellow]"
                    )
                else:
                    print(f"Geração {gen:3d}/{num_generations} | "
                          f"Melhor: {record['max']:.0f} | Média: {record['avg']:.0f}")
    
    finally:
        # Garantir que o pool seja fechado ao final
        pool.close()
        pool.join()
    
    best_individual = hof[0]
    
    # Extrair top 3 indivíduos e suas pontuações
    top_individuals = [ind[:] for ind in hof]  # Copiar os indivíduos
    top_fitnesses = [ind.fitness.values[0] for ind in hof]
    
    if HAS_RICH:
        console.print("\n[bold green]Evolução concluída![/bold green]\n")
        console.print("[cyan]Top 3 soluções encontradas:[/cyan]")
        for i, (ind, fit) in enumerate(zip(top_individuals, top_fitnesses), 1):
            console.print(f"  {i}º lugar: [bold green]{fit:.0f}[/bold green] pontos")
    else:
        print("\nEvolução concluída!\n")
        print("Top 3 soluções encontradas:")
        for i, (ind, fit) in enumerate(zip(top_individuals, top_fitnesses), 1):
            print(f"  {i}º lugar: {fit:.0f} pontos")
    
    return best_individual, best_fitness_history, avg_fitness_history, top_individuals, top_fitnesses
