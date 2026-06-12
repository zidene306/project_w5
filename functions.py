import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
sys.path.append("../")

import yaml

def clean_final_demo_func(df_final_demo):
    """
    cleans df_final_demo.txt and outputs df_final_demo_cleaned.csv
    """
    df = df_final_demo.copy()
    #drop empty rows
    df = df.dropna(subset = "clnt_tenure_yr", ignore_index = True)
    #replace the missing age value in  clnt_age F
    condition = df["gendr"] == "F"
    #female_df = df_final_demo[condition]
    mean_age_f = df[condition].clnt_age.mean()
    
    df['clnt_age'] = df.clnt_age.fillna(mean_age_f)

##############################################################################
#MERGE DF FUNCTION: cast date_time to date 
##############################################################################
def merge_dfs_funct(df_final_demo, df_final_web_data):
    """
    input: ceaned df_final_demo and df_final_web_data df
    this function cast date_time column into date_time format,
    replaces NaN in Variation column by 'others' and merges the 2 input df and uncapitalize column Variation
    output: df cleaned
    """
    df = df_final_demo.merge(df_final_web_data, on = "client_id", how = "outer")

    #clean date columns
    df.date_time = pd.to_datetime(df.date_time, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce')
    #fillup Variation column empty values with: others
    df["Variation"] = df.Variation.fillna('Others')
    #remove capitalization of column Variation
    df = df.rename(columns = {"Variation" : "variation"})
    df = df.dropna(subset = "clnt_age")
    
    return df

##############################################################################
# Function:  user_id and number of completed steps
##############################################################################
def get_steps_by_client(df):
    """
    input: cleaned df or any processed df from original cleaned df
    Adds column at end with the number of steps completed by client
    """
    df1 = df.copy()
    
    user_step_counts = (df1.groupby(['client_id', 'visit_id'])['process_step'].nunique().rename("n_of_unique_steps"))#.reset_index(drop = True)
    user_step_counts.reset_index()
    df1 = df1.merge(user_step_counts, on=['client_id','visit_id'] , how='left')
    df1["completed_steps"] = df1.n_of_unique_steps.apply(lambda x: "Yes" if x == 5 else "No")
    return df1

##############################################################################
# Function:  Get unique clients with the las step reached per client
##############################################################################
def uniq_clnt_with_last_step_df(df):
    """
    RETURNS a df with the last step, for unique client_id
    """
    df1 = get_steps_by_client(df)
    df1 = df1.sort_values(['client_id', 'visit_id', 'date_time']).reset_index(drop = True)
    keep_last_step_per_client = df1.groupby(['client_id', 'visit_id'])['n_of_unique_steps'].max().rename('last_reached_step')
    df1 = df1.merge(keep_last_step_per_client, on = ['client_id', 'visit_id'], how = 'right')
    df1 = df1.sort_values(['client_id', 'visit_id', 'date_time']).reset_index(drop = True)
    df1 = df1.drop_duplicates(subset = ['client_id'], keep = 'last', ignore_index = True)

    return df1
##############################################################################
def get_compl_duration_df(df):
    """
    input: df
    Used for testing hyposthesis This function takes the processed with columns about total duration & step duration from 'get_process_duration(df)' function
    Output: df with unique clients_ids
    """
    df1 = get_process_duration(df)
    df1 = df1.reset_index(drop=True)
    df1 = df1.sort_values(['client_id', 'visit_id', 'date_time']).reset_index(drop = True)
    df1 = df1[df1["n_of_unique_steps"] == 5]
    #remove duplicates from client_id/visit_id groups
    df1 = df1.drop_duplicates(subset = ['client_id'], keep = "last").reset_index(drop = True)
    
    return df1


##############################################################################
# Function: get completion duration for every client (step and overall)
##############################################################################
def get_process_duration(df):
    """
    Input: cleaned df
    
    The function calculates the step duration and over all duration of the process. Considerations:
    1. step duration: if many start steps, last one is considered
    2. if many confirmation steps, consider the lasr one
    3. duration is calculates considering id_visit
    4. repeated steps duration is considered in all duration of process, as it is considered as an error

    Output: df with:
    1. step duration in days, min and seconds
    """

    dfx = get_steps_by_client(df)
    #define my df columns
    dfx = dfx.loc[: ,['client_id', 'clnt_age',
                           'gendr', 'clnt_age', 'gendr',
                           #'calls_6_mnth_y', 'logons_6_mnth_y',
                           'variation', 'visitor_id', 'visit_id',
                           'date_time',  
                           'process_step','n_of_unique_steps'
                        ]
                     ]
        
    #mapping = {'start': 0, 'step_1': 1, 'step_2': 2, 'step_3': 3, 'confirm': 4}
     #dfx['process_nbr'] = dfx.process_step.map(mapping)
    dfx = dfx.sort_values(['client_id', 'date_time', 'visit_id']).reset_index(drop = True)
        
    #take only the last start times for every step to calculate the step duration: 
    #start step:
    last_start = dfx.loc[dfx['process_step'] == 'start'].groupby(['client_id', 'visit_id'])['date_time'].max().rename('last_start_time')
    
    #Step1, 2, 3:
    last_s1 = dfx.loc[dfx['process_step'] == 'step_1'].groupby(['client_id', 'visit_id'])['date_time'].max().rename('last_step1_time')
    last_s2 = dfx.loc[dfx['process_step'] == 'step_2'].groupby(['client_id', 'visit_id'])['date_time'].max().rename('last_step2_time')
    last_s3 = dfx.loc[dfx['process_step'] == 'step_3'].groupby(['client_id', 'visit_id'])['date_time'].max().rename('last_step3_time')
    #confirm step
    last_confirm = dfx.loc[dfx['process_step'] == 'confirm'].groupby(['client_id', 'visit_id'])['date_time'].max().rename('last_confirm_time')
    
    #merge the series back to the df
    dfx = dfx.merge(last_start, on = ['client_id', 'visit_id'], how = 'left')
    dfx = dfx.merge(last_s1, on = ['client_id', 'visit_id'], how = 'left')
    dfx = dfx.merge(last_s2, on = ['client_id', 'visit_id'], how = 'left')
    dfx = dfx.merge(last_s3, on = ['client_id', 'visit_id'], how = 'left')
    dfx = dfx.merge(last_confirm, on = ['client_id', 'visit_id'], how = 'left')
    #keep only max dates for client/visit list
    dfx = dfx[(dfx['date_time'] >= dfx['last_start_time'])]
    
    #keep only last start time   
    condition_confirm = ((dfx['process_step'] == 'confirm') & (dfx['date_time'] < dfx['last_confirm_time']))
    dfx = dfx[~condition_confirm].reset_index(drop = True)
    condition_st1 = ((dfx['process_step'] == 'step_1') & (dfx['date_time'] < dfx['last_step1_time'])) 
    dfx = dfx[~condition_st1].reset_index(drop = True)
    condition_st2 = ((dfx['process_step'] == 'step_2') & (dfx['date_time'] < dfx['last_step2_time']))
    dfx = dfx[~condition_st2].reset_index(drop = True)
    condition_st3 = ((dfx['process_step'] == 'step_3') & (dfx['date_time'] < dfx['last_step3_time']))
    dfx = dfx[~condition_st3].reset_index(drop = True)
    #keep the last date of confir step
        
    #calculate step duration
    dfx['step_duration'] = dfx.groupby(['client_id', 'visit_id'])['date_time'].diff()
        
    #convert to min and seconds
    dfx['step_duration_min'] = round(dfx['step_duration'].dt.total_seconds()/60, 2)
    dfx['step_duration_sec'] = dfx['step_duration'].dt.total_seconds()
        
    #calculate overall duration for every client
    start_time = dfx.groupby(['client_id', 'visit_id'])['date_time'].transform('min')
    end_time = dfx.groupby(['client_id', 'visit_id'])['date_time'].transform('max')
    dfx['all_steps_duration'] = end_time - start_time
        
    #convert to min and hours
    dfx['all_steps_dur_min'] = round(dfx['all_steps_duration'].dt.total_seconds()/60, 2)
    dfx['all_steps_dur_hr'] = round(dfx['all_steps_duration'].dt.total_seconds()/3600, 3)
    dfx = dfx.sort_values(['client_id', 'date_time', 'visit_id']).reset_index(drop = True)

 
    
    #dfx = dfx.loc[:, ['client_id', 'clnt_age', 'gendr',  
                      #'variation', 'visitor_id', 'visit_id',
                      #'date_time', 'process_step','step_duration', 'step_duration_min',
                      #'step_duration_sec','n_of_unique_steps','all_steps_duration',
                      #'all_steps_dur_hr' 
                      #]
                 #]
    dfx = dfx.loc[:, ~ dfx.columns.duplicated()]
    return dfx

##############################################################################
#H0: test_duration_mean = control_duration_mean.
#H1: test_duration_mean < control_duration_mean.
##############################################################################
def run_test_hypo_duration(df):

    """
    Input: df comple durations
    ### Null Hypothesis: 
    H0: test_duration_mean = control_duration_mean.
    H1: test_duration_mean < control_duration_mean.
    output: stat, p_value
    """
    
    df1 = fn.get_compl_duration_df(df)

    test_duration = df1[df1["variation"] == "Test"]["all_steps_dur_hr"]
    control_duration = df1[df1["variation"] == "Control"]["all_steps_dur_hr"]

    stat, p_value = ttest_ind(
        test_duration,
        control_duration,
        equal_var = False,
        alternative='less'
    )
    if p_value < 0.05:
        print(
        f"Reject H0 (p_value ={p_value:.2f}). "
        "There is sufficient evidence that the mean duration of the Test group is lower than that of the Control group."
    )
    else:
        print(
        f"Fail to reject H0 (p_value ={p_value:.2f}). "
        "There is insufficient evidence that the mean duration of the Test group is lower than that of the Control group."
    )
   
    return stat, p_value
##############################################################################
# Define the Dropoff rates
##############################################################################

def funnel_df(df):

    import pandas as pd

    # Step 1: prepare data
    df1 = get_steps_by_client(df)
    df1 = df1.sort_values(['client_id', 'date_time'])

    # Define correct funnel order
    steps = ['start', 'step_1', 'step_2', 'step_3', 'confirm']

    # Step 2: ensure correct order (VERY IMPORTANT for funnels)
    df1['process_step'] = pd.Categorical(
        df1['process_step'],
        categories=steps,
        ordered=True
    )

    # Step 3: compute number of clients per step & variation
    funnel_all_groups = (
        df1.groupby(
            ['variation', 'process_step'],
            observed=True   # FIXES FutureWarning
        )['client_id']
        .nunique()
        .reset_index()
        .sort_values(['variation', 'process_step'])
    )

    # Step 4: conversion rate per variation
    funnel_all_groups["conversion_rate"] = (
        funnel_all_groups.groupby('variation')['client_id']
        .transform(lambda x: x / x.iloc[0] * 100)
    ).round(2)

    # Step 5: drop-off rate per variation (step-to-step)
    funnel_all_groups["dropoff_rate"] = (
        1 - funnel_all_groups.groupby('variation')['client_id']
        .transform(lambda x: x / x.shift(1))
    ) * 100

    return funnel_all_groups
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

