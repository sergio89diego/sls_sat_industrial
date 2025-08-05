import matplotlib.pyplot as plt
import pandas as pd
import re
from itertools import cycle
from collections import defaultdict
from tabulate import tabulate

# Analize results file and return a DataFrame
def parse_results_file(filename):
    data = []
    current_section = {}
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Detectar encabezados de sección
            if line.startswith('####################'):
                param = line.strip('#').strip()
                if 'n =' in param:
                    current_section['n'] = int(re.search(r'n = (\d+)', param).group(1))
                elif 'c =' in param:
                    current_section['c'] = int(re.search(r'c = (\d+)', param).group(1))
                elif 'Q =' in param:
                    current_section['Q'] = float(re.search(r'Q = (\d+\.\d+)', param).group(1))
                elif 'Max Flips =' in param:
                    current_section['Max Flips'] = int(re.search(r'Max Flips = (\d+)', param).group(1))
            
            # Analizar líneas de datos
            elif line.startswith('c=') or line.startswith('n=') or line.startswith('p='):
                parts = re.split(r',\s+', line)
                entry = current_section.copy()
                
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key in ['n', 'c', 'max_tries']:
                            entry[key] = int(value)
                        elif key in ['Q', 'p', 'm/n']:
                            entry[key] = float(value)
                        elif key == 'max_flips':
                            entry['max_flips'] = int(value)

                    elif ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'Success Rate':
                            entry['Success Rate'] = float(value.rstrip('%'))
                        elif key == 'Total Flips':
                            entry['Total Flips'] = int(value)
                        elif key == 'Time':
                            entry['Time'] = float(value.split()[0])
                
                data.append(entry)
    
    return pd.DataFrame(data)

# Generate individual subplots and return quantitative metrics
def generate_subplot(ax, group, hue_param, hue_value, fixed_params):
    colors = cycle(plt.cm.tab10.colors)
    markers = cycle(['o', 's', '^', 'D', 'v', 'p', '*', 'h', '8', 'X'])
    
    # Agrupar por el parámetro de hue si es diferente a los parámetros fijos
    plot_param = hue_param if hue_param not in fixed_params else None
    grouped = group.groupby(plot_param) if plot_param else [(None, group)]

    metrics = {
        'all': {},  
        'by_n': defaultdict(dict)  
    }
    
    for (plot_value, subgroup), color, marker in zip(grouped, colors, markers):
        subgroup = subgroup.sort_values('m/n')
        label = f"{plot_param}={plot_value}" if plot_value else "All"
        
        metrics['all'] = {
            'avg_success': group['Success Rate'].mean(),
            'max_success': group['Success Rate'].max(),
            'min_success': group['Success Rate'].min(),
            'avg_time': group['Time'].mean(),
            'avg_total_flips': group['Total Flips'].mean()
        }
        
        critical_points = group[group['Success Rate'] < 50]['m/n']
        if not critical_points.empty:
            metrics['all']['phase_transition'] = critical_points.min()
        
        for n, n_group in subgroup.groupby('n'):
            metrics['by_n'][n] = {
                'avg_success': n_group['Success Rate'].mean(),
                'max_success': n_group['Success Rate'].max(),
                'min_success': n_group['Success Rate'].min(),
                'avg_time': n_group['Time'].mean(),
                'avg_total_flips': n_group['Total Flips'].mean() 
            }
            
            n_critical_points = n_group[n_group['Success Rate'] < 50]['m/n']
            if not n_critical_points.empty:
                metrics['by_n'][n]['phase_transition'] = n_critical_points.min()
        
        ax.plot(
            subgroup['m/n'], 
            subgroup['Success Rate'], 
            label=label,
            color=color,
            marker=marker,
            linestyle='--',
            linewidth=1.5,
            markersize=5
        )
    
    title_parts = []
    for param, value in fixed_params.items():
        if param != hue_param:
            title_parts.append(f"{param}={value}")
    if hue_param in fixed_params:
        title_parts.append(f"{hue_param}={hue_value}")
    
    ax.set_title(", ".join(title_parts), fontsize=10)
    ax.set_xlabel("m/n", fontsize=8)
    ax.set_ylabel("Success Rate (%)", fontsize=8)
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, loc='upper right')

    return metrics, ", ".join(title_parts)

