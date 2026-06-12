# Vanguard A/B Test Analysis

> **Ironhack Data Analytics — Week 5 Project**
> Team: Diana Yule & Zidene

---

## Project Overview

Vanguard, a US-based investment management company, ran a digital A/B test from **March 15 – June 20, 2017** to evaluate whether a redesigned online UI improves client experience and process completion rates compared to the traditional interface.

This project analyses the experiment results end-to-end: data cleaning, EDA, KPI definition, hypothesis testing, and Tableau visualizations.

---

## The Experiment

| | |
|---|---|
| **Period** | March 15 – June 20, 2017 |
| **Control group** | Legacy Vanguard online interface (23,527 clients) |
| **Test group** | Redesigned UI with contextual prompts (26,961 clients) |
| **Process flow** | Start → Step 1 → Step 2 → Step 3 → Confirm |
| **Data volume** | 443,897 web interaction events |
| **Primary KPIs** | Completion rate (client level) · Process duration rate |
| **Core question** | Did the new UI produce higher completion rates & improved user experience? |

---

## Repository Structure

```
.
├── README.md
├── config.yaml              # All file paths — single source of truth (input_data / output_data)
├── pyproject.toml           # Dependency declarations
├── uv.lock                  # Pinned dependencies for reproducibility
├── .gitignore
├── functions.py             # Shared helpers: I/O, cleaning, EDA, error & completion-rate utilities
├── data/
│   ├── raw/                 # Original unmodified source files
│   │   ├── df_final_demo.txt
│   │   ├── df_final_experiment_clients.txt
│   │   ├── df_final_web_data_pt_1.txt
│   │   └── df_final_web_data_pt_2.txt
│   └── clean/               # Processed, analysis-ready files
│       ├── clean_final_demo.csv          # cleaned demographics
│       ├── digfootpring_groups_clean.csv # web log + group labels
│       ├── cleaned_dataset.csv           # merged master dataset
│       ├── error_compRate_clean.csv      # event-level data for error/completion KPIs
│       ├── error_compRate_tableau.csv    # trimmed column set exported for Tableau
│       └── finishersOnly_clean.csv       # finishers subset (demographics EDA)
├── notebooks/
│   ├── cleaning_exp_web_data_Diana.ipynb   # Web data + experiment group cleaning
│   ├── clean_up_final_demo_zidene.ipynb    # Demographics cleaning
│   ├── Merge_files.ipynb                   # Final master dataset assembly
│   ├── DesignEffectiveness_Diana.ipynb     # EDA: group balance — demographics, age, tenure, gender
│   ├── Error&CompletionRates_Diana.ipynb   # EDA: error rate per step + completion rate (Control vs Test)
│   └── HypothesisTesting_Diana.ipynb       # Z-tests for completion rate (H1) and error rate (H2)
├── figures/                 # Plots and visual outputs
│   ├── AgeTenure_demographics.png
│   ├── TenureDistribution_boxplot.png
│   ├── completers_demographics.png
│   ├── genderDistribution.png
│   ├── genderDistribution_boxplot.png
│   ├── Average_completion_duration_by_age.png
│   ├── Average_completion_time.png
│   ├── Average_step_duration.png
│   ├── average_step_duration_by gender.png
│   ├── Dropoff_rate_by_group.png
│   └── pairplot_demographics.png

├── Tableau/                 # Tableau workbook
│   └── Error_completionRate.twbx
│   └── porject_w5_completion_Mean.twbx
│   └── Error_completionRate.twbx
│   └── porject_w5_step_by_step_Mean.twbx
└── slides/                  # Final presentation
    └── Vanguard_AB_Test_Presentation.pdf
```

---

## Datasets

| Dataset | Raw file | Description |
|---|---|---|
| `df_final_demo` | `df_final_demo.txt` | Client demographics: age, gender, tenure, balance, call & login history |
| `df_final_web_data` | `df_final_web_data_pt_1.txt` + `pt_2.txt` | Digital footprints — every client interaction step with timestamp |
| `df_final_experiment_clients` | `df_final_experiment_clients.txt` | Group assignment: Control or Test (`no_data` = not part of experiment) |

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

