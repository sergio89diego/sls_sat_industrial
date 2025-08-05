# -*- coding: utf-8 -*-
"""
Módulo mejorado para ejecutar experimentos con WalkSAT en paralelo
"""

import os
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from algorithms.WalkSAT import WalkSAT as WalkSAT_random
from algorithms.WalkSAT_v00 import WalkSAT as WalkSAT_community_v00
from algorithms.WalkSAT_v01 import WalkSAT as WalkSAT_community_v01
from algorithms.WalkSAT_v02 import WalkSAT as WalkSAT_community_v02
from algorithms.WalkSAT_v03 import WalkSAT as WalkSAT_community_v03
from algorithms.WalkSAT_v04 import WalkSAT as WalkSAT_community_v04
from algorithms.WalkSAT_v05 import WalkSAT as WalkSAT_community_v05
from algorithms.GSAT import GSAT
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import warnings
warnings.filterwarnings('ignore')

# Global constants
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 2)
CHUNK_SIZE = 10
MAX_RETRIES = 3

# Execute experiments in parallel with a maximum number of retries
def run_single_configuration(config_params, num_seeds=100, algorithm_type='WalkSAT_community', experiment_name='WalkSAT_community'):
    for attempt in range(MAX_RETRIES):
        results = {
            'success_count': 0,
            'total_flips': 0,
            'start_time': time.time()
        }
        
        seeds = random.sample(range(1001), num_seeds)
        for seed in seeds:
            if algorithm_type == 'WalkSAT_community':
                if "v00" in experiment_name:
                    solver_class = WalkSAT_community_v00
                elif "v01" in experiment_name:
                    solver_class = WalkSAT_community_v01
                elif "v02" in experiment_name:
                    solver_class = WalkSAT_community_v02
                elif "v03" in experiment_name:
                    solver_class = WalkSAT_community_v03
                elif "v04" in experiment_name:
                    solver_class = WalkSAT_community_v04
                elif "v05" in experiment_name:
                    solver_class = WalkSAT_community_v05
                else:
                    solver_class = WalkSAT_community_v00

                solver = solver_class(
                    variables=config_params['n'],
                    clauses=int(config_params['m_n'] * config_params['n']),
                    clauseLength=config_params['k'],
                    seed=seed,
                    modularity=config_params['Q'],
                    communities=config_params['c']
                )
                success, tries, flips = solver.solve(
                max_flips=config_params['max_flips'],
                max_tries=config_params['max_tries'],
                probability=config_params['p'] if 'p' in config_params else None 
            )
            elif algorithm_type == 'WalkSAT_random':
                solver = WalkSAT_random(
                    variables=config_params['n'],
                    clauses=int(config_params['m_n'] * config_params['n']),
                    clauseLength=config_params['k'],
                    seed=seed
                )
                success, tries, flips = solver.solve(
                max_flips=config_params['max_flips'],
                max_tries=config_params['max_tries'],
                probability=config_params['p'] if 'p' in config_params else None 
            )
            else:
                solver = GSAT(
                    variables=config_params['n'],
                    clauses=int(config_params['m_n'] * config_params['n']),
                    clauseLength=config_params['k'],
                    seed=seed
                )
                success, tries, flips = solver.solve(
                    max_flips=config_params['max_flips'],
                    max_tries=config_params['max_tries'],
                )
            
            if success:
                results['success_count'] += 1
            results['total_flips'] += flips * tries
        
        results['success_rate'] = (results['success_count'] / num_seeds) * 100
        results['execution_time'] = time.time() - results['start_time']
        return results

