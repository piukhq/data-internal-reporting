#%%
from turtle import left, width
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output  # pip install dash (version 2.0.0 or higher)
from supporting_files import query_functions
from app import app
import dash_bootstrap_components as dbc
from supporting_files import env
import psycopg2

df_UA = pd.read_sql("""
SELECT COUNT(*) "Total User Count", DATE(u.date_joined) "Creation Date", ca.name "Channel"
FROM "user" u
LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id
GROUP BY  ca.name, DATE(u.date_joined)
""", psycopg2.connect(
    host=env.hostref,
    database=env.databasenameref,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))

# print(df_UA[:5])

df_vouchers = """SELECT
    jsonb_array_elements(vouchers)->>'date_issued'::TEXT AS issue_date,
    jsonb_array_elements(vouchers)->>'code'::TEXT AS code,
    scheme_scheme.company AS name
FROM
    scheme_schemeaccount
WHERE
    vouchers!= '{}'"""

dff_UA_table = df_UA.groupby(['Channel'])['Total User Count'].sum().reset_index()

#%%
#%%
# ------------------------------------------------------------------------------
# App layout - everything in the dash goes in here including the HTML
layout = dbc.Container([

    dbc.Row([
        dbc.Col(
                [
                html.H2("Users Registered by Channel",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'}),
                html.Br(),
                dash_table.DataTable(
                    dff_UA_table.to_dict('records'),
                    [{"id": i, "name": i} for i in dff_UA_table.columns], 
                    id='UA_by_channel_table',
                    style_cell={'textAlign': 'left',
                        'font-family': 'Roboto, sans-serif', 'fontSize': '25', 'font-weight': 300},
                    style_cell_conditional=[
                        {'if': {'column_id': 'name'},
                            'width': '30%'}],
                    style_header={
                        'backgroundColor': 'rgb(30, 30, 30)',
                        'color': 'white',
                        'border': '1px solid blue' ,
                        'font-family': 'Roboto, sans-serif', 'fontSize': '25', 'font-weight': 700
                        },
                    style_data={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'color': 'white',
                        'border': '1px solid blue' ,
                        'font-family': 'Roboto, sans-serif', 'fontSize': '20', 'font-weight': 300
                        },
                    ),
                ], 
            xs=12, sm=12, md=12, lg=6, xl=6),

        ], justify='around'),

    dbc.Row([
        dbc.Col(
            [
                dcc.Dropdown(id="slct_year_ua",
                    options=[
                        {"label": "2019", "value": 2019},
                        {"label": "2020", "value": 2020},
                        {"label": "2021", "value": 2021},
                        {"label": "2022", "value": 2022}],
                    multi=False,
                    value=2019,
                    style={'width': "40%",
                                      'color': '#212121'},
                    persistence=True,
                    persistence_type='local'
                    ),
                html.Div(id='output_container_ua', children=[]),
                ],
            xs=12, sm=12, md=12, lg=6, xl=6
            )
        ]),

    dbc.Row([
        dbc.Col(
            [
                html.H2("Users Registered by Day"),
                dcc.Graph(id='UA_by_channel', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2("Users by Channel Pie Chart"),
                dcc.Graph(id='UA_pie_by_channel', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around')
], fluid=True)

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container_ua', component_property='children'),
     Output(component_id='UA_by_channel', component_property='figure'),
     Output(component_id='UA_pie_by_channel', component_property='figure')],
    [Input(component_id='slct_year_ua', component_property='value')]
)
def update_graph_ua(option_slctd_ua):
    # print(option_slctd_ua)
    # print(type(option_slctd_ua))

    container_ua = f"The year chosen by user was: {option_slctd_ua}"

    dff_UA = df_UA.copy()
    dff_UA['Creation Date'] = pd.to_datetime(dff_UA['Creation Date'])
    dff_UA['Year'] = df_UA['Creation Date'].astype(str).str[:4]
    dff_UA['Year'] = dff_UA['Year'].astype('int32')
    dff_UA = dff_UA[dff_UA["Year"] == option_slctd_ua]
    

    # Plotly Express
    fig_lin_ua = px.line(
        data_frame=dff_UA,
        x='Creation Date',
        y='Total User Count',
        color='Channel',
        hover_data=['Channel', 'Total User Count'],
        template='plotly_dark'
    )
    fig_pie_ua = px.pie(
        data_frame=dff_UA,
        values='Total User Count',
        names='Channel',
        template='plotly_dark'
    )

    return container_ua, fig_lin_ua, fig_pie_ua #This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns