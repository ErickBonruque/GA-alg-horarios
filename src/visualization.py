"""
Funções de visualização e exportação de horários.
"""

from pathlib import Path
from typing import List, Dict

# Verificar bibliotecas opcionais
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def print_schedule(schedule: List[Dict], fitness_info: Dict):
    """
    Imprime o horário de forma tabular no terminal com métricas detalhadas.
    """
    print("\n" + "=" * 80)
    print("MELHOR HORÁRIO ENCONTRADO")
    print("=" * 80)
    print(f"\n🎯 Fitness Total: {fitness_info['fitness']:.0f}")
    print(f"   Pontuação Base: {fitness_info['base_score']}")
    
    print("\n📊 PENALIDADES CRÍTICAS (maior peso):")
    print(f"   - Conflito de Professor: -{fitness_info['penalidade_professor']}")
    print(f"   - Conflito de Período: -{fitness_info['penalidade_periodo']}")
    
    print("\n🔧 PENALIDADES DE QUALIDADE DA GRADE:")
    print(f"   - Fragmentação de Disciplinas: -{fitness_info['penalidade_fragmentacao']}")
    print(f"   - Pulverização Semanal: -{fitness_info['penalidade_pulverizacao']}")
    print(f"   - Saltos Temporais: -{fitness_info['penalidade_salto_temporal']}")
    
    print("\n⚙️  PENALIDADES DE OTIMIZAÇÃO:")
    print(f"   - Concentração Excessiva: -{fitness_info['penalidade_concentracao']}")
    print(f"   - Lacunas (Gaps): -{fitness_info['penalidade_lacuna']}")
    print(f"   - Blocos Incompletos (aulas isoladas): -{fitness_info['penalidade_blocos_incompletos']}")
    print(f"   - Overload Sequencial (>3 aulas): -{fitness_info['penalidade_overload']}")
    
    print("\n✅ BONIFICAÇÕES:")
    print(f"   + Aulas Sequenciais Ideais (2-3): +{fitness_info['bonificacao_sequencial']}")
    
    print("\n📈 ESTATÍSTICAS DE BLOCOS:")
    print(f"   - Blocos Ideais (2-3 aulas): {fitness_info['blocos_ideais']}")
    print(f"   - Blocos Overload (4+ aulas): {fitness_info['blocos_overload']}")
    print(f"   - Aulas Isoladas: {fitness_info['aulas_isoladas']}")
    print("\n")
    
    periodos = sorted(set(item['periodo'] for item in schedule))
    
    for periodo in periodos:
        period_schedule = [s for s in schedule if s['periodo'] == periodo]
        
        print(f"\n{'─' * 80}")
        print(f"PERÍODO {periodo}")
        print(f"{'─' * 80}\n")
        
        table_data = [
            [
                item['dia'],
                f"{item['inicio']} - {item['fim']}",
                f"{item['codigo']} - {item['disciplina']}",
                item['professor']
            ]
            for item in period_schedule
        ]
        
        headers = ["Dia", "Horário", "Disciplina", "Professor"]
        
        if HAS_TABULATE:
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            print(f"{'Dia':<5} | {'Horário':<13} | {'Disciplina':<27} | {'Professor':<28}")
            print("-" * 80)
            for row in table_data:
                print(f"{row[0]:<5} | {row[1]:<13} | {row[2]:<27} | {row[3]:<28}")


