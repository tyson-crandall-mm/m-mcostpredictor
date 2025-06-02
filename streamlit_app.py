import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import date, timedelta
import gspread
import warnings

# Suppress warnings for cleaner UX
warnings.filterwarnings("ignore")

# Page Title and Intro
st.title('M&M Machine Learning Cost Proposal Tool')
st.info('This is an Aid, Final Proposals are Subject to Partner Reviews')

# Load data from Google Sheets
sheet_id = "1-RpnD_G0mvaqWINletxUERqeQKOJ6K1ZiYyUqKIA6oU"
gid = "263876729"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

df = pd.read_csv(url)
user_df = df.iloc[:0]  # Empty structure

# Predefine for global safety
project_region = None

# Sidebar inputs
with st.sidebar:
    st.write("# Project Characteristics")

    project_office = st.selectbox('Project Office', 
        ("Akron", "Beachwood", "Cleveland", "MCS", "Wooster"), 
        index=None, 
        placeholder="Location..."
    )

    south = {"FL", "TX", "GA", "SC", "NC", "TN", "VA", "AR", "KY", "AL", "MD", "DC", "PR"}
    northeast = {"NY", "MA", "CT", "NJ", "PA", "ME"}
    midwest = {"IL", "IN", "OH", "MI", "WI", "MO", "IA"}
    west = {"CA", "CO", "WA", "OR", "NV", "AZ", "ID", "MT", "NM", "UT"}

    project_state = st.selectbox('Project State', 
        ("AK", "AR", "AZ", "CA", "CO", "CT", "DC", "FL", "GA", "IA", "ID", "IL", "IN", "KS", 
         "KY", "MA", "MD", "ME", "MI", "MN", "MO", "MT", "NC", "NM", "NV", "NY", "OH", "OK", 
         "OR", "PA", "PR", "SC", "TN", "TX", "VA", "WA", "WI", "WV"), 
        index=None, 
        placeholder="State..."
    )

    def get_region(state):
        if state in south:
            return "South"
        elif state in northeast:
            return "Northeast"
        elif state in midwest:
            return "Midwest"
        elif state in west:
            return "West"
        else:
            return "Unknown"

    if project_state:
        project_region = get_region(project_state)

    client_type = st.selectbox('Client Type', 
        ("Corporation", "Fiduciary", "Individual", "Non-Profit", "Partnership"), 
        index=None, 
        placeholder="Client Type..."
    )

    services = st.multiselect('Proposed Services', [
        "1040 - Large Tax", "1099 Forms", "4868 Extension", "7004 Extension", 
        "7004F Extension for Fiduciary Return", "8868 Extension", "Amended Return Corporate", 
        "Amended Return Individual/Estate", "Annual Return/Report of Employee Benefit Plan", 
        "Corporate Federal Tax Return", "Corporate Income Tax Return", 
        "Corporate State Tax Return", "ERP Utilization or Improvement", "ERP or Other Upgrade", 
        "Estates & Trusts Income Tax Return", "Individual Income Tax Return", "MCS-ECi-DEV", 
        "MCS-Onsites", "MCS-SUPPORT PROJECT", "Ongoing Client Support", 
        "Partnership Income Tax Return", "Payroll - Annual", "Payroll - Quarterly", 
        "Payroll-Monthly", "Payroll- Quarterly", "Quartely Estimates", 
        "Quarterly Estimates - Corporate", "Quarterly Estimates - Individual", 
        "Return of Organization Exempt from Income Tax", "S Corporation Tax Return", 
        "TAX PLANNING", "Tax One Time Only - Corporate", "Tax One Time Only - Individual", 
        "U.S. Gift Tax Return"
    ])

    selected_roles = st.multiselect(
        "Select Seniority of Staff Member(s) on the Project", 
        ["Senior Manager", "Administrator", "Staff", "Director", "Manager", "Officer", "Senior", 
         "Associate", "Senior Executive", "Seasonal", "Owner", "Intern", "Intern PT", 
         "Consultant", "Intern FT"]
    )

    st.write("#### Enter workload percentages (must total 100%)")
    staff_workload = {}
    cols = st.columns(2)
    for idx, role in enumerate(selected_roles):
        with cols[idx % 2]:
            percent = st.number_input(
                f"{role} (%)",
                min_value=0,
                max_value=100,
                step=1,
                key=f"work_{role}"
            )
            staff_workload[role] = percent

    total = sum(staff_workload.values())
    st.markdown(f"**Total Allocated: {total}%**")

    if total < 100:
        st.warning("**Total is less than 100%.**")
    elif total > 100:
        st.error("**Total exceeds 100%. Please adjust the values.**")
    else:
        st.success("**Total is exactly 100%. Ready to proceed!**")

    # Project complexity
    complexity_levels = {1: "Basic", 2: "Easy", 3: "Moderate", 4: "Complex"}
    project_complexity = st.segmented_control(
        "Project Complexity Level", 
        options=complexity_levels.keys(), 
        format_func=lambda option: complexity_levels[option],
        selection_mode="single"
    )

    hour_levels = {
        1: "Extremely Little", 2: "Quite Little", 3: "Little", 4: "Moderate", 
        5: "High", 6: "Quite High", 7: "Extremely High"
    }

    project_hours = st.pills(
        "Project Hours", 
        options=hour_levels.keys(), 
        format_func=lambda option: hour_levels[option],
        selection_mode="single"
    )

    st.warning("""\
    **Project Hours Guide**  
    - Extremely Little: 0 to 1 hours  
    - Quite Little: 1 to 2 hours  
    - Little: 2 to 5 hours  
    - Moderate: 5 to 11 hours  
    - High: 11 to 39 hours  
    - Quite High: 39 to 80 hours  
    - Extremely High: 80+ hours\
    """)

    default_start = date.today()
    default_finish = default_start + timedelta(days=1)
    estimated_dates = st.date_input("Project Estimated Start and Finish Date", value=(default_start, default_finish))

    if isinstance(estimated_dates, tuple) and len(estimated_dates) == 2:
        estimated_start_date, estimated_end_date = estimated_dates
        if estimated_start_date > estimated_end_date:
            st.error("Start date must be before or equal to end date.")
    else:
        st.error("Please select both a start and end date.")

# Logic after sidebar
user_data = {}

if all([
    project_office, project_state, project_region, client_type,
    services, staff_workload, project_complexity, project_hours,
    isinstance(estimated_dates, tuple) and len(estimated_dates) == 2
]):
    user_data = {
        "ProjectOffice": project_office,
        "ProjectState": project_state,
        "ProjectRegion": project_region,
        "ClientType": client_type,
        "Services": services,
        "StaffWorkDistribution": staff_workload,
        "ProjectComplexity": project_complexity,
        "ProjectHours": project_hours,
        "EstimatedDates": estimated_dates
    }

    st.success("All inputs collected successfully!")
    st.json(user_data)

    # Drop column if exists
    if "ActualBudgetAmount" in user_df.columns:
        user_df = user_df.drop(columns="ActualBudgetAmount")

    # Add user input as one-hot encoded row
    new_row = {col: 0 for col in user_df.columns}
    for feature in [project_office, project_state, project_region, client_type]:
        if feature in user_df.columns:
            new_row[feature] = 1

    user_df = pd.concat([user_df, pd.DataFrame([new_row])], ignore_index=True)

else:
    st.warning("Please complete all required fields to generate a project summary.")

# Show updated dataframe
user_df
