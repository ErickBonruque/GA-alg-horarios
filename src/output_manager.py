"""
Gerenciador de outputs do algoritmo genético.
Salva os melhores horários e informações da execução.
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from .models import Disciplina, Slot


class OutputManager:
    """Gerencia o salvamento de resultados do algoritmo genético."""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Inicializa o gerenciador de outputs.
        
        Args:
            output_dir: Diretório onde os outputs serão salvos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Criar diretório para esta execução com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.output_dir / f"run_{timestamp}"
        self.run_dir.mkdir(exist_ok=True)
        
    def save_execution_data(
        self,
        top_individuals: List[Any],
        top_fitnesses: List[float],
        best_fitness_history: List[float],
        avg_fitness_history: List[float],
        execution_time: float,
        config: Dict[str, Any],
        expanded_disciplines: List[Disciplina],
        slot_mapping: Dict[int, Slot],
        disciplinas_unicas: List[Disciplina]
    ) -> None:
        """
        Salva todos os dados da execução do algoritmo.
        
        Args:
            top_individuals: Lista com os 3 melhores indivíduos
            top_fitnesses: Lista com as pontuações dos 3 melhores
            best_fitness_history: Histórico do melhor fitness por geração
            avg_fitness_history: Histórico do fitness médio por geração
            execution_time: Tempo de execução em segundos
            config: Configurações usadas no algoritmo
            expanded_disciplines: Lista expandida de disciplinas
            slot_mapping: Mapeamento de slots
            disciplinas_unicas: Lista de disciplinas únicas
        """
        # Salvar dados de execução em JSON
        execution_data = {
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": execution_time,
            "config": config,
            "top_3_fitnesses": [float(f) for f in top_fitnesses],
            "best_fitness_per_generation": [float(f) for f in best_fitness_history],
            "avg_fitness_per_generation": [float(f) for f in avg_fitness_history],
            "total_generations": len(best_fitness_history),
            "final_best_fitness": float(top_fitnesses[0]) if top_fitnesses else 0,
            "final_avg_fitness": float(avg_fitness_history[-1]) if avg_fitness_history else 0,
            "convergence_info": self._analyze_convergence(best_fitness_history),
            "num_disciplines": len(disciplinas_unicas),
            "total_weekly_classes": sum(d.aulas_semanais for d in disciplinas_unicas),
        }
        
        # Salvar JSON com informações gerais
        with open(self.run_dir / "execution_summary.json", "w", encoding="utf-8") as f:
            json.dump(execution_data, f, indent=2, ensure_ascii=False)
        
        # Salvar os 3 melhores indivíduos com pickle (para análise posterior)
        individuals_data = {
            "top_individuals": top_individuals,
            "top_fitnesses": top_fitnesses,
            "expanded_disciplines": expanded_disciplines,
            "slot_mapping": slot_mapping,
            "disciplinas_unicas": disciplinas_unicas
        }
        
        with open(self.run_dir / "top_individuals.pkl", "wb") as f:
            pickle.dump(individuals_data, f)
        
        # Salvar históricos em formato CSV para fácil análise
        self._save_fitness_history_csv(best_fitness_history, avg_fitness_history)
        
        print(f"\n✓ Dados salvos em: {self.run_dir}")
        
    def save_schedule_details(
        self,
        rank: int,
        individual: List[int],
        fitness: float,
        schedule: List[Dict[str, Any]],
        fitness_info: Dict[str, Any]
    ) -> None:
        """
        Salva detalhes de um horário específico.
        
        Args:
            rank: Posição do horário (1, 2 ou 3)
            individual: Cromossomo do indivíduo
            fitness: Pontuação de fitness
            schedule: Horário decodificado
            fitness_info: Informações detalhadas de fitness
        """
        schedule_data = {
            "rank": rank,
            "fitness": float(fitness),
            "fitness_details": {
                "base_score": fitness_info.get("base_score", 0),
                "conflicts": fitness_info.get("conflicts", 0),
                "penalties": fitness_info.get("penalties", {}),
                "bonuses": fitness_info.get("bonuses", {}),
            },
            "chromosome": individual,
            "schedule": schedule
        }
        
        # Salvar JSON do horário
        filename = f"schedule_rank_{rank}.json"
        with open(self.run_dir / filename, "w", encoding="utf-8") as f:
            json.dump(schedule_data, f, indent=2, ensure_ascii=False)
    
    def _save_fitness_history_csv(
        self,
        best_fitness_history: List[float],
        avg_fitness_history: List[float]
    ) -> None:
        """Salva histórico de fitness em formato CSV."""
        csv_path = self.run_dir / "fitness_history.csv"
        
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("generation,best_fitness,avg_fitness\n")
            for gen, (best, avg) in enumerate(zip(best_fitness_history, avg_fitness_history), 1):
                f.write(f"{gen},{best},{avg}\n")
    
    def _analyze_convergence(self, best_fitness_history: List[float]) -> Dict[str, Any]:
        """
        Analisa a convergência do algoritmo.
        
        Returns:
            Dicionário com informações sobre convergência
        """
        if not best_fitness_history:
            return {}
        
        # Encontrar em qual geração atingiu o melhor fitness
        max_fitness = max(best_fitness_history)
        best_gen = best_fitness_history.index(max_fitness) + 1
        
        # Calcular melhoria
        initial_fitness = best_fitness_history[0]
        final_fitness = best_fitness_history[-1]
        improvement = final_fitness - initial_fitness
        improvement_percent = (improvement / abs(initial_fitness)) * 100 if initial_fitness != 0 else 0
        
        # Verificar estagnação (últimas 20% das gerações)
        last_20_percent = int(len(best_fitness_history) * 0.2)
        if last_20_percent > 0:
            recent_history = best_fitness_history[-last_20_percent:]
            stagnation = len(set(recent_history)) == 1
        else:
            stagnation = False
        
        return {
            "best_generation": best_gen,
            "initial_fitness": float(initial_fitness),
            "final_fitness": float(final_fitness),
            "improvement": float(improvement),
            "improvement_percent": float(improvement_percent),
            "stagnated": stagnation
        }
    
    def get_run_directory(self) -> Path:
        """Retorna o diretório da execução atual."""
        return self.run_dir
