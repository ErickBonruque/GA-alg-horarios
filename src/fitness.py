"""
Funções de penalidade, bonificação e cálculo de fitness.
"""

from typing import List, Dict, Optional
from collections import defaultdict

from .models import Disciplina, Slot
from .config import (
    BASE_SCORE,
    PESO_CONFLITO_PROFESSOR,
    PESO_CONFLITO_PERIODO,
    PESO_CONCENTRACAO,
    PESO_LACUNA,
    PESO_AULAS_SEQUENCIAIS,
    PESO_FRAGMENTACAO,
    PESO_PULVERIZACAO_SEMANAL,
    PESO_SALTO_TEMPORAL,
    PESO_BLOCO_INCOMPLETO,
    PESO_OVERLOAD_SEQUENCIAL,
    PESO_SOBRECARGA_DIARIA,
    MIN_AULAS_SEQUENCIAIS_IDEAL,
    MAX_AULAS_SEQUENCIAIS_IDEAL,
    THRESHOLD_SALTO_TEMPORAL,
    MAX_AULAS_POR_DIA
)


def penalidade_conflito_professor(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot]
) -> int:
    """
    Penaliza se um professor tem aulas simultâneas.
    
    ATENÇÃO: Esta é uma restrição CRÍTICA e INADMISSÍVEL.
    Um professor não pode ministrar duas aulas diferentes ao mesmo tempo.
    """
    # Mapeia: (professor, dia, inicio, fim) -> lista de disciplinas
    professor_slot_disciplinas = defaultdict(list)
    
    for gene, disc in zip(individual, expanded_disciplines):
        slot = slot_mapping.get(gene)
        if slot:
            key = (disc.professor, slot.dia, slot.inicio, slot.fim)
            professor_slot_disciplinas[key].append(disc.codigo)
    
    penalty = 0
    
    # Para cada combinação (professor, slot), verificar se há múltiplas disciplinas
    for key, disciplinas in professor_slot_disciplinas.items():
        disciplinas_unicas = set(disciplinas)
        
        if len(disciplinas_unicas) > 1:
            # Número de conflitos = número de pares de disciplinas em conflito
            num_conflitos = (len(disciplinas_unicas) * (len(disciplinas_unicas) - 1)) // 2
            penalty += num_conflitos * PESO_CONFLITO_PROFESSOR
    
    return penalty


def penalidade_conflito_periodo(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot]
) -> int:
    """
    Penaliza se disciplinas do mesmo período têm aulas simultâneas.
    
    ATENÇÃO: Esta é uma restrição CRÍTICA e INADMISSÍVEL.
    Duas ou mais disciplinas do mesmo período não podem ocupar o mesmo horário,
    pois os alunos precisariam estar em dois lugares ao mesmo tempo.
    """
    # Mapeia: (periodo, dia, inicio, fim) -> lista de disciplinas nesse slot
    periodo_slot_disciplinas = defaultdict(list)
    
    for gene, disc in zip(individual, expanded_disciplines):
        slot = slot_mapping.get(gene)
        if slot:
            key = (disc.periodo, slot.dia, slot.inicio, slot.fim)
            periodo_slot_disciplinas[key].append(disc.codigo)
    
    penalty = 0
    
    # Para cada combinação (período, slot), verificar se há múltiplas disciplinas
    for key, disciplinas in periodo_slot_disciplinas.items():
        # Se mais de uma disciplina (mesmo código) no mesmo período e slot = CONFLITO
        disciplinas_unicas = set(disciplinas)
        
        if len(disciplinas_unicas) > 1:
            # Número de conflitos = número de pares de disciplinas em conflito
            # Se 2 disciplinas -> 1 conflito; se 3 disciplinas -> 3 conflitos (2+1)
            num_conflitos = (len(disciplinas_unicas) * (len(disciplinas_unicas) - 1)) // 2
            penalty += num_conflitos * PESO_CONFLITO_PERIODO
    
    return penalty


def penalidade_concentracao(
    distribuicao: Dict
) -> int:
    """
    Penaliza se uma disciplina tem muitas aulas no mesmo dia.
    Objetivo: distribuir aulas ao longo da semana.
    """
    penalty = 0
    for codigo, dias in distribuicao.items():
        for dia, indices in dias.items():
            count = len(indices)
            if count > 2:
                penalty += (count - 2) * PESO_CONCENTRACAO
    
    return penalty