> ⚠️ **Windows-exported files (Zidene's outputs):** CRLF/BOM in those files breaks the project's `read_file()` helper. Load them with `pd.read_csv(path, sep=None, engine='python')` instead.

---

## How to Run

Run notebooks **in this order**:

1. `clean_up_final_demo_zidene.ipynb` → cleans demographics, outputs `clean_final_demo.csv`
2. `cleaning_exp_web_data_Diana.ipynb` → cleans web data + attaches group labels, outputs `digfootpring_groups_clean.csv`
3. `Merge_files.ipynb` → joins both clean datasets into `cleaned_dataset.csv`
4. `DesignEffectiveness_Diana.ipynb` → EDA on group balance (demographics, age, tenure, gender distribution)
5. `Error&CompletionRates_Diana.ipynb` → error rate per step + completion rate per group; exports `error_compRate_clean.csv` and `error_compRate_tableau.csv`
6. `HypothesisTesting_Diana.ipynb` → z-tests on completion rate (H1) and error rate (H2)

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

## EDA Findings

### Group Balance (`DesignEffectiveness_Diana.ipynb`)

The experiment assigned **23,527** clients to Control and **26,961** to Test (excluding `no_data`).

| Metric | Control | Test |
|---|---|---|
| Mean age (yrs) | 47.50 | 47.16 |
| Age std | 15.52 | 15.51 |
| Mean tenure (yrs) | 12.09 | 11.98 |
| Tenure std | 6.88 | 6.84 |

Gender distribution is also near-identical across groups (F ~32%, M ~33%, U ~34%). Both groups are well-balanced across age, tenure, and gender — supporting the validity of the A/B test design.

> **Note:** The Unknown (U) gender segment is the largest group (~34%) and skews ~8 yrs younger; it is **retained** in all KPIs. Clients with `gendr = 'X'` (<0.01% of Test group) are excluded from KPI analysis given the negligible sample size.

### Error & Completion Rates (`Error&CompletionRates_Diana.ipynb`)

**Error** = any backwards step move within a `visit_id` session, attributed to the step the user *left* (origin-flagged via `shift(-1)`, chronological order).

| Step | Control error % | Test error % |
|---|---|---|
| 0 (Start) | 0.00 | 0.00 |
| 1 | 8.46 | 16.57 |
| 2 | 8.41 | 15.48 |
| 3 | 18.88 | 18.43 |
| 4 (Confirm) | 4.63 | 1.82 |
| **Mean of steps** | **8.08** | **10.46** |

The **Test** group backtracks far more on steps 1–2 (≈16% vs ≈8%) — the redesign adds friction early in the flow. At step 3 both jump, with Control highest (18.9%). At the decisive **confirm** step the pattern flips: Test finishes *cleaner* (1.8% vs 4.6%).

#### Completion Rate — two metrics

| Metric | Definition | Control | Test |
|---|---|---|---|
| **`%_finisher_clients`** | Finishers / unique clients in group (**primary**) | 62.45% | 68.04% |
| **`completion_rate_%`** | Finishers / total process attempts (**secondary**) | 71.40% | 81.64% |

`%_finisher_clients` is the primary KPI: the unit of randomisation is the *client*, not the attempt, so this is the correct denominator for comparing group outcomes. `completion_rate_%` is a secondary view useful for per-attempt efficiency; it rises even more in Test because Test clients also retry less often on the confirm step.

### Process Efficiency & Duration

- **Drop-off / conversion:** Control drop-off rate (~34%) is higher than Test (~30%). The biggest drop happens at **Step 1**: Control ~14% vs Test ~9%.
- **Completion time:** Test group is slightly faster across the whole process, but the difference is **not significant**. Males and females show nearly identical average completion times.
- **Age segments:** Both groups follow the same completion-time trend across age bands.
- **Step-by-step duration:** Same tendency for both groups — the later validation steps take the most time.
- **Step time by gender:** First two steps roughly equal; at step 3 females are faster, while males catch up by the final step.

---

## Hypothesis Testing

One-sided z-tests for proportions (manual implementation via `scipy.stats.norm`), plus a two-sample t-test for duration. Significance level **α = 0.05**. Groups confirmed independent (0 overlapping clients).

### H1 — Completion Rate (primary metric: `%_finisher_clients`)

- **H₀:** p_Test ≤ p_Control (redesign has no positive effect)
- **H₁:** p_Test > p_Control (redesign improves completion rate)
- Denominator: unique clients per group (unit of randomisation)
- **Result:** z-stat = **13.1564**, p-value < 0.0001 → **reject H₀**
- Observed gap = **+5.59 pp** (68.04% − 62.45%): the Test group's completion rate is significantly higher than Control's.

### H2 — Error Rate

- **H₀:** error_Test ≤ error_Control (redesign does not increase errors)
- **H₁:** error_Test > error_Control (redesign increases errors)
- Denominator: all step rows in steps 1–4 per group (where backward navigation is possible)
- **Result:** p_Test = **13.57%**, p_Control = **10.21%**, z-stat = **23.7421**, p-value < 0.0001 → **reject H₀**
- The Test group's error rate is significantly higher than Control's (**+3.36 pp**).

### H3 — Completion Time

- **H₀:** mean_duration_Test = mean_duration_Control
- **H₁:** mean_duration_Test < mean_duration_Control
- Test: two-sample t-test
- **Result:** p-value = **0.37** → **fail to reject H₀**: insufficient evidence that the Test group completes the process faster.

> All proportion tests used `scipy.stats.norm` with a manual z-statistic and one-sided p-value (`1 - norm.cdf(z_stat)`). `nobs` is set to unique clients (H1) / step rows (H2) per group — never total attempts mixed with clients, to avoid pseudoreplication.

---

## Conclusions & Recommendations

- ✅ **New UI lifts completion.** Test clients finish **+5.6 pp** more often than Control at the client level; per-attempt rate also rises (81.64% vs 71.40%). Statistically confirmed (H1).
- ✅ **Cleaner confirm step.** Test drops confirm-step errors to **1.82%** vs **4.63%** — users commit more confidently at the decisive final step.
- ⚠️ **Higher early-funnel friction.** Step 1–2 error rates nearly double in Test (~16% vs ~8%); overall error rate is significantly higher (H2). Users explore/backtrack more with the new interface.
- ➖ **Same process speed.** No significant difference in completion time between groups (H3).

**Recommendation:** 🚀 **Deploy** the redesign for the completion gain, but 🔍 **investigate** the Steps 1–2 friction — A/B test the UX copy and contextual prompts to reduce early backtracking.

---

## Key Tools

| Tool | Purpose |
|---|---|
| Python (Pandas) | Data cleaning, merging, analysis |
| Matplotlib / Seaborn | Visualizations |
| Tableau | Interactive dashboards (`Tableau/Error_completionRate.twbx`) |
| Jupyter Notebooks | Analysis environment |
| GitHub | Version control & submission |
| Trello | Task management (Kanban) |

---

## Data Source

🔗 Vanguard A/B Test datasets — Ironhack provided via course portal

---

## Presentation

🔗 **Google Slides:** https://docs.google.com/presentation/d/1gpLTHCmwkclnOi78ShSA-Dw4ycLCLS4dUNSVCDYH5Pk/edit
📄 **Local copy:** `slides/Vanguard_AB_Test_Presentation.pdf` (15 slides)