# Check if all configurations have been completed
def check_completion_status(results_df, n_values, p_values=None, c_values=None, Q_values=None, m_n_ratios=None, algorithm_type='WalkSAT_community'):
    if results_df.empty:
        return False, set()
    
    required_configs = set()
    for n in n_values:
        for p in p_values:
            if algorithm_type == 'WalkSAT_community':
                for c in c_values:
                    for Q in Q_values:
                        for m_n in m_n_ratios:
                            config_str = f'c={c}, Q={Q}, p={p}, n={n}, m/n={m_n:.1f}'
                            required_configs.add(config_str)
            elif algorithm_type == 'WalkSAT_random':
                for m_n in m_n_ratios:
                    config_str = f'p={p}, n={n}, m/n={m_n:.1f}'
                    required_configs.add(config_str)
            else:
                for m_n in m_n_ratios:
                    config_str = f'n={n}, m/n={m_n:.1f}'
                    required_configs.add(config_str)
    
    completed_configs = set(results_df['Configurations'].unique())
    missing_configs = required_configs - completed_configs
    
    return len(missing_configs) == 0, missing_configs

# Load existing results from a file or return None if the file does not exist
def load_existing_results(results_file):
    if not os.path.exists(results_file):
        return None
    
    data = []
    with open(results_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or 'Success Rate:' not in line:
                continue
            
            try:
                parts = [p.strip() for p in line.split(',')]
                config_data = {}
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=')
                        config_data[key.strip()] = value.strip()
                    elif 'Success Rate:' in part:
                        config_data['Success'] = float(part.split(':')[1].strip('%'))
                    elif 'Total Flips:' in part:
                        config_data['Flips'] = int(part.split(':')[1].strip())
                    elif 'Time:' in part:
                        config_data['Time'] = float(part.split(':')[1].replace('seconds', '').strip())
                
                if 'c' in config_data and 'Q' in config_data:
                    data.append({
                        'Configurations': f"c={config_data['c']}, Q={config_data['Q']}, p={config_data['p']}, n={config_data['n']}, m/n={config_data['m/n']}, max_tries={config_data.get('max_tries', 1)}, max_flips={config_data.get('max_flips', 0)}",
                        'Success Rate': config_data['Success'],
                        'Time (seconds)': config_data.get('Time', 0),
                        'Total Flips': config_data.get('Flips', 0),
                        'Max Tries': int(config_data.get('max_tries', 1)),
                        'Max Flips': int(config_data.get('max_flips', 0)),
                        'c': int(config_data['c']),
                        'Q': float(config_data['Q']),
                        'p': float(config_data['p']),
                        'n': int(config_data['n']),
                        'm/n': float(config_data['m/n'])
                    })
                elif 'p' in config_data:
                    data.append({
                        'Configurations': f"p={config_data['p']}, n={config_data['n']}, m/n={config_data['m/n']}, max_tries={config_data.get('max_tries', 1)}, max_flips={config_data.get('max_flips', 0)}",
                        'Success Rate': config_data['Success'],
                        'Time (seconds)': config_data.get('Time', 0),
                        'Total Flips': config_data.get('Flips', 0),
                        'Max Tries': int(config_data.get('max_tries', 1)),
                        'Max Flips': int(config_data.get('max_flips', 0)),
                        'p': float(config_data['p']),
                        'n': int(config_data['n']),
                        'm/n': float(config_data['m/n'])
                    })
                else:
                    data.append({
                        'Configurations': f"n={config_data['n']}, m/n={config_data['m/n']}, max_tries={config_data.get('max_tries', 1)}, max_flips={config_data.get('max_flips', 0)}",
                        'Success Rate': config_data['Success'],
                        'Time (seconds)': config_data.get('Time', 0),
                        'Total Flips': config_data.get('Flips', 0),
                        'Max Tries': int(config_data.get('max_tries', 1)),
                        'Max Flips': int(config_data.get('max_flips', 0)),
                        'n': int(config_data['n']),
                        'm/n': float(config_data['m/n'])
                    })
            except Exception as e:
                print(f"Error processing line: {line}\nError: {str(e)}")
                continue
    
    return pd.DataFrame(data) if data else None

# Execute the experiment in parallel
def run_experiment_parallel(
    experiment_name,
    n_values,
    p_values=None,
    c_values=None,
    Q_values=None,
    k=3,
    max_tries_values=[3],
    max_flips_values=None,       
    max_flips_coef_values=None,  
    m_n_ratios=np.arange(2.5, 5.5, 0.1),
    num_seeds=100,
    algorithm_type='WalkSAT_community'
):
    os.makedirs('data/results', exist_ok=True)
    
    results_txt_file = f'data/results/results_{experiment_name}.txt'
    
    results_df = load_existing_results(results_txt_file)

    if results_df is None:
        print("\nNo previous results found. Starting experiments from scratch...")
        results_df = pd.DataFrame(columns=[
            'Configurations', 'Success Rate', 'Time (seconds)', 
            'Total Flips', 'Max Tries', 'Max Flies','c', 'Q', 'p', 'n', 'm/n'
        ])
        
        # Escribir encabezado en archivo TXT
        with open(results_txt_file, 'w') as f:
            f.write(f"Experiment: {experiment_name}\n")
            f.write(f"Start date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
    else:
        print("\nPrevious results found. Continuing from the last checkpoint...")

    all_configs = []
    for n in n_values:
        for max_tries in max_tries_values:
            if max_flips_values is not None:
                current_max_flips_list = max_flips_values
            else:
                current_max_flips_list = [coef * n for coef in max_flips_coef_values]
            for max_flips in current_max_flips_list:
                if algorithm_type != 'GSAT':
                    for p in p_values:
                        if algorithm_type == 'WalkSAT_community':
                            for c in c_values:
                                for Q in Q_values:
                                    for m_n in m_n_ratios:
                                        config_str = f'c={c}, Q={Q}, p={p}, n={n}, m/n={m_n:.1f}, max_tries={max_tries}, max_flips={max_flips}'
                                        if not results_df.empty and config_str in results_df['Configurations'].values:
                                            continue
                                        if n == 50 and c in [20,30]:
                                            continue
                                        all_configs.append({
                                            'config_str': config_str,
                                            'params': {
                                                'n': n,
                                                'p': p,
                                                'c': c,
                                                'Q': Q,
                                                'k': k,
                                                'max_tries': max_tries,
                                                'max_flips': max_flips,
                                                'm_n': m_n
                                            }
                                        })
                        else:
                            for m_n in m_n_ratios:
                                config_str = f'p={p}, n={n}, m/n={m_n:.1f}, max_tries={max_tries}, max_flips={max_flips}'
                                if not results_df.empty and config_str in results_df['Configurations'].values:
                                            continue
                                all_configs.append({
                                    'config_str': config_str,
                                    'params': {
                                        'n': n,
                                        'p': p,
                                        'k': k,
                                        'max_tries': max_tries,
                                        'max_flips': max_flips,
                                        'm_n': m_n
                                    }
                                })
                else:
                    for m_n in m_n_ratios:
                        config_str = f'n={n}, m/n={m_n:.1f}, max_tries={max_tries}, max_flips={max_flips}'
                        if not results_df.empty and config_str in results_df['Configurations'].values:
                            continue
                                          
                        all_configs.append({
                            'config_str': config_str,
                            'params': {
                                'n': n,
                                'k': k,
                                'max_tries': max_tries,
                                'max_flips': max_flips,
                                'm_n': m_n
                            }
                        })
    
    if all_configs:
        print(f"\nRunning {len(all_configs)} pending configurations...")
        pbar = tqdm(total=len(all_configs), desc="Progress")
        try:    
            i = 0
            while i < len(all_configs):
                chunk = all_configs[i:i + CHUNK_SIZE]
                i += len(chunk)
                pbar.update(len(chunk))
                
                with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {
                        executor.submit(run_single_configuration, config['params'], num_seeds, algorithm_type, experiment_name): config
                        for config in chunk
                    }
                    
                    for future in as_completed(futures):
                        config = futures[future]
                        
                        try:
                            results = future.result()
                            if algorithm_type == 'WalkSAT_community':
                                new_row = {
                                    'Configurations': config['config_str'],
                                    'Success Rate': results['success_rate'],
                                    'Time (seconds)': results['execution_time'],
                                    'Total Flips': results['total_flips'],
                                    'Max Tries': config['params']['max_tries'],
                                    'Max Flips': config['params']['max_flips'],
                                    'c': config['params']['c'],
                                    'Q': config['params']['Q'],
                                    'p': config['params']['p'],
                                    'n': config['params']['n'],
                                    'm/n': config['params']['m_n']
                                }
                            elif algorithm_type == 'WalkSAT_random':
                                new_row = {
                                    'Configurations': config['config_str'],
                                    'Success Rate': results['success_rate'],
                                    'Time (seconds)': results['execution_time'],
                                    'Total Flips': results['total_flips'],
                                    'Max Tries': config['params']['max_tries'],
                                    'Max Flips': config['params']['max_flips'],
                                    'p': config['params']['p'],
                                    'n': config['params']['n'],
                                    'm/n': config['params']['m_n']
                                }
                            else:
                                new_row = {
                                    'Configurations': config['config_str'],
                                    'Success Rate': results['success_rate'],
                                    'Time (seconds)': results['execution_time'],
                                    'Total Flips': results['total_flips'],
                                    'Max Tries': config['params']['max_tries'],
                                    'Max Flips': config['params']['max_flips'],
                                    'n': config['params']['n'],
                                    'm/n': config['params']['m_n']
                                }
                            results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
                            
                            with open(results_txt_file, 'a') as f:
                                if 'p' in new_row:
                                    f.write(f"{config['config_str']}, Success Rate: {results['success_rate']:.1f}%, "
                                        f"Total Flips: {results['total_flips']}, "
                                        f"Time: {results['execution_time']:.2f} seconds\n")
                                else:
                                    f.write(f"{config['config_str']}, Success Rate: {results['success_rate']:.1f}%, "
                                        f"Total Flips: {results['total_flips']}, "
                                        f"Time: {results['execution_time']:.2f} seconds\n")
                            
                        except Exception as e:
                            print(f"\nError in {config['config_str']}: {str(e)}")
        
        finally:
            pbar.close()
    else:
        print("\nNo pending configurations. All experiments are complete.")
    
    print("Sorting results in the files...")
    clean_and_reorder_results(results_txt_file, results_df)

    return results_df

# Clean and reorder results in the results file
def clean_and_reorder_results(results_file, results_df):
    if 'c' in results_df and 'Q' in results_df:
        group_params = ['n', 'c', 'Q', 'p', 'Max Tries', 'Max Flips']
    elif 'p' in results_df:
        group_params = ['n', 'p', 'Max Tries', 'Max Flips']
    else:
        group_params = ['n', 'Max Tries', 'Max Flips']
    
    varying_params = [param for param in group_params 
                      if len(results_df[param].unique()) > 1]
    
    varying_params.append('m/n') 
    if not varying_params:
        varying_params = ['m/n']
    
    results_df = results_df.sort_values(varying_params)
    
    def write_groups(df, params, file_handle, indent_level=0):
        current_param = params[0] if params else None
        
        if not params:
            for _, row in df.iterrows():
                file_handle.write("    " * indent_level + 
                                f"{row['Configurations']}, Success Rate: {row['Success Rate']:.1f}%, "
                                f"Total Flips: {row['Total Flips']}, Time: {row['Time (seconds)']:.2f} seconds\n")
            return
        
        grouped = df.groupby(current_param, sort=False)
        
        for value, group in grouped:
            if current_param != 'm/n':
                file_handle.write("    " * indent_level + f"\n{'#' * 20} {current_param} = {value} {'#' * 20}\n")
                indent_level = -1
            write_groups(group, params[1:], file_handle, indent_level + 1)

    with open(results_file, 'w') as f:
        f.write(f"Sorted results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n")
        
        write_groups(results_df, varying_params, f)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("End of results\n")