def penalidade_lacuna(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot],
    disciplinas_unicas: List[Disciplina]
) -> int:
    """
    Penaliza buracos (gaps) na grade horária de cada período.
    """
    periodo_slots_por_dia = defaultdict(lambda: defaultdict(list))
    
    for gene, disc in zip(individual, expanded_disciplines):
        slot = slot_mapping.get(gene)
        if slot:
            periodo_slots_por_dia[disc.periodo][slot.dia].append(slot.inicio)
    
    penalty = 0
    for periodo, dias in periodo_slots_por_dia.items():
        for dia, horarios in dias.items():
            if len(horarios) > 1:
                horarios_sorted = sorted(set(horarios))
                
                ordem_horarios = [
                    "07:30", "08:20", "09:10", "10:20", "11:10",
                    "13:00", "13:50", "14:40", "15:50", "16:40"
                ]
                
                indices = [ordem_horarios.index(h) for h in horarios_sorted if h in ordem_horarios]
                
                if len(indices) > 1:
                    indices_sorted = sorted(indices)
                    for i in range(len(indices_sorted) - 1):
                        gap = indices_sorted[i + 1] - indices_sorted[i] - 1
                        if gap > 0:
                            penalty += gap * PESO_LACUNA
    
    return penalty


def penalidade_sobrecarga_diaria(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot]
) -> int:
    """
    Penaliza dias com mais de 5 aulas para um mesmo período.
    """
    # Mapeia: (periodo, dia) -> contagem de aulas
    periodo_dia_aulas = defaultdict(lambda: defaultdict(int))
    
    for gene, disc in zip(individual, expanded_disciplines):
        slot = slot_mapping.get(gene)
        if slot:
            periodo_dia_aulas[disc.periodo][slot.dia] += 1
    
    penalty = 0
    
    for periodo, dias in periodo_dia_aulas.items():
        for dia, num_aulas in dias.items():
            if num_aulas > MAX_AULAS_POR_DIA:
                # Penalizar proporcionalmente ao excesso
                excesso = num_aulas - MAX_AULAS_POR_DIA
                penalty += excesso * PESO_SOBRECARGA_DIARIA
    
    return penalty


# ============================================================================
# FUNÇÕES AUXILIARES PARA ANÁLISE DE DISTRIBUIÇÃO DE AULAS
# ============================================================================

def get_daily_distribution(individual: List[int], 
                          expanded_disciplines: List[Disciplina],
                          slot_mapping: Dict[int, Slot]) -> Dict:
    """
    Retorna a distribuição de aulas por disciplina e dia.
    """
    # Ordem de horários para conversão em índices numéricos
    ordem_horarios = [
        "07:30", "08:20", "09:10", "10:20", "11:10",
        "13:00", "13:50", "14:40", "15:50", "16:40"
    ]
    
    # Estrutura: codigo -> dia -> lista de índices de horários
    distribuicao = defaultdict(lambda: defaultdict(list))
    
    # Iterar sobre cada gene (aula) do cromossomo
    for gene, disc in zip(individual, expanded_disciplines):
        slot = slot_mapping.get(gene)
        if slot and slot.inicio in ordem_horarios:
            # Converter horário para índice numérico (0-9)
            idx_horario = ordem_horarios.index(slot.inicio)
            distribuicao[disc.codigo][slot.dia].append(idx_horario)
    
    # Ordenar os índices de horários para cada dia
    for codigo in distribuicao:
        for dia in distribuicao[codigo]:
            distribuicao[codigo][dia].sort()
    
    return dict(distribuicao)


