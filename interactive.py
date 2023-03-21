# %%
# Importing Libraries
import pandas as pd
from sodapy import Socrata
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import streamlit as st
from vega_datasets import data
import altair_viewer
import re

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# %%
# Using Socrata API to get data from CDC website
client = Socrata("data.cdc.gov", None)

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("k62p-6esq", limit=5000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# print all the columns
print(results_df.columns)

# %%
# create a new df with column locationdesc
small_df = results_df[['locationdesc', 'indicator', 'response', 'data_value']]

# remove all the values in locationdesc that are not states and starts with HHS
small_df = small_df[~small_df['locationdesc'].str.contains('HHS')]
small_df.sample(10)

# %%
# change data value column to float
small_df['data_value'] = small_df['data_value'].astype(float)

# drop all the rows with NaN values
small_df = small_df.dropna()
small_df.sample(2)

# %%
# change name of locationdesc column to state
edited_df = small_df.rename(columns={'locationdesc': 'state'})
edited_df.sample(2)

# Using population_engineers_hurricanes() from vega_datasets to get state id
state_id = data.population_engineers_hurricanes()[['state', 'id']]

# load new data 
new_df = pd.read_csv('HI_percent.csv')
# remove the row with United States in Location column
new_df = new_df[new_df['Location'] != 'United States']
# change location column to state
new_df = new_df.rename(columns={'Location': 'state'})
# change state column first letter to uppercase and rest to lowercase
new_df['state'] = new_df['state'].str.title()

# merge state id with merged_df
merged_df = pd.merge(edited_df, state_id, on='state')

# merge new_df with merged_df
merged_df = pd.merge(merged_df, new_df, on='state')

merged_df.sample(2)


# %%
# Using data.us_10m.url to get the url of the states
states_url = data.us_10m.url
states = alt.topo_feature(states_url, 'states')

# %%
# build a text chart for big title for streamlit webpage title is "Health Inequities for disabled people in the US"
title = alt.Chart(merged_df).mark_text(
    align='center',
    baseline='middle',
    fontSize=40,
    fontWeight='bold',
    color='lightblue'
).encode(
    text=alt.value('Health Inequities for Disabled People')
).properties(
    width=880,
    height=100
)

title

# %%
# Define a dropdown for selecting the indicator
indicator_dropdown = alt.binding_select(options=sorted(list(merged_df['indicator'].unique())))
indicator_select = alt.selection_single(fields=['indicator'], bind=indicator_dropdown, name='Select health')

# Define a bar chart with the indicator filter
bar_chart = alt.Chart(merged_df).mark_bar().encode(
    y=alt.Y('response:N', sort='-x', axis=alt.Axis(title='Response from Survey', labelAlign='right', titleFontSize=16, labelFontSize=14)),
    x=alt.X('count():Q', axis=alt.Axis(title='Count', titleFontSize=16)),
    color=alt.Color('response:N', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
    tooltip=['response:N', 'count():Q']
).properties(
    width=980,
    height=450,
    title=alt.TitleParams(text='Disability & Health Indicators', 
                          fontSize=25, offset=10, 
                          anchor='middle', subtitle='(Select an indicator from the dropdown to see the data)', color='lightblue')
).add_selection(
    indicator_select
).transform_filter(
    indicator_select
).interactive()  # Add interactivity to the chart


# Add a text layer to display the data source
source_text = alt.Chart(merged_df).mark_text(
    text="(Source: CDC; Behavioral Risk Factor Surveillance System Data – BRFSS, 2020)",
    fontSize=14,
    font='arial',
    color='gray',
    align='left',
    baseline='bottom',
    dx=170,
    dy=250,
    x=0
)

# Combine the bar chart and the data source text layer
chart_with_source = alt.layer(bar_chart, source_text)

chart_with_source

# create a blank chart to create a space between the two charts
blank = alt.Chart(merged_df).mark_text(
    text="",
    fontSize=14,
    align='center',
).properties(
    width=1080,
    height=50
)

blank

# %%
# Define the layer chart with population data
us_map = alt.Chart(alt.topo_feature(states_url, 'states')).mark_geoshape().project('albersUsa').transform_lookup(
    lookup='id',
    from_=alt.LookupData(data=merged_df, key='id', fields=['Uninsured(%)', 'state', 'Insured(%)', 'Employer/Union(%)'])
).encode(
    alt.Color('Uninsured(%):Q', scale=alt.Scale(scheme='yellowgreenblue')),
    tooltip=[alt.Tooltip('state:N', title='State'), 
            alt.Tooltip('Uninsured(%):Q', title='Uninsured(%)'), 
            alt.Tooltip('Insured(%):Q', title='Insured(%)'),
            alt.Tooltip('Employer/Union(%):Q', title='Employer/Union(%)')]
).properties(
    width=980,
    height=600,
    title=alt.TitleParams(text='Health Insurance Coverage (%) for People with Disability in the United States (2019)', 
                          fontSize=22, offset=10, anchor='middle', subtitle='(Hover over the map to see the data)', color='lightblue')
)

# Add a text layer to display the data source
source_text = alt.Chart(merged_df).mark_text(
    text="(Source: Cornell University Disability Statistics website: www.disabilitystatistics.org)",
    fontSize=14,
    font='arial',
    color='gray',
    align='center',
    baseline='bottom',
    dx=380,
    dy=290,
    x=0
)

# Combine the bar chart and the data source text layer
chart_with_source = alt.layer(us_map, source_text)

chart_with_source


# %%
file = st.file_uploader("IP_Interactive.ipynb", type=["csv", "txt"])

if file is not None:
    df = pd.read_csv(file)
    st.write(df)


