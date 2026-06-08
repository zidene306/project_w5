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


def flag_no_data_variation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace NaN values in the Variation column with the string 'no_data'.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a Variation column that may contain NaN values.

    Returns
    -------
    pd.DataFrame
        DataFrame with NaN Variation replaced by 'no_data'.
    """
    out = df.copy()
    out["Variation"] = np.where(out["Variation"].isnull(), "no_data", out["Variation"])
    return out


def compute_error_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute backwards-navigation (error) rates per step per Variation group.

    An 'error' is defined as any step within a visit_id session where
    process_step regresses to a numerically lower step than the previous one.

    Steps
    -----
    1. Map process_step strings to integers via step_order.
    2. Sort chronologically within each visit_id (date_time first).
    3. Compute step-to-step difference; a negative diff = a backward move.
    4. Attribute the error to the step the user LEFT (where the backward
       move originated) using shift(-1) within each visit_id.
    5. Aggregate mean error rate (%) per Variation x step_num.

    Parameters
    ----------
    df : pd.DataFrame
        Master DataFrame containing at least:
        visit_id, process_step, date_time, Variation columns.
        Only rows where Variation is 'Control' or 'Test' are analysed.

    Returns
    -------
    pd.DataFrame
        Columns: Variation, step_num, error_rate_%
        One row per (Variation, step_num) combination.

    Notes
    -----
    Intentional backwards navigation (e.g. correcting a form entry) is
    counted the same as accidental errors. This metric reflects navigation
    friction rather than pure mistakes.
    """
    step_order = {"start": 0, "step_1": 1, "step_2": 2, "step_3": 3, "confirm": 4}
    work = df[df["Variation"].isin(["Control", "Test"])].copy()
    work["step_num"] = work["process_step"].map(step_order)
    # Chronological order within each session (date_time first, matches notebook).
    work = work.sort_values(["date_time", "visit_id"])
    work["step_diff"] = work.groupby("visit_id")["step_num"].diff()
    # Flag the ORIGINATING step (where the backward move started), not the
    # landing step: shift(-1) within each visit_id group.
    work["is_error"] = work.groupby("visit_id")["step_diff"].transform(
        lambda x: (x < 0).shift(-1).fillna(False)
    )

    result = (
        work.groupby(["Variation", "step_num"])["is_error"]
        .mean()
        .mul(100)
        .round(2)
        .reset_index()
    )
    result.columns = ["Variation", "step_num", "error_rate_%"]
    return result


# ---------------------------------------------------------------------------
# COMPLETION-RATE UTILITIES
# (🤖 extracted from Error&CompletionRates_Diana.ipynb — review before relying on it)
# ---------------------------------------------------------------------------

def add_attempt_number(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add an `attempt_No` column counting funnel attempts chronologically per client.

    A client can run the funnel more than once. An attempt is counted across the
    client's whole history (ignoring visit_id): a new attempt begins at
    step_num == 0 only when the previous step was 'confirm' (4) or it is the
    client's first row, and consecutive 'start' rows collapse to the last one.

    Requires a `step_num` column; if absent it is created from `process_step`.

    Parameters
    ----------
    df : pd.DataFrame
        Master DataFrame with client_id, process_step (or step_num), date_time.

    Returns
    -------
    pd.DataFrame
        Copy of df with an added integer `attempt_No` column.
    """
    step_order = {"start": 0, "step_1": 1, "step_2": 2, "step_3": 3, "confirm": 4}
    out = df.copy()
    if "step_num" not in out.columns:
        out["step_num"] = out["process_step"].map(step_order)

    out = out.sort_values(["client_id", "date_time"]).reset_index(drop=True)
    out["prev_step"] = out.groupby("client_id")["step_num"].shift(1)
    out["new_attempt"] = (out["step_num"] == 0) & (
        (out["prev_step"] == 4) | (out["prev_step"].isna())
    )
    out["next_step"] = out.groupby("client_id")["step_num"].shift(-1)
    out["new_attempt"] = out["new_attempt"] & (out["next_step"] != 0)
    out["attempt_No"] = out.groupby("client_id")["new_attempt"].cumsum()
    out["attempt_No"] = (
        out.groupby("client_id")["attempt_No"].ffill().fillna(0).astype(int)
    )
    return out.drop(columns=["prev_step", "next_step", "new_attempt"])


def compute_completion_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the completion rate per Variation group.

    Completion is measured per ATTEMPT, not per session:
        completion_rate_% = unique clients who finished / total attempts * 100

    A client 'finished' if they reached step_num == 4 (confirm) with is_error
    == False on that step. Errors at earlier steps are allowed.

    Prerequisites
    -------------
    The input must already carry `step_num`, `is_error` (see compute_error_rates'
    flagging logic) and `attempt_No` (see add_attempt_number). Only 'Control' and
    'Test' rows are reported.

    Parameters
    ----------
    df : pd.DataFrame
        Master DataFrame with client_id, Variation, step_num, is_error, attempt_No.

    Returns
    -------
    pd.DataFrame
        Columns: Variation, clients_finished, total_attempts, completion_rate_%
    """
    finish_df = df[(df["step_num"] == 4) & (df["is_error"] == False)]
    finisher_count = (
        finish_df.groupby("Variation")["client_id"].nunique().reset_index()
    )
    finisher_count.columns = ["Variation", "clients_finished"]

    total_attempts = (
        df.groupby(["Variation", "client_id"])["attempt_No"]
        .max()
        .reset_index()
        .groupby("Variation")["attempt_No"]
        .sum()
        .reset_index()
    )
    total_attempts.columns = ["Variation", "total_attempts"]

    completion = finisher_count.merge(total_attempts, on="Variation")
    completion["completion_rate_%"] = (
        completion["clients_finished"] / completion["total_attempts"] * 100
    ).round(2)
    return completion[completion["Variation"].isin(["Control", "Test"])].reset_index(drop=True)
