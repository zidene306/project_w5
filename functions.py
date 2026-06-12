"""
functions.py — Shared helper functions for the Vanguard A/B Test project.
Derived from work in:
  - cleaning_exp_web_data_Diana.ipynb
  - clean_up_final_demo_zidene.ipynb
  - Merge_files.ipynb
  - DesignEffectiveness_Diana.ipynb    (group balance / demographics — replaces Clients5steps_vs_others)
  - Error&CompletionRates_Diana.ipynb  (error rate per step + completion rate)
"""

import pandas as pd
import yaml


# ---------------------------------------------------------------------------
# I/O HELPERS
# ---------------------------------------------------------------------------
import csv

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
    Notes
    -----
    Uses csv.Sniffer to auto-detect the delimiter from the file itself.
    ⚠️ DO NOT use this function on files exported from a Windows machine
    (e.g. Zidene's exports): CRLF line endings / BOM break Sniffer's
    detection and can mis-read the delimiter. For those files load with:
        pd.read_csv(path, sep=None, engine='python')
    """
    try:
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[read_file] Config not found: {yaml_path}")
        return None
    file_path = cfg[section][file_key]
    
    # detect separator from the file itself
    with open(file_path, "r") as f:
        sep = csv.Sniffer().sniff(f.readline()).delimiter
    
    return pd.read_csv(file_path, sep=sep, low_memory=False)


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


# ---------------------------------------------------------------------------
# EDA UTILITIES
# ---------------------------------------------------------------------------

import numpy as np


def filter_valid_groups(df: pd.DataFrame, exclude_gender_x: bool = True) -> pd.DataFrame:
    """
    Filter the master DataFrame to include only Control and Test clients,
    optionally removing clients with gendr == 'X'.

    Parameters
    ----------
    df : pd.DataFrame
        Master DataFrame (output of merge_demo_web with Variation filled).
    exclude_gender_x : bool, default True
        If True, also drops rows where gendr == 'X'.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame containing only Control and Test rows.
    """
    out = df[df["Variation"].isin(["Control", "Test"])].copy()
    if exclude_gender_x:
        out = out[out["gendr"] != "X"]
    return out



# ---------------------------------------------------------------------------
# ERROR-RATE & COMPLETION-RATE UTILITIES
# (derived from Error&CompletionRates_Diana.ipynb)
# ---------------------------------------------------------------------------

STEP_ORDER = {"start": 0, "step_1": 1, "step_2": 2, "step_3": 3, "confirm": 4}


def build_error_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect backward-navigation errors within each visit_id session.

    Steps:
      1. Map process_step -> integer (step_num) using STEP_ORDER.
      2. Sort chronologically within each session (visit_id).
      3. Compute step_diff = diff of step_num per visit_id.
      4. Flag the step *before* a backward move as is_error=True
         (shift(-1) inside each group).

    Parameters
    ----------
    df : pd.DataFrame
        Filtered master DataFrame (no_data rows and gendr==X already dropped).
        Must contain: visit_id, process_step, date_time.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with three new columns:
          step_num  : int, numeric step index (0-4)
          step_diff : float, difference from previous step in same session
          is_error  : bool, True if this step was the origin of a backward move
    """
    out = df.copy()
    out["step_num"] = out["process_step"].map(STEP_ORDER)
    out = out.sort_values(["date_time", "visit_id"])
    out["step_diff"] = out.groupby("visit_id")["step_num"].diff()
    out["is_error"] = out.groupby("visit_id")["step_diff"].transform(
        lambda x: (x < 0).shift(-1).fillna(False)
    )
    return out

