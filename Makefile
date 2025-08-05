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
# Variables
VENV_DIR ?= .venv
PY       := $(VENV_DIR)/bin/python
PIP      := $(VENV_DIR)/bin/pip
REQ_FILE := requirements.txt

# ─────────────────────────────────────────────────────────────
# Objetivos de alto nivel
.PHONY: env build run plots compare all clean

## crea/actualiza el entorno virtual
env:
	@if [ ! -d $(VENV_DIR) ]; then \
		python -m venv $(VENV_DIR); \
		echo "[+] Entorno creado en $(VENV_DIR)"; \
	fi
	$(PIP) install -U pip
	$(PIP) install -r $(REQ_FILE)

## compila el generador C++ (dos proyectos)
build:
	$(MAKE) -C generator/communityAttachment
	$(MAKE) -C generator/graph_features_sat_v_2_2

## ejecuta toda la batería de experimentos
run: env build
	$(PY) main.py

## genera gráficas y métricas
plots: env
	$(PY) plot_results.py

compare: env
	$(PY) compare_metrics.py

## pipeline completo
all: build run plots compare

## limpia binarios y salidas
clean:
	$(MAKE) -C generator/communityAttachment clean || true
	$(MAKE) -C generator/graph_features_sat_v_2_2 clean || true
	rm -rf $(VENV_DIR)
	rm -rf data/plots/* data/metrics/* data/results/*