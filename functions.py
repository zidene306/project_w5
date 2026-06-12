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