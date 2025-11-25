"""
Funções para construir e manipular o template do cromossomo.
"""

from typing import List, Dict, Tuple
from .models import Disciplina, Slot


def build_chromosome_template(disciplinas: List[Disciplina]) -> Tuple[List[Disciplina], int]:
    """
    Constrói o template do cromossomo expandindo cada disciplina
    de acordo com suas aulas semanais.
    
    Args:
        disciplinas: Lista de disciplinas
        
    Returns:
        Tupla com lista expandida de disciplinas e tamanho do cromossomo
    """
    expanded = []
    for disc in disciplinas:
        expanded.extend([disc] * disc.aulas_semanais)
    return expanded, len(expanded)


def create_slot_mapping(slots: List[Slot]) -> Dict[int, Slot]:
    """
    Cria um dicionário de mapeamento slot_id -> Slot.
    
    Args:
        slots: Lista de slots de horário
        
    Returns:
        Dicionário mapeando slot_id para objeto Slot
    """
    return {s.slot_id: s for s in slots}