def export_html(schedule: List[Dict], output_path: Path = Path("horario_final.html")):
    """Exporta a grade horária para um arquivo HTML em formato de grade."""
    
    # Criar estrutura de dados organizada por período, dia e horário
    dias_ordem = ['SEG', 'TER', 'QUA', 'QUI', 'SEX']
    periodos = sorted(set(item['periodo'] for item in schedule))
    
    # Obter todos os horários únicos ordenados
    horarios_unicos = sorted(set((item['inicio'], item['fim']) for item in schedule))
    
    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horário - Ciência da Computação UTFPR</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
        }
        h1 { 
            color: #2c3e50; 
            text-align: center; 
            margin-bottom: 30px;
        }
        h2 { 
            color: #34495e; 
            margin-top: 40px; 
            margin-bottom: 20px;
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px; 
        }
        .grade-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 12px 8px; 
            text-align: center;
            min-width: 180px;
        }
        th { 
            background-color: #34495e; 
            color: white; 
            font-weight: bold;
            font-size: 14px;
        }
        th.horario-col {
            background-color: #2c3e50;
            min-width: 100px;
        }
        td {
            font-size: 12px;
            vertical-align: middle;
            height: 70px;
        }
        td.ocupado {
            background-color: #e8f4f8;
            font-weight: 500;
            color: #2c3e50;
            padding: 8px;
        }
        td.vazio {
            background-color: #f9f9f9;
        }
        .disciplina-nome {
            font-weight: bold;
            color: #2980b9;
            font-size: 13px;
            display: block;
            margin-bottom: 4px;
        }
        .professor-nome {
            font-size: 11px;
            color: #555;
            font-style: italic;
            display: block;
        }
    </style>
</head>
<body>
    <h1>Horário - Ciência da Computação UTFPR Santa Helena</h1>
"""
    
    # Gerar grade para cada período
    for periodo in periodos:
        period_schedule = [s for s in schedule if s['periodo'] == periodo]
        
        # Criar mapeamento (horário, dia) -> disciplina
        grade = {}
        for item in period_schedule:
            key = ((item['inicio'], item['fim']), item['dia'])
            if key not in grade:
                grade[key] = []
            grade[key].append(item)
        
        html_content += f"\n    <h2>Período {periodo}</h2>\n"
        html_content += '    <div class="grade-container">\n'
        html_content += "    <table>\n"
        
        # Cabeçalho com dias da semana
        html_content += "        <tr>\n"
        html_content += '            <th class="horario-col">Horário</th>\n'
        for dia in dias_ordem:
            dia_nome = {'SEG': 'Segunda', 'TER': 'Terça', 'QUA': 'Quarta', 
                       'QUI': 'Quinta', 'SEX': 'Sexta'}[dia]
            html_content += f'            <th>{dia_nome}</th>\n'
        html_content += "        </tr>\n"
        
        # Linhas de horários
        for inicio, fim in horarios_unicos:
            html_content += "        <tr>\n"
            html_content += f'            <th class="horario-col">{inicio}<br>{fim}</th>\n'
            
            for dia in dias_ordem:
                key = ((inicio, fim), dia)
                if key in grade:
                    disciplinas = grade[key]
                    cell_content = '<br><br>'.join([
                        f'<span class="disciplina-nome">{d["disciplina"]}</span><br>'
                        f'<span class="professor-nome">{d["professor"]}</span>' 
                        for d in disciplinas
                    ])
                    html_content += f'            <td class="ocupado">{cell_content}</td>\n'
                else:
                    html_content += '            <td class="vazio"></td>\n'
            
            html_content += "        </tr>\n"
        
        html_content += "    </table>\n"
        html_content += "    </div>\n"
    
    html_content += "</body>\n</html>"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nHorário exportado para: {output_path}")


def plot_fitness_evolution(
    best_fitness: List[float],
    avg_fitness: List[float],
    output_path: Path = Path("fitness_evolution.png")
):
    """
    Plota a evolução do fitness ao longo das gerações.
    """
    if not HAS_MATPLOTLIB:
        print("Matplotlib não disponível. Gráfico não será gerado.")
        return
    
    generations = list(range(1, len(best_fitness) + 1))
    
    plt.figure(figsize=(12, 6))
    plt.plot(generations, best_fitness, label='Fitness Melhor', color='green', linewidth=2)
    plt.plot(generations, avg_fitness, label='Fitness Média', color='blue', linewidth=1.5, alpha=0.7)
    
    plt.xlabel('Geração', fontsize=12)
    plt.ylabel('Fitness', fontsize=12)
    plt.title('Evolução do Fitness ao Longo das Gerações', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    print(f"Gráfico salvo em: {output_path}")
    plt.close()
