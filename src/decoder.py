"""
Funções para decodificar cromossomos em horários legíveis.
"""

from typing import List, Dict
from .models import Disciplina, Slot


def decode_schedule(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot]
) -> List[Dict]:
    """
    Decodifica um cromossomo (lista de slot_ids) em uma lista de aulas.
    
    Args:
        individual: Cromossomo (lista de slot_ids)
        expanded_disciplines: Lista expandida de disciplinas
        slot_mapping: Mapeamento de slot_id para Slot
        
    Returns:
        Lista de dicionários contendo informações de cada aula
    """
    schedule = []
    
    for gene, disc in zip(individual, expanded_disciplines):
        slot = slot_mapping.get(gene)
        if slot:
            schedule.append({
                'periodo': disc.periodo,
                'codigo': disc.codigo,
                'disciplina': disc.nome,
                'professor': disc.professor,
                'dia': slot.dia,
                'inicio': slot.inicio,
                'fim': slot.fim
            })
    
    schedule.sort(key=lambda x: (x['periodo'], x['dia'], x['inicio']))
    return schedule


def get_fitness_details(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot],
    disciplinas_unicas: List[Disciplina]
) -> Dict:
    """
    Calcula e retorna detalhes sobre o fitness de um indivíduo.
    
    Inclui todas as penalidades e bonificações implementadas no sistema,
    permitindo uma análise detalhada da qualidade da solução.
    
    Args:
        individual: Cromossomo (lista de slot_ids)
        expanded_disciplines: Lista expandida de disciplinas
        slot_mapping: Mapeamento de slot_id para Slot
        disciplinas_unicas: Lista de disciplinas únicas (sem expansão)
    
    Returns:
        Dicionário com fitness total e componentes individuais detalhados
    """
    from .fitness import (
        BASE_SCORE,
        penalidade_conflito_professor,
        penalidade_conflito_periodo,
        penalidade_concentracao,
        penalidade_lacuna,
        penalidade_fragmentacao_disciplina,
        penalidade_pulverizacao_semanal,
        penalidade_salto_temporal,
        penalidade_overload_sequencial,
        penalidade_blocos_incompletos,
        bonificacao_aulas_sequenciais,
        count_consecutive_blocks,
        get_daily_distribution,
        compute_discipline_daily_spread,
        compute_temporal_jump_penalty
    )
    
    # ========================================================================
    # CÁLCULO PRÉVIO DE ESTRUTURAS AUXILIARES
    # ========================================================================
    distribuicao = get_daily_distribution(individual, expanded_disciplines, slot_mapping)
    blocos_info = count_consecutive_blocks(distribuicao)
    spread_info = compute_discipline_daily_spread(distribuicao)
    saltos_info = compute_temporal_jump_penalty(distribuicao)
    
    # ========================================================================
    # CÁLCULO DAS PENALIDADES CRÍTICAS
    # ========================================================================
    pen_prof = penalidade_conflito_professor(individual, expanded_disciplines, slot_mapping)
    pen_per = penalidade_conflito_periodo(individual, expanded_disciplines, slot_mapping)
    
    # ========================================================================
    # CÁLCULO DAS PENALIDADES DE QUALIDADE DA GRADE
    # ========================================================================
    pen_frag = penalidade_fragmentacao_disciplina(spread_info)
    pen_pulv = penalidade_pulverizacao_semanal(spread_info)
    pen_salto = penalidade_salto_temporal(saltos_info)
    
    # ========================================================================
    # CÁLCULO DAS PENALIDADES DE OTIMIZAÇÃO
    # ========================================================================
    pen_conc = penalidade_concentracao(distribuicao)
    pen_lac = penalidade_lacuna(individual, expanded_disciplines, slot_mapping, disciplinas_unicas)
    
    # ========================================================================
    # CÁLCULO DAS PENALIDADES DE OVERLOAD E BLOCOS INCOMPLETOS
    # ========================================================================
    pen_overload = penalidade_overload_sequencial(blocos_info)
    pen_incompleto = penalidade_blocos_incompletos(blocos_info)
    
    # ========================================================================
    # CÁLCULO DAS BONIFICAÇÕES
    # ========================================================================
    bonus_seq = bonificacao_aulas_sequenciais(blocos_info)
    
    # ========================================================================
    # CÁLCULO DO FITNESS TOTAL
    # ========================================================================
    fitness = (BASE_SCORE 
               - pen_prof 
               - pen_per 
               - pen_frag 
               - pen_pulv 
               - pen_salto 
               - pen_conc 
               - pen_lac 
               - pen_overload 
               - pen_incompleto 
               + bonus_seq)
    
    # ========================================================================
    # ANÁLISE DE BLOCOS CONSECUTIVOS (para estatísticas adicionais)
    # ========================================================================
    # (blocos_info já calculado anteriormente)
    
    # Contar totais de blocos
    total_blocos_ideais = sum(info['blocos_ideais'] for info in blocos_info.values())
    total_blocos_overload = sum(info['blocos_overload'] for info in blocos_info.values())
    total_aulas_isoladas = sum(info['aulas_isoladas'] for info in blocos_info.values())
    
    # ========================================================================
    # RETORNAR DICIONÁRIO COMPLETO COM TODAS AS MÉTRICAS
    # ========================================================================
    return {
        # Fitness total
        'fitness': fitness,
        'base_score': BASE_SCORE,
        
        # Penalidades críticas
        'penalidade_professor': pen_prof,
        'penalidade_periodo': pen_per,
        
        # Penalidades de qualidade da grade
        'penalidade_fragmentacao': pen_frag,
        'penalidade_pulverizacao': pen_pulv,
        'penalidade_salto_temporal': pen_salto,
        
        # Penalidades de otimização
        'penalidade_concentracao': pen_conc,
        'penalidade_lacuna': pen_lac,
        
        # Penalidade de overload e blocos incompletos
        'penalidade_overload': pen_overload,
        'penalidade_blocos_incompletos': pen_incompleto,
        
        # Bonificações
        'bonificacao_sequencial': bonus_seq,
        
        # Estatísticas de blocos consecutivos
        'blocos_ideais': total_blocos_ideais,
        'blocos_overload': total_blocos_overload,
        'aulas_isoladas': total_aulas_isoladas
    }
