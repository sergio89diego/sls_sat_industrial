import pandas as pd
import os
from tabulate import tabulate

# Load all CSV files from the specified directory and combine them into a single DataFrame
def load_results(directory):
    all_data = []
    
    for filename in os.listdir(directory):
        if filename.endswith("_general.csv"):
            algorithm = filename.replace("_general.csv", "")
            df = pd.read_csv(os.path.join(directory, filename))
            df['Algorithm'] = algorithm
            all_data.append(df)
    
    if not all_data:
        raise ValueError("No result files found in the specified directory")
    
    return pd.concat(all_data, ignore_index=True)

# Normalize scores for comparison
def normalize_scores(df):
    # df['norm_time'] = 1 / (1 + df['avg_time'])
    
    for col in ['AvgSucc', 'AvgFlips', 'PhaseTr']:
        if col in df.columns:
            df[f'norm_{col}'] = df[col] / df[col].max()
    
    return df

# Calculate composite score based on weights
def calculate_composite_score(df, weights):
    score_components = []
    
    if 'norm_AvgSucc' in df.columns and 'AvgSucc' in weights:
        score_components.append(df['norm_AvgSucc'] * weights['AvgSucc'])
    
    if 'norm_AvgFlips' in df.columns and 'AvgFlips' in weights:
        score_components.append(df['norm_AvgFlips'] * weights['AvgFlips'])
    
    if 'norm_PhaseTr' in df.columns and 'PhaseTr' in weights:
        score_components.append(df['norm_PhaseTr'] * weights['PhaseTr'])

    if not score_components:
        raise ValueError("No hay métricas válidas para calcular la puntuación")
    
    df['Composite_Score'] = sum(score_components)
    return df

# Compare algorithms based on their performance metrics
def compare_algorithms(results_dir, output_file=None, weights=None):
    if weights is None:
        weights = {
            'AvgSucc': 0.4,
            'AvgFlips': 0.2,
            # 'max_success': 0.1,
            'PhaseTr': 0.1,
            # 'avg_time': 0.2
        }
    
    try:
        df = load_results(results_dir)
        df = normalize_scores(df)
        df = calculate_composite_score(df, weights)
        
        comparison_df = df.groupby('Algorithm').agg({
            'AvgSucc': 'mean',
            'AvgFlips': 'mean',
            # 'max_success': 'mean',
            # 'avg_time': 'mean',
            'PhaseTr': 'mean',
            'Composite_Score': 'mean'
        }).sort_values('Composite_Score', ascending=False)
        
        comparison_df = comparison_df.reset_index()
        comparison_df['Rank'] = range(1, len(comparison_df) + 1)
        
        cols = ['Rank', 'Algorithm', 'Composite_Score', 'AvgSucc', 'AvgFlips', 'max_success', 
                'PhaseTr', 'avg_time']
        comparison_df = comparison_df[[c for c in cols if c in comparison_df.columns]]
        
        print("\nComparación de Algoritmos:")
        print("="*90)
        print(tabulate(comparison_df, headers='keys', tablefmt='psql', showindex=False, floatfmt=".2f"))
        
        best_algo = comparison_df.iloc[0]['Algorithm']
        best_score = comparison_df.iloc[0]['Composite_Score']
        print(f"\nBEST ALGORITHM: {best_algo} (Score: {best_score:.2f})")
        
        if output_file:
            # CSV
            csv_file = output_file.replace('.txt', '.csv')
            comparison_df.to_csv(csv_file, index=False)
            print(f"\nResults saved as CSV: {csv_file}")
            
            # LaTeX
            latex_file = output_file.replace('.txt', '.tex')
            with open(latex_file, 'w') as f:
                f.write(comparison_df.to_latex(index=False, float_format=".2f"))
            print(f"Results saved as LaTeX: {latex_file}")
            
            # Markdown
            md_file = output_file.replace('.txt', '.md')
            with open(md_file, 'w') as f:
                f.write(comparison_df.to_markdown(index=False, floatfmt=".2f"))
            print(f"Results saved as Markdown: {md_file}")
        
        return comparison_df
    
    except Exception as e:
        print(f"\nError comparing algorithms: {str(e)}")
        return None

if __name__ == "__main__":
    results_directory = r"data/metrics"
    output_comparison = results_directory + r"/comparation_algorithms.txt"
    
    custom_weights = {
        'AvgSucc': 0.6,  
        'AvgFlips': 0.4,
        # 'max_success': 0.0,
        'PhaseTr': 0.0,
        # 'avg_time': 0.0
    }
    
    comparison_results = compare_algorithms(
        results_dir=results_directory,
        output_file=output_comparison,
        weights=custom_weights
    )