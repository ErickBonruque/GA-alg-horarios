"""
Funções para carregar e validar dados dos arquivos CSV.
"""

from pathlib import Path
from typing import List, Tuple
import pandas as pd

from .models import Disciplina, Slot


def load_and_validate_csv(csv_dir: Path = Path("CSVs")) -> Tuple[List[Disciplina], List[Slot]]:
    """
    Carrega e valida os arquivos CSV de disciplinas e horários.
    
    Args:
        csv_dir: Diretório contendo os arquivos CSV
        
    Returns:
        Tupla contendo lista de disciplinas e lista de slots
        
    Raises:
        FileNotFoundError: Se os arquivos CSV não existirem
        ValueError: Se os CSVs estiverem malformados ou faltarem colunas
    """
    disciplinas_path = csv_dir / "disciplinas.csv"
    horarios_path = csv_dir / "horarios.csv"
    
    if not disciplinas_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {disciplinas_path}\n"
            f"   Certifique-se de que 'disciplinas.csv' está no diretório CSVs/"
        )
    
    if not horarios_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {horarios_path}\n"
            f"   Certifique-se de que 'horarios.csv' está no diretório CSVs/"
        )
    
    # Carregar disciplinas
    try:
        df_disciplinas = pd.read_csv(disciplinas_path)
    except Exception as e:
        raise ValueError(f"Erro ao ler disciplinas.csv: {e}")
    
    # Validar colunas obrigatórias
    required_cols_disc = ['periodo', 'codigo', 'nome', 'carga_horaria', 'professor', 'aulas_semanais']
    missing_cols = set(required_cols_disc) - set(df_disciplinas.columns)
    if missing_cols:
        raise ValueError(
            f"Colunas faltando em disciplinas.csv: {missing_cols}\n"
            f"   Colunas esperadas: {required_cols_disc}"
        )
    
    # Remover linhas vazias e criar objetos Disciplina
    df_disciplinas = df_disciplinas.dropna(subset=['codigo'])
    disciplinas = [
        Disciplina(
            periodo=int(row['periodo']),
            codigo=str(row['codigo']),
            nome=str(row['nome']),
            carga_horaria=int(row['carga_horaria']),
            professor=str(row['professor']),
            aulas_semanais=int(row['aulas_semanais'])
        )
        for _, row in df_disciplinas.iterrows()
    ]
    
    if not disciplinas:
        raise ValueError("Nenhuma disciplina encontrada em disciplinas.csv")
    
    # Carregar horários
    try:
        df_horarios = pd.read_csv(horarios_path)
    except Exception as e:
        raise ValueError(f"Erro ao ler horarios.csv: {e}")
    
    # Validar colunas obrigatórias
    required_cols_hora = ['slot_id', 'dia', 'inicio', 'fim']
    missing_cols = set(required_cols_hora) - set(df_horarios.columns)
    if missing_cols:
        raise ValueError(
            f"Colunas faltando em horarios.csv: {missing_cols}\n"
            f"   Colunas esperadas: {required_cols_hora}"
        )
    
    # Remover linhas vazias e criar objetos Slot
    df_horarios = df_horarios.dropna(subset=['slot_id'])
    slots = [
        Slot(
            slot_id=int(row['slot_id']),
            dia=str(row['dia']),
            inicio=str(row['inicio']),
            fim=str(row['fim'])
        )
        for _, row in df_horarios.iterrows()
    ]
    
    if not slots:
        raise ValueError("Nenhum slot de horário encontrado em horarios.csv")
    
    # Verificar unicidade dos slot_ids
    slot_ids = [s.slot_id for s in slots]
    if len(slot_ids) != len(set(slot_ids)):
        raise ValueError("Existem slot_ids duplicados em horarios.csv")
    
    return disciplinas, slots
