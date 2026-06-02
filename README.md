# Vanguard A/B Test Analysis

> **Ironhack Data Analytics — Week 5 Project**
> Team: Diana Yule & Zidene

---

## Project Overview

Vanguard, a US-based investment management company, ran a digital A/B test from **March 15 to June 20, 2017** to evaluate whether a redesigned online UI — modernized layout with in-context prompts — improves client experience and process completion rates compared to the traditional interface.

This project analyses the experiment results end-to-end: data cleaning, EDA, KPI definition, hypothesis testing, and Tableau visualizations.

---

## The Experiment

| | |
|---|---|
| **Period** | March 15 – June 20, 2017 |
| **Control group** | Traditional Vanguard online interface |
| **Test group** | New UI with contextual prompts |
| **Process flow** | Start → Step 1 → Step 2 → Step 3 → Confirm |
| **Core question** | Did the new UI produce higher completion rates? |

---

## Repository Structure

```
.
├── README.md
├── config.yaml              # All file paths — single source of truth
├── pyproject.toml           # Dependency declarations
├── uv.lock                  # Pinned dependencies for reproducibility
├── .gitignore
├── functions.py             # Shared helper functions (I/O + cleaning)
├── data/
│   ├── raw/                 # Original unmodified source files
│   │   ├── df_final_demo.txt
│   │   ├── df_final_experiment_clients.txt
│   │   ├── df_final_web_data_pt_1.txt
│   │   └── df_final_web_data_pt_2.txt
│   └── clean/               # Processed, analysis-ready files
│       ├── clean_final_demo.csv
│       └── digfootpring_groups_clean.csv
├── notebooks/
│   ├── cleaning_exp_web_data_Diana.ipynb   # Web data + experiment group cleaning
│   ├── clean_up_final_demo_zidene.ipynb    # Demographics cleaning
│   └── Merge_files.ipynb                  # Final master dataset assembly
└── figures/                 # Plots and visual outputs
```

---

## Datasets

| Dataset | Raw file | Description |
|---|---|---|
| `df_final_demo` | `df_final_demo.txt` | Client demographics: age, gender, tenure, balance, call & login history |
| `df_final_web_data` | `df_final_web_data_pt_1.txt` + `pt_2.txt` | Digital footprints — every client interaction step with timestamp |
| `df_final_experiment_clients` | `df_final_experiment_clients.txt` | Group assignment: Control or Test (NaN = not part of experiment) |

---

## Setup & Installation

### Prerequisites
- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv) for environment management

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/vanguard-ab-test.git
cd vanguard-ab-test

# 2. Create and activate the virtual environment
uv venv
source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
uv sync

# 4. Register the Jupyter kernel
python -m ipykernel install --user --name=venv

# 5. Launch Jupyter
jupyter notebook
```

> All file paths are managed via `config.yaml` — no hardcoded paths in notebooks.

---

## How to Run

Run notebooks **in this order**:

1. `clean_up_final_demo_zidene.ipynb` → cleans demographics, outputs `clean_final_demo.csv`
2. `cleaning_exp_web_data_Diana.ipynb` → cleans web data + attaches group labels, outputs `digfootpring_groups_clean.csv`
3. `Merge_files.ipynb` → joins both clean datasets into the master DataFrame

---

## Data Cleaning Summary

### Demographics (`df_final_demo`)
- **70,609** raw rows; **14 rows** dropped (null `clnt_tenure_yr`)
- **1 missing age** imputed with mean age of female clients
- Output: **70,595 rows**, no nulls

### Web Data (`df_final_web_data`)
- Part 1: **343,141** rows → **2,095 duplicates** removed → **341,046 rows**
- Part 2: **412,264** rows → **8,669 duplicates** removed → **403,595 rows**
- Parts concatenated → **744,641 rows**
- Merged with experiment group file on `client_id` → **443,897 rows**
- **126,662 rows** have `NaN` Variation (clients present in web data but not assigned to a group — retained for reference)

### Master Dataset (`Merge_files.ipynb`)
- Outer join of demographics + web+group data on `client_id`
- **443,897 rows × 14 columns**

---

## Key Tools

| Tool | Purpose |
|---|---|
| Python (Pandas) | Data cleaning, merging, analysis |
| Matplotlib / Seaborn | Visualizations |
| Tableau | Interactive dashboards |
| Jupyter Notebooks | Analysis environment |
| GitHub | Version control & submission |
| Trello | Task management (Kanban) |

---

## Data Source

🔗 [Vanguard A/B Test datasets — Ironhack provided via course portal]

---

## Contributors

| Name | Workstream |
|---|---|
| Diana Yule | Web data cleaning, experiment group merging, master dataset |
| Zidene | Demographics cleaning, dataset assembly |

---

## Project Status

- [x] Data sourcing & raw file setup
- [x] Demographics cleaning (`df_final_demo`)
- [x] Web data cleaning + deduplication
- [x] Experiment group labelling
- [x] Master dataset merge
- [ ] EDA & visualizations
- [ ] KPI definition & performance metrics
- [ ] Hypothesis testing
- [ ] Tableau dashboards
- [ ] Final presentation