def count_consecutive_blocks(distribuicao: Dict) -> Dict:
    """
    Conta e classifica blocos de aulas consecutivas por disciplina.
    Recebe a distribuição pré-calculada.
    """
    resultado = {}
    
    # Analisar cada disciplina
    for codigo, dias in distribuicao.items():
        blocos_ideais = 0
        blocos_overload = 0
        aulas_isoladas = 0
        total_blocos = 0
        
        # Analisar cada dia
        for dia, indices in dias.items():
            if not indices:
                continue
            
            # Detectar sequências de aulas consecutivas
            i = 0
            while i < len(indices):
                sequencia_count = 1
                j = i
                
                # Contar aulas consecutivas
                while j < len(indices) - 1 and indices[j + 1] == indices[j] + 1:
                    sequencia_count += 1
                    j += 1
                
                # Classificar o bloco
                if sequencia_count == 1:
                    aulas_isoladas += 1
                elif MIN_AULAS_SEQUENCIAIS_IDEAL <= sequencia_count <= MAX_AULAS_SEQUENCIAIS_IDEAL:
                    blocos_ideais += 1
                else:  # sequencia_count > MAX_AULAS_SEQUENCIAIS_IDEAL
                    blocos_overload += 1
                
                total_blocos += 1
                i = j + 1
        
        resultado[codigo] = {
            'blocos_ideais': blocos_ideais,
            'blocos_overload': blocos_overload,
            'aulas_isoladas': aulas_isoladas,
            'total_blocos': total_blocos
        }
    
    return resultado


def compute_discipline_daily_spread(distribuicao: Dict) -> Dict:
    """
    Calcula métricas de fragmentação/pulverização das disciplinas.
    Recebe a distribuição pré-calculada.
    """
    resultado = {}
    
    for codigo, dias in distribuicao.items():
        dias_utilizados = len(dias)
        total_aulas = sum(len(indices) for indices in dias.values())
        
        # Calcular fragmentação: quantas "quebras" existem em cada dia
        total_quebras = 0
        for dia, indices in dias.items():
            if len(indices) <= 1:
                continue
            
            # Contar quantas vezes há um gap entre aulas no mesmo dia
            for i in range(len(indices) - 1):
                if indices[i + 1] != indices[i] + 1:
                    total_quebras += 1
        
        # Fragmentação média por dia
        fragmentacao_media = total_quebras / dias_utilizados if dias_utilizados > 0 else 0
        
        # Pulverização: razão entre dias utilizados e total de aulas
        pulverizacao = dias_utilizados / total_aulas if total_aulas > 0 else 0
        
        resultado[codigo] = {
            'dias_utilizados': dias_utilizados,
            'total_aulas': total_aulas,
            'fragmentacao_por_dia': fragmentacao_media,
            'pulverizacao': pulverizacao
        }
    
    return resultado


def compute_temporal_jump_penalty(distribuicao: Dict) -> Dict:
    """
    Calcula penalidades por saltos temporais exagerados.
    Recebe a distribuição pré-calculada.
    """
    resultado = {}
    
    for codigo, dias in distribuicao.items():
        saltos_detectados = 0
        maior_salto = 0
        dias_com_saltos = []
        
        for dia, indices in dias.items():
            if len(indices) < 2:
                continue
            
            # Verificar a distância entre a primeira e última aula do dia
            distancia_maxima = indices[-1] - indices[0]
            
            # Se a distância for maior que o threshold, considerar salto temporal
            if distancia_maxima > THRESHOLD_SALTO_TEMPORAL:
                saltos_detectados += 1
                dias_com_saltos.append(dia)
                maior_salto = max(maior_salto, distancia_maxima)
        
        resultado[codigo] = {
            'saltos_detectados': saltos_detectados,
            'maior_salto': maior_salto,
            'dias_com_saltos': dias_com_saltos
        }
    
    return resultado


# ============================================================================
# FUNÇÕES DE PENALIDADE E BONIFICAÇÃO
# ============================================================================

def bonificacao_aulas_sequenciais(blocos: Dict) -> int:
    """
    Bonifica quando aulas da mesma disciplina são colocadas em sequência IDEAL.
    Recebe os blocos já calculados.
    """
    bonus = 0
    for codigo, info in blocos.items():
        bonus += info['blocos_ideais'] * PESO_AULAS_SEQUENCIAIS
    return bonus


def penalidade_fragmentacao_disciplina(spread_info: Dict) -> int:
    """
    Penaliza disciplinas com aulas muito fragmentadas.
    Recebe spread_info já calculado.
    """
    penalty = 0
    for codigo, info in spread_info.items():
        if info['fragmentacao_por_dia'] > 0:
            penalty += int(info['fragmentacao_por_dia'] * PESO_FRAGMENTACAO)
    return penalty


