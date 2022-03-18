#%%
from turtle import left
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output  # pip install dash (version 2.0.0 or higher)
import query_functions

# -- Import and clean data (importing csv into pandas)
# df = pd.read_csv("intro_bees.csv")

df_LC = query_functions.QueryGroup("""
SELECT sa.id AS sa_id,  u.id AS u_id, u.client_id, sa.created, sa.scheme_id, ss.company
FROM scheme_schemeaccount sa
LEFT JOIN ubiquity_schemeaccountentry usa ON usa.scheme_account_id = sa.id
LEFT JOIN "user" u ON u.id = usa.user_id
LEFT JOIN scheme_scheme ss ON ss.id = sa.scheme_id
WHERE client_id LIKE 'neik%' AND u.id > 500000
""", "created", "company", "u_id", "2018-01-01","2022-05-01")
#%%

dff_LC = df_LC.copy()
dff_LC['created'] = pd.to_datetime(dff_LC['created'])
dff_LC['Year'] = df_LC['created'].astype(str).str[:4]
dff_LC['Year'] = dff_LC['Year'].astype('int32')
dff_LC = dff_LC[dff_LC["Year"] == 2022]

dff_LC_table = df_LC.groupby(['company'])['u_id'].sum().reset_index()
# %%
  # Plotly Express
fig_bar = px.bar(
    data_frame=dff_LC,
    x='created',
    y='u_id',
    color='company',
    hover_data=['company', 'u_id'],
    template='plotly_dark'
)
fig_pie = px.pie(
    data_frame=dff_LC,
    values='u_id',
    names='company',
    template='plotly_dark'
)


LC_table = dff_LC_table.to_dict('records')
LC_table
# %%
