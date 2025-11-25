#!/usr/bin/env python3
"""
Gerador de Horários com Algoritmo Genético

Sistema de geração automática de horários para o curso de Ciência da Computação
da UTFPR - Santa Helena, utilizando Algoritmos Genéticos.
"""

import sys
import random
import time
import numpy as np
from pathlib import Path
from collections import Counter

# Importar módulos do projeto
from src.config import RANDOM_SEED
from src.data_loader import load_and_validate_csv
from src.chromosome import build_chromosome_template, create_slot_mapping
from src.genetic_algorithm import setup_deap_toolbox, run_genetic_algorithm
from src.decoder import decode_schedule, get_fitness_details
from src.visualization import print_schedule, export_html, plot_fitness_evolution
from src.output_manager import OutputManager
from src import config

# Verificar se rich está disponível
try:
    from rich.console import Console
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def main():
    """Função principal que orquestra todo o processo."""
    try:
        # Fixar seed para reprodutibilidade
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
        
        # Banner inicial
        if HAS_RICH:
            console.print("\n[bold cyan]Gerador de Horários com Algoritmo Genético[/bold cyan]")
            console.print("[cyan]" + "=" * 50 + "[/cyan]\n")
        else:
            print("\nGerador de Horários com Algoritmo Genético")
            print("=" * 50 + "\n")
        
        # 1. Carregar e validar dados
        if HAS_RICH:
            console.print("[yellow]Carregando dados...[/yellow]")
        else:
            print("Carregando dados...")
        
        disciplinas, slots = load_and_validate_csv()
        
        if HAS_RICH:
            console.print(f"[green]OK[/green] {len(disciplinas)} disciplinas carregadas")
            console.print(f"[green]OK[/green] {len(slots)} slots de horário disponíveis")
        else:
            print(f"OK - {len(disciplinas)} disciplinas carregadas")
            print(f"OK - {len(slots)} slots de horário disponíveis")
        
        # 2. Construir template do cromossomo
        expanded_disciplines, chromosome_size = build_chromosome_template(disciplinas)
        slot_mapping = create_slot_mapping(slots)
        valid_slot_ids = [s.slot_id for s in slots]
        
        if HAS_RICH:
            console.print(f"[green]OK[/green] Cromossomo: {chromosome_size} genes "
                          f"(total de aulas/semana)\n")
        else:
            print(f"OK - Cromossomo: {chromosome_size} genes (total de aulas/semana)\n")
        
        # 3. Configurar DEAP
        toolbox = setup_deap_toolbox(
            chromosome_size=chromosome_size,
            valid_slot_ids=valid_slot_ids,
            expanded_disciplines=expanded_disciplines,
            slot_mapping=slot_mapping,
            disciplinas_unicas=disciplinas
        )
        
        # 4. Executar Algoritmo Genético
        start_time = time.time()
        best_individual, best_fitness_history, avg_fitness_history, top_individuals, top_fitnesses = run_genetic_algorithm(toolbox)
        execution_time = time.time() - start_time
        
        # 5. Decodificar o melhor indivíduo
        schedule = decode_schedule(best_individual, expanded_disciplines, slot_mapping)
        fitness_info = get_fitness_details(
            best_individual,
            expanded_disciplines,
            slot_mapping,
            disciplinas
        )
        
        # 6. Imprimir horário
        print_schedule(schedule, fitness_info)
        
        # Inicializar OutputManager para gerenciar todos os arquivos de saída
        if HAS_RICH:
            console.print("\n[yellow]Salvando outputs...[/yellow]")
        else:
            print("\nSalvando outputs...")
        
        output_manager = OutputManager()
        run_dir = output_manager.get_run_directory()
        
        # 7. Exportar HTML
        export_html(schedule, output_path=run_dir / "horario_final.html")
        
        # 8. Plotar evolução do fitness
        plot_fitness_evolution(best_fitness_history, avg_fitness_history, output_path=run_dir / "fitness_evolution.png")
        
        # 9. Salvar outputs adicionais (top 3 horários e dados de execução)
        
        # Preparar configurações para salvar
        config_dict = {
            "population_size": config.POPULATION_SIZE,
            "num_generations": config.NUM_GENERATIONS,
            "crossover_prob": config.CROSSOVER_PROB,
            "mutation_prob": config.MUTATION_PROB,
            "tournament_size": config.TOURNAMENT_SIZE,
            "mutation_indpb": config.MUTATION_INDPB,
            "random_seed": config.RANDOM_SEED,
        }
        
        # Salvar dados gerais de execução
        output_manager.save_execution_data(
            top_individuals=top_individuals,
            top_fitnesses=top_fitnesses,
            best_fitness_history=best_fitness_history,
            avg_fitness_history=avg_fitness_history,
            execution_time=execution_time,
            config=config_dict,
            expanded_disciplines=expanded_disciplines,
            slot_mapping=slot_mapping,
            disciplinas_unicas=disciplinas
        )
        
        # Salvar detalhes de cada um dos top 3 horários
        for rank, (individual, fitness) in enumerate(zip(top_individuals, top_fitnesses), 1):
            schedule_rank = decode_schedule(individual, expanded_disciplines, slot_mapping)
            fitness_info_rank = get_fitness_details(
                individual,
                expanded_disciplines,
                slot_mapping,
                disciplinas
            )
            output_manager.save_schedule_details(
                rank=rank,
                individual=individual,
                fitness=fitness,
                schedule=schedule_rank,
                fitness_info=fitness_info_rank
            )
        
        if HAS_RICH:
            console.print(f"[green]OK[/green] Outputs salvos em: {output_manager.get_run_directory()}")
        else:
            print(f"OK - Outputs salvos em: {output_manager.get_run_directory()}")
        
        # 10. Verificação final (auto-check)
        if HAS_RICH:
            console.print("\n[bold yellow]Executando verificação final...[/bold yellow]")
        else:
            print("\nExecutando verificação final...")
        
        # Verificar se o número total de aulas por disciplina está correto
        disciplina_counts = Counter(d.codigo for d in expanded_disciplines)
        schedule_counts = Counter(item['codigo'] for item in schedule)
        
        all_ok = True
        for disc in disciplinas:
            expected = disc.aulas_semanais
            allocated = schedule_counts.get(disc.codigo, 0)
            if expected != allocated:
                print(f"AVISO: {disc.codigo} - esperado {expected} aulas, "
                      f"alocado {allocated}")
                all_ok = False
        
        if all_ok:
            if HAS_RICH:
                console.print("[green]OK - Todas as disciplinas têm o número correto de aulas alocadas![/green]")
            else:
                print("OK - Todas as disciplinas têm o número correto de aulas alocadas!")
        
        # Verificar se todos os slot_ids são válidos
        invalid_slots = [gene for gene in best_individual if gene not in valid_slot_ids]
        if invalid_slots:
            print(f"AVISO: Encontrados {len(invalid_slots)} slots inválidos")
        else:
            if HAS_RICH:
                console.print("[green]OK - Todos os slots alocados são válidos![/green]")
            else:
                print("OK - Todos os slots alocados são válidos!")
        
        # Mensagem final
        if HAS_RICH:
            console.print(f"\n[bold green]Processo concluído com sucesso![/bold green]")
            if fitness_info['fitness'] >= 9000:
                console.print("[bold green]Excelente solução encontrada![/bold green]")
            elif fitness_info['fitness'] >= 8000:
                console.print("[yellow]Boa solução encontrada![/yellow]")
            else:
                console.print("[yellow]Solução subótima. Considere aumentar o número de gerações.[/yellow]")
        else:
            print("\nProcesso concluído com sucesso!")
            if fitness_info['fitness'] >= 9000:
                print("Excelente solução encontrada!")
            elif fitness_info['fitness'] >= 8000:
                print("Boa solução encontrada!")
            else:
                print("Solução subótima. Considere aumentar o número de gerações.")
        
    except FileNotFoundError as e:
        print(f"\n{e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
