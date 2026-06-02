"""
functions.py — Shared helper functions for the Vanguard A/B Test project.
Derived from work in:
  - cleaning_exp_web_data_Diana.ipynb
  - clean_up_final_demo_zidene.ipynb
  - Merge_files.ipynb
"""

import pandas as pd
import yaml


# ---------------------------------------------------------------------------
# I/O HELPERS
# ---------------------------------------------------------------------------

def read_file(yaml_path: str, section: str, file_key: str) -> pd.DataFrame | None:
    """
    Load a CSV file whose path is defined in config.yaml.

    Parameters
    ----------
    yaml_path : str
        Path to config.yaml (relative to the calling notebook, e.g. '../config.yaml').
    section : str
        Top-level key in the YAML file (e.g. 'input_data' or 'output_data').
    file_key : str
        Key within that section that holds the file path (e.g. 'file1').

    Returns
    -------
    pd.DataFrame or None
        Loaded DataFrame, or None if the config file is missing.
    """
    try:
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[read_file] Config not found: {yaml_path}")
        return None

    file_path = cfg[section][file_key]
    return pd.read_csv(file_path, low_memory=False)


def out_csv(df: pd.DataFrame, yaml_path: str, section: str, file_key: str) -> None:
    """
    Save a DataFrame to the CSV path defined in config.yaml.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    yaml_path : str
        Path to config.yaml.
    section : str
        Top-level YAML key for the output section (e.g. 'output_data').
    file_key : str
        Key within that section that holds the target path (e.g. 'file2').
    """
    try:
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[out_csv] Config not found: {yaml_path}")
        return

    out_path = cfg[section][file_key]
    df.to_csv(out_path, index=False)
    print(f"[out_csv] Saved → {out_path}")


# ---------------------------------------------------------------------------
# DATA CLEANING
# ---------------------------------------------------------------------------

def clean_web_data(pt1: pd.DataFrame, pt2: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the two web-data parts, drop duplicate rows, and reset the index.

    Steps:
      1. Drop exact duplicates from each part independently.
      2. Concatenate vertically (both share identical schema).
      3. Reset index.

    Parameters
    ----------
    pt1, pt2 : pd.DataFrame
        Raw df_final_web_data parts 1 and 2.

    Returns
    -------
    pd.DataFrame
        Combined, deduplicated web interaction log.
        Columns: client_id, visitor_id, visit_id, process_step, date_time.
    """
    pt1_clean = pt1.drop_duplicates()
    pt2_clean = pt2.drop_duplicates()
    combined = pd.concat([pt1_clean, pt2_clean], axis=0).reset_index(drop=True)
    return combined


def merge_experiment_groups(web_df: pd.DataFrame, exp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach Control/Test group labels to the web interaction log.

    Uses an inner join on client_id so only clients present in both
    datasets are retained. Clients with a NaN Variation are kept
    (they exist in the experiment file but have no group assignment).

    Parameters
    ----------
    web_df : pd.DataFrame
        Cleaned web data (output of clean_web_data).
    exp_df : pd.DataFrame
        df_final_experiment_clients with columns [client_id, Variation].

    Returns
    -------
    pd.DataFrame
        Web log enriched with the Variation column.
        Columns: client_id, Variation, visitor_id, visit_id,
                 process_step, date_time.
    """
    return pd.merge(exp_df, web_df, on="client_id")


def clean_final_demo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the client demographics dataset (df_final_demo).

    Steps:
      1. Drop rows where clnt_tenure_yr is null (14 rows in raw data).
      2. Impute the single missing clnt_age value using the mean age
         of female clients (gendr == 'F').

    Parameters
    ----------
    df : pd.DataFrame
        Raw df_final_demo DataFrame.

    Returns
    -------
    pd.DataFrame
        Cleaned demographics DataFrame with no nulls.
    """
    out = df.copy()
    out = out.dropna(subset=["clnt_tenure_yr"]).reset_index(drop=True)
    mean_age_f = out.loc[out["gendr"] == "F", "clnt_age"].mean()
    out["clnt_age"] = out["clnt_age"].fillna(mean_age_f)
    return out


def merge_demo_web(demo_df: pd.DataFrame, web_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join cleaned demographics with the enriched web interaction log.

    Uses an outer join so clients who appear in only one dataset
    are preserved for completeness checks.

    Parameters
    ----------
    demo_df : pd.DataFrame
        Cleaned demographics (output of clean_final_demo).
    web_df : pd.DataFrame
        Web log with group labels (output of merge_experiment_groups).

    Returns
    -------
    pd.DataFrame
        Master DataFrame combining all 14 columns for downstream analysis.
    """
    return pd.merge(demo_df, web_df, on="client_id", how="outer")