def penalidade_pulverizacao_semanal(spread_info: Dict) -> int:
    """
    Penaliza disciplinas com aulas muito pulverizadas.
    Recebe spread_info já calculado.
    """
    penalty = 0
    for codigo, info in spread_info.items():
        pulverizacao = info['pulverizacao']
        if pulverizacao > 0.75:
            fator_penalidade = (pulverizacao - 0.75) * 4
            penalty += int(fator_penalidade * PESO_PULVERIZACAO_SEMANAL)
    return penalty


def penalidade_salto_temporal(saltos_info: Dict) -> int:
    """
    Penaliza saltos temporais exagerados.
    Recebe saltos_info já calculado.
    """
    penalty = 0
    for codigo, info in saltos_info.items():
        if info['saltos_detectados'] > 0:
            penalty += info['saltos_detectados'] * PESO_SALTO_TEMPORAL
            if info['maior_salto'] > THRESHOLD_SALTO_TEMPORAL + 2:
                penalty += PESO_SALTO_TEMPORAL
    return penalty


def penalidade_overload_sequencial(blocos: Dict) -> int:
    """
    Penaliza blocos de aulas com MAIS de 3 aulas consecutivas.
    Recebe os blocos já calculados.
    """
    penalty = 0
    for codigo, info in blocos.items():
        if info['blocos_overload'] > 0:
            penalty += info['blocos_overload'] * PESO_OVERLOAD_SEQUENCIAL
    return penalty


def penalidade_blocos_incompletos(blocos: Dict) -> int:
    """
    Penaliza blocos incompletos.
    Recebe os blocos já calculados.
    """
    penalty = 0
    for info in blocos.values():
        if info['aulas_isoladas'] > 0:
            penalty += info['aulas_isoladas'] * PESO_BLOCO_INCOMPLETO
    return penalty


def evaluate_fitness(
    individual: List[int],
    expanded_disciplines: List[Disciplina],
    slot_mapping: Dict[int, Slot],
    disciplinas_unicas: List[Disciplina]
) -> tuple:
    """
    Calcula o fitness de um indivíduo (solução candidata).
    VERSÃO OTIMIZADA: Calcula estruturas auxiliares apenas uma vez.
    """
    # Começar com pontuação base
    score = BASE_SCORE
    
    # ========================================================================
    # 1. CÁLCULO PRÉVIO DE ESTRUTURAS AUXILIARES (OTIMIZAÇÃO)
    # ========================================================================
    # Calcula distribuição de aulas UMA ÚNICA VEZ
    distribuicao = get_daily_distribution(individual, expanded_disciplines, slot_mapping)
    
    # Calcula blocos consecutivos UMA ÚNICA VEZ
    blocos = count_consecutive_blocks(distribuicao)
    
    # Calcula spread (fragmentação/pulverização) UMA ÚNICA VEZ
    spread_info = compute_discipline_daily_spread(distribuicao)
    
    # Calcula saltos temporais UMA ÚNICA VEZ
    saltos_info = compute_temporal_jump_penalty(distribuicao)
    
    # ========================================================================
    # 2. PENALIDADES CRÍTICAS
    # ========================================================================
    score -= penalidade_conflito_professor(individual, expanded_disciplines, slot_mapping)
    score -= penalidade_conflito_periodo(individual, expanded_disciplines, slot_mapping)
    
    # ========================================================================
    # 3. QUALIDADE DA GRADE (usando estruturas pré-calculadas)
    # ========================================================================
    score -= penalidade_fragmentacao_disciplina(spread_info)
    score -= penalidade_pulverizacao_semanal(spread_info)
    score -= penalidade_salto_temporal(saltos_info)
    
    # ========================================================================
    # 4. OTIMIZAÇÕES
    # ========================================================================
    score -= penalidade_concentracao(distribuicao)
    score -= penalidade_lacuna(individual, expanded_disciplines, slot_mapping, disciplinas_unicas)
    score -= penalidade_sobrecarga_diaria(individual, expanded_disciplines, slot_mapping)
    
    # ========================================================================
    # 5. PENALIDADE DE OVERLOAD
    # ========================================================================
    score -= penalidade_overload_sequencial(blocos)
    score -= penalidade_blocos_incompletos(blocos)

    # ========================================================================
    # 6. BONIFICAÇÕES
    # ========================================================================
    score += bonificacao_aulas_sequenciais(blocos)
    
    return (score,)