# Generate comparative metrics tables
def generate_metrics_tables(all_metrics, vary_params, output_file=None):
    general_data = []
    detailed_data = []
    
    for config, metrics in all_metrics.items():
        config_parts = []
        for param in vary_params:
            pattern = rf"{param}=([^,)]+)"
            match = re.search(pattern, config)
            if match:
                value = match.group(1)
                param_short = {
                    'max_tries': 'MT',
                    'max_flips': 'MF',
                    'flips_coef': 'FC',
                    'Q': 'Q',
                    'c': 'c',
                    'p': 'p'
                }.get(param, param)
                config_parts.append(f"{param_short}={value}")
        
        modified_config = ", ".join(config_parts)
        
        general_row = {
            'Config': modified_config,
            'AvgSucc': metrics['all']['avg_success'],
            'AvgFlips': metrics['all']['avg_total_flips'],
            'PhaseTr': metrics['all'].get('phase_transition', 'N/A')
        }
        general_data.append(general_row)
        
        for n, n_metrics in metrics['by_n'].items():
            detailed_row = {
                'Config': modified_config,
                'n': n,
                'AvgSucc': n_metrics['avg_success'],
                'AvgFlips': n_metrics['avg_total_flips'],
                'PhaseTr': n_metrics.get('phase_transition', 'N/A')
            }
            detailed_data.append(detailed_row)
    
    df_general = pd.DataFrame(general_data)
    df_detailed = pd.DataFrame(detailed_data)
    
    print("\nGeneral Table (All n combined):")
    print("="*60)
    print(tabulate(
        df_general, 
        headers='keys', 
        tablefmt='psql', 
        showindex=False, 
        floatfmt=".2f",
        colalign=("left",) + ("center",)*3
    ))
    
    print("\nDetailed Table (Breakdown by n):")
    print("="*60)
    print(tabulate(
        df_detailed, 
        headers='keys', 
        tablefmt='psql', 
        showindex=False, 
        floatfmt=".2f",
        colalign=("left", "left") + ("center",)*3)
    )
    
    if output_file:
        base_name = output_file.replace('.txt', '')
        
        general_csv = f"{base_name}_general.csv".replace('\\metrics','\\metrics\\csv')
        df_general.to_csv(general_csv, index=False)
        print(f"\nGeneral table saved as CSV: {general_csv}")

        general_md = f"{base_name}_general.md"
        with open(general_md, 'w') as f:
            f.write(df_detailed.to_markdown(
                index=False, 
                floatfmt=".2f",
                tablefmt="github"
            ))
        print(f"General table saved as Markdown: {general_md}") 
    
        detailed_csv = f"{base_name}_detailed.csv".replace('\\metrics','\\metrics\\csv')
        df_detailed.to_csv(detailed_csv, index=False)
        print(f"Detailed table saved as CSV: {detailed_csv}")
          
        detailed_md = f"{base_name}_detailed.md"
        with open(detailed_md, 'w') as f:
            f.write(df_detailed.to_markdown(
                index=False, 
                floatfmt=".2f",
                tablefmt="github"
            ))
        print(f"Detailed table saved as Markdown: {detailed_md}") 
    
    return df_general, df_detailed

