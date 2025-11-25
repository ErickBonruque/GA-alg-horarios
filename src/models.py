"""
Modelos de dados para o sistema de geração de horários.
"""

from dataclasses import dataclass


@dataclass
class Disciplina:
    """Representa uma disciplina do currículo."""
    periodo: int
    codigo: str
    nome: str
    carga_horaria: int
    professor: str
    aulas_semanais: int


@dataclass
class Slot:
    """Representa um slot de tempo disponível."""
    slot_id: int
    dia: str
    inicio: str
    fim: str
