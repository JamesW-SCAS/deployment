import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px

# To Do:
# 1) Fix start up bug with chart (initialising issue?)
# 2) Add a tab/link to the assumptions that I've made
# 3) Investigate why I have a float total number of appointments!
# 4) Add a way to split by SCAS/non-SCAS and add £?
# 5) Create Git repo
# 6) Upload to GitHub
# 7) Deploy via Streamlit Community Cloud

DELIBERATE BUG HERE!

# Set the page config to spread across the screen
st.set_page_config(layout='wide')

# Add a sidebar with user controls and functions
with st.sidebar:
    st.header("User inputs")

    # Add a selection box for user to choose between "inward" and "outward"
    selected_direction = st.selectbox("Select demand type",
        options=list(['inward', 'outward']))
    
    # User inputs the number of appointments to move when button clicked
    num_to_move = st.number_input("How many appointments do you want to move?", 
    min_value=0)
    from_hour = st.number_input("FROM which hour of the day should they move?", 
    min_value=0, max_value=23)
    to_hour = st.number_input("Which hour of the day should they move TO?", 
    min_value=0, max_value=23)

    # initialise number of moves counter
    if 'move_counter' not in st.session_state:
        st.session_state.move_counter = 0

    # Define a function to update the tables and charts when button clicked
    def update_charts():
        st.session_state.move_counter += num_to_move
        # **Up to here - need to amend the second dataframe with user moves
        st.session_state.edit_df.loc[from_hour,f"{selected_direction}_demand"]\
            -= num_to_move
        st.session_state.edit_df.loc[to_hour,f"{selected_direction}_demand"]\
            += num_to_move
        
    # Calling a function via a button this way is called a "callback" 
    # and it fixes an issue where the button wasn't responding to the 
    # first click
    st.button("move appointments", on_click = update_charts)

    # Add cohorting rate slider here:
    cohort_num = st.slider(
        "How many passengers per load?",
        value=1.0,  # Default value should be a float
        min_value=0.0,
        max_value=4.0,
        format="%.1f"  # Format string without parentheses)
    )

st.header("PTS tools: effect of demand profile \
    and cohorting on resources and KPIs (v1.2)")
# Set up user input dataframe

col1, col2 = st.columns(2)

df = pd.DataFrame(
 # Fill the dataframe with zeros - can do calculations if row is "None"
 np.zeros((24, 2)),
 columns=['inward_demand', 'outward_demand'],
 dtype='int'
 )

# Make the dataframe editable, NB no need to st.write - it prints automatically
with col1:
    st.markdown("#### Input original demand below, then press the button")
    #df['test'] = df[['inward_demand', 'outward_demand']].max(axis=1) / cohort_num
    input_df = st.data_editor(df)
    input_df['orig_res_req'] = (input_df[['inward_demand', 'outward_demand']]\
        .max(axis=1) / cohort_num).round(1)
    
    
    
    # function to copy the user inputs into a new dataframe for later editing
    def take_user_inputs():
        st.session_state.edit_df = input_df.copy()
        st.session_state.move_counter = 0
        
    # Make a button that calls the take_user_inputs function when clicked
    st.button("Set demand inputs and zero moves counter",
     on_click = take_user_inputs)

    # Draw chart of original demand
    orig_demand_fig = px.bar(input_df,
                        y=['inward_demand', 'outward_demand'],
                        title='Original demand profile',
                        barmode='group')

    orig_demand_fig.update_layout(
        yaxis_title="Number of bookings", xaxis_title="Hour")

    st.plotly_chart(orig_demand_fig)

# initialise the new dataframe that users can reprofile
if 'edit_df' not in st.session_state:
    st.session_state.edit_df = "Inputs not finalised."

# New columns for resource requirement with new profile
st.session_state.edit_df['new_res_req'] = \
    (st.session_state.edit_df[['inward_demand','outward_demand']]\
        .max(axis=1) / cohort_num).round(1)

# New column for change in hourly resource requirement
st.session_state.edit_df['change_in_res'] = st.session_state.edit_df['new_res_req'] - st.session_state.edit_df['orig_res_req']

# Print the new dataframe that will be reprofiled with user input buttons
with col2:
    st.subheader("Re-profiled demand below:")
    st.write(st.session_state.edit_df)
    # Add some new lines to allow for the button offeset and align the two charts
    st.markdown("#### \n")



# GRAPHS HERE
# Initialse the melted dataframe used for charts
if 'edit_df_melted' not in st.session_state:
    st.session_state.edit_df_melted = "Push button to draw charts"

# Make a melted dataframe that I can use to draw a bar chart
# if 'edit_df_melted' in st.session_state:
try:
    st.session_state.edit_df_melted = \
                pd.melt(st.session_state.edit_df.reset_index(),
                id_vars='index', value_vars=['inward_demand',\
                        'outward_demand'], 
                var_name='profile', value_name='journeys')
except:
    st.write("Waiting to draw charts")

# Draw a chart of new demand profile
if 'new_demand_fig' not in st.session_state:
    st.session_state.new_demand_fig = "new_demand_fig goes here"
    # st.write(new_demand_fig)

st.session_state.new_demand_fig = px.bar(st.session_state.edit_df_melted,
 x='index', y='journeys', title="Re-profiled demand", barmode='group', 
 color='profile')

st.session_state.new_demand_fig.update_layout(yaxis_title="Number of bookings",
 xaxis_title="Hour")

with col2:
    st.plotly_chart(st.session_state.new_demand_fig)

# METRICS here:
total_appoints = (input_df.values.sum())#.round(0)
# Multiply percentage by -1 as any change is assumed to result in a KPI failure
kpi_effect = (st.session_state.move_counter / total_appoints)*100*-1

# First row of columns
col1, col2, col3 = st.columns(3)
with col1:
    # Show the move counter as a metric
    st.metric(label="Appointments moved",
        value=st.session_state.move_counter)
with col2:
    st.metric(label="Total number of appoinments",
        value=total_appoints)
with col3:
    st.metric(label="KPI percentage change", value = f"{kpi_effect:.1f}%")

#  Second row of columns
col1, col2, col3 = st.columns(3)

orig_res_max = st.session_state.edit_df['orig_res_req'].max()
new_res_max = st.session_state.edit_df['new_res_req'].max()
res_delta = (orig_res_max - new_res_max).round(1)

with col1:
    st.metric(label="Original peak resource req.",
        value=orig_res_max)
with col2:
    st.metric(label="New peak resource req.",
        value=new_res_max)
with col3:
    st.metric(label="Peak resouce saving",
        value=res_delta)

# Resource by hour graph
res_line_fig = px.line(st.session_state.edit_df,
    title="Resources required per hour; Original v's New demand profile",
    y=['orig_res_req','new_res_req'],
    # various line_shape are available - 'spline' smooths the line
    # https://plotly.com/python/line-charts/#interpolation-with-line-plots
    line_shape='spline')

res_line_fig.update_layout(yaxis_title="Number of resources required",
    xaxis_title="Hour")

st.plotly_chart(res_line_fig)

# Change in resource requirement graph
res_delta_fig = px.bar(st.session_state.edit_df,
    title='Change in resource\
 requirement, per hour, due to reprofiling and cohorting',
    y='change_in_res'
    )

res_delta_fig.update_layout(yaxis_title="Change in resource requirement",
    xaxis_title="Hour")

st.plotly_chart(res_delta_fig)