# Generate a grid of plots varying specified parameters
def generate_custom_grid(results_df, experiment_name, plot_file, 
                        vary_params, hue_param="n", fixed_params=None, flips_coef=None,
                        metrics_output_file=None):

    if results_df.empty:
        print("No data to plot.")
        return
    
    filtered_df = results_df.copy()
    if fixed_params:
        for param, value in fixed_params.items():
            if param in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[param] == value]
    
    if flips_coef:
        filtered_df = filtered_df[filtered_df['Max Flips'] == flips_coef * filtered_df['n']]

    if not vary_params:
        print("You must specify at least one parameter to vary.")
        return
    
    if len(vary_params) > 2:
        print("Warning: Only the first 2 parameters to vary will be considered.")
        vary_params = vary_params[:2]
    
    param_values = {}
    for param in vary_params:
        if param != 'flips_coef':
            if param in filtered_df.columns:
                param_values[param] = sorted(filtered_df[param].unique())
            else:
                print(f"Warning: The parameter '{param}' does not exist in the data.")
                return
        else:
            param_values[param] = [1,10,20]
    
    if len(vary_params) == 1:
        num_plots = len(param_values[vary_params[0]])
        cols = min(3, num_plots)
        rows = (num_plots + cols - 1) // cols
    else:
        param1_vals = param_values[vary_params[0]]
        param2_vals = param_values[vary_params[1]]
        rows = len(param1_vals)
        cols = len(param2_vals)
        
        if cols > 3:
            new_rows = rows * ((cols + 2) // 3) 
            rows = new_rows
            cols = min(3, cols)
    
    fig, axes = plt.subplots(
        nrows=rows,
        ncols=cols,
        figsize=(5*cols, 4*rows),
        squeeze=False
    )
    fig.suptitle(experiment_name, fontsize=12, y=1.02)
    
    all_metrics = {}
    
    if len(vary_params) == 1:
        param = vary_params[0]
        for plot_idx, val in enumerate(param_values[param]):
            row = plot_idx // cols
            col = plot_idx % cols
            
            ax = axes[row, col]
                                                
            if 'flips_coef' not in vary_params:
                group = filtered_df[filtered_df[param] == val]
            else:
                group = filtered_df[(filtered_df['Max Flips'] == val * filtered_df['n'])]
            
            if not group.empty:
                fixed = {**fixed_params, param: val}
                metrics, config_name = generate_subplot(ax, group, hue_param, None, fixed)
                all_metrics[config_name] = metrics
            else:
                ax.axis('off')
                
        total_plots = len(param_values[param])
        for plot_idx in range(total_plots, rows*cols):
            row = plot_idx // cols
            col = plot_idx % cols
            axes[row, col].axis('off')
            
    else:
        param1, param2 = vary_params
        param1_vals = param_values[param1]
        param2_vals = param_values[param2]
        
        original_cols = len(param2_vals)
        
        for i, val1 in enumerate(param1_vals):
            for j, val2 in enumerate(param2_vals):
                block_row = i * ((original_cols + 2) // 3)
                pos_in_block = j // 3 
                row = block_row + pos_in_block
                col = j % 3
                
                ax = axes[row, col]
                
                if 'flips_coef' not in vary_params:
                    group = filtered_df[(filtered_df[param1] == val1) & 
                                        (filtered_df[param2] == val2)]
                elif 'flips_coef' == param1:
                    group = filtered_df[(filtered_df[param1] == val2) & 
                                        (filtered_df['Max Flips'] == val1 * filtered_df['n'])]
                else:
                    group = filtered_df[(filtered_df[param1] == val1) & 
                                        (filtered_df['Max Flips'] == val2 * filtered_df['n'])]
                
                if not group.empty:
                    if fixed_params is None:
                        fixed_params = {}
                    fixed = {**fixed_params, param1: val1, param2: val2}
                    metrics, config_name = generate_subplot(ax, group, hue_param, None, fixed)
                    all_metrics[config_name] = metrics
                else:
                    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nPlot saved at: {plot_file}")
    
    if metrics_output_file and all_metrics:
        generate_metrics_tables(all_metrics, vary_params, metrics_output_file)

# Main function to analyze results from a file
def analyze_results(filename):
    df = parse_results_file(filename)
      
    base_name = filename
    if base_name.lower().endswith('.txt'):
        base_name = base_name[:-4]
    plot_file = base_name.replace('results/', 'plots\\') + '.png'
    metrics_output_file = base_name.replace('results/', 'metrics\\') + '.txt'

    generate_custom_grid(
        df,
        experiment_name="Success Rate by Community Size and Randomness",
        plot_file=plot_file,
        vary_params=['Q', 'c'],  # o flips_coef
        # vary_params=['p'],  # o flips_coef
        # vary_params=['max_tries', 'max_flips'],  # o flips_coef
        fixed_params={'p':0.5, 'max_tries': 3, 'flips_coef':10},
        # fixed_params={'max_tries': 3, 'flips_coef':10},
        # fixed_params={'p':0.5, 'Q':0.8, 'c':20},
        # fixed_params={'p':0.5},
        metrics_output_file=metrics_output_file
    )

if __name__ == "__main__":
    filename = r"data/results/results_WalkSAT_community_v02.txt"
    analyze_results(filename)