# TFM – Búsqueda Estocástica en 3‑SAT

Repositorio que acompaña al Trabajo Fin de Máster «Búsqueda estocástica en instancias SAT pseudo‑industriales».  Contiene:

- **Algoritmos** (Python) – `algorithms/`
- **Generador C++** (submódulo) – `generator/`
- **Scripts de ejecución y análisis** – `main.py`, `modules/experiment_runner_parallel.py`, `modules/plot_results.py`, `modules/compare_metrics.py`
- **Datos** – `data/` (vacío: se rellena al ejecutar los experimentos)

---

## 1 · Clonado y submódulos

```bash
git clone https://github.com/sergio89diego/sls_sat_industrial.git
cd tfm-sls-sat
# descarga el generador C++ como submódulo
git submodule update --init --recursive
```

---

## 2 · Entorno

Crea el entorno a partir de requirements.txt` (Python ≥ 3.10):

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

---

## 3 · Compilar el generador

El submódulo incluye dos proyectos con Makefile.  Compílalos de forma independiente:

```bash
# (1) Fórmulas con estructura comunitaria
cd generator/communityAttachment
make

# (2) Cálculo de métricas de grafo
cd ../graph_features_sat_v_2_2
make

# vuelve a la raíz del repo
cd ../../
```

Esto crea los ejecutables necesarios en cada directorio (`communityAttachment`, `graph_features_sat_v_2_2`).

---

## 4 · Lanzar los experimentos

`main.py` carga la configuración por defecto y llama a `modules/experiment_runner_parallel.py`, que ejecuta los algoritmos en paralelo.

```bash
python main.py          # lanza todos los experimentos definidos dentro de main.py
```

Los resultados se van almacenando en `data/results/` como ficheros TXT.

---

## 5 · Post‑proceso y métricas

1. **Graficar y extraer métricas agregadas**\
   El siguiente comando recorre el TXT seleccionado, genera la figura PNG y almacena tablas CSV/MD en `data/metrics/`:

   ```bash
   python modules/plot_results.py             # ruta de resultados hard‑coded dentro del script
   ```

2. **Comparar algoritmos**\
   Con las métricas ya generadas, obtén la tabla comparativa y sus variantes (CSV, LaTeX, MD):

   ```bash
   python modules/compare_metrics.py          # directorio data/metrics predefinido
   ```

Ajusta rutas o pesos de métricas editando los parámetros en la cabecera de cada script.

---

## 6 · Estructura de carpetas

```
SLS_SAT_INDUSTRIAL/
├── algorithms/            # GSAT, WalkSAT y variantes
├── data/
│   ├── metrics/           # tablas agregadas CSV/MD/TEX
│   ├── plots/             # figuras PNG
│   └── results/           # salidas TXT de los experimentos
├── generator/             # submódulo C++ (instancias + métricas grafo)
├── modules/  
│   ├── plot_results.py           # visualización + métricas
│   ├── compare_metrics.py           # ranking comparativo
│   └── experiment_runner_parallel.py              # lógica de ejecución paralela
├── main.py                # punto de entrada
├── requirements.txt
└── README.md
```

---

### Preguntas frecuentes

- **¿Puedo cambiar los parámetros sin tocar el código?**\
  Sí; edita los diccionarios `experiments` dentro de `main.py` o utiliza tus propios archivos YAML.
- **¿Dónde se definen los pesos para el ranking de algoritmos?**\
  En la cabecera de `compare_metrics.py` (`custom_weights`).
- **¿Por qué mi tabla sale vacía?**\
  Asegúrate de ejecutar primero `plot_results.py`, que genera los CSV intermedios en `data/metrics/`.

---

© 2025 \<Sergio Izquierdo> — licencia MIT salvo el submódulo `generator/`, que mantiene la licencia GPL v3 original.

