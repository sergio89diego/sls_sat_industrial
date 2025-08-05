from modules.experiment_runner_parallel import run_experiment_parallel
import numpy as np
import multiprocessing
import os

MAX_WORKERS = max(1, multiprocessing.cpu_count() - 2)

def main():
    experiments = [
                {
            "base_name": "GSAT_random_flips&tries",
            "n": [50,100,250,500,1000],
            "k": 3,
            "max_tries_values": [5,50],
            "max_flips_coef_values": None,  # Usar coeficientes
            "max_flips_values": [10,100,250],  # No usar valores fijos
            "m_n_ratios": np.arange(1.0, 5.0, 0.1),
            "num_seeds": 100,
            "algorithm_type": "GSAT" # GSAT, WalkSAT_community, WalkSAT_random
        },

    ]

    for exp_config in experiments:
        experiment_name = exp_config["base_name"]

        print(f"\n{'='*60}")
        print(f"Configuring experiment: {experiment_name}")
        print(f"Available cores: {multiprocessing.cpu_count()}")
        print(f"Workers used: {MAX_WORKERS}")
        print(f"{'='*60}")

        results_txt = f'results/results_{experiment_name}.txt'
        if os.path.exists(results_txt):
            print("\nAnalyzing previous results...")

        c_values = exp_config.get("c", [None])
        Q_values = exp_config.get("Q", [None])

        results = run_experiment_parallel(
            experiment_name=experiment_name,
            n_values=exp_config["n"],
            p_values=exp_config["p"] if exp_config["algorithm_type"] != "GSAT" else None,
            c_values=c_values if exp_config["algorithm_type"] == "WalkSAT_community" else None,
            Q_values=Q_values if exp_config["algorithm_type"] == "WalkSAT_community" else None,
            k=exp_config["k"],
            max_tries_values=exp_config["max_tries_values"],
            max_flips_values=exp_config.get("max_flips_values"),  # Usar get() por si no está definido
            max_flips_coef_values=exp_config.get("max_flips_coef_values"),  # Usar get() por si no está definido
            m_n_ratios=exp_config["m_n_ratios"],
            num_seeds=exp_config["num_seeds"],
            algorithm_type=exp_config["algorithm_type"]
        )



if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
