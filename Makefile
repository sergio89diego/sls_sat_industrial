# Makefile – TFM Búsqueda Estocástica en 3‑SAT
#
# Objetivos principales:
#   make env      → crea/actualiza el entorno Conda
#   make build    → compila el generador C++ (dos directorios)
#   make run      → ejecuta todos los experimentos (main.py)
#   make plots    → genera todas las gráficas (plot_results.py)
#   make compare  → construye la tabla comparativa (compare_metrics.py)
#   make all      → build  + run + plots + compare
#   make clean    → borra binarios C++ y salidas en data/

# ———————————————————————————————
# Variables de usuario (pueden sobre‑escribirse en la línea de comandos):
PY        ?= python
ENV_NAME  ?= tfm-sls
CONDA_ACT ?= conda activate $(ENV_NAME)

# ———————————————————————————————
.PHONY: env build run plots compare all clean

## Crear (o actualizar) el entorno Conda —──────────────────────────────
#  Si el entorno ya existe, simplemente lo actualiza.
env:
	conda env list | grep -q "$(ENV_NAME)" \
		&& (echo "[env] Ya existe: $(ENV_NAME)" ) \
		|| conda env create -f environment.yml -n $(ENV_NAME)
	@echo "[env] Activar con: 'conda activate $(ENV_NAME)'"

## Compilar el generador C++ —───────────────────────────────────────────
build:
	$(CONDA_ACT) && $(MAKE) -C generator/communityAttachment
	$(CONDA_ACT) && $(MAKE) -C generator/graph_features_sat_v_2_2
	@echo "[build] Generador compilado en ambos directorios."

## Ejecutar todos los experimentos definidos en main.py —───────────────
run:
	$(CONDA_ACT) && $(PY) main.py

## Generar gráficas y métricas —────────────────────────────────────────
plots:
	$(CONDA_ACT) && $(PY) plot_results.py

compare:
	$(CONDA_ACT) && $(PY) compare_metrics.py

## Pipeline completo —──────────────────────────────────────────────────
all: build run plots compare
	@echo "[all] Flujo completo finalizado."

## Limpiar artefactos —─────────────────────────────────────────────────
clean:
	 rm -rf data/results/* data/plots/* data/metrics/* || true
	 $(MAKE) -C generator/communityAttachment clean
	 $(MAKE) -C generator/graph_features_sat_v_2_2 clean
	@echo "[clean] Directorios de salida y binarios eliminados."
