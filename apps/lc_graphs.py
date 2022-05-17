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


# -- Import and clean data (importing csv into pandas)

df_LC = pd.read_sql("""
SELECT COUNT(*) "Total Card Count", DATE(sa.created) "Creation Date", ss.company "Merchant"
FROM scheme_schemeaccount sa
LEFT JOIN scheme_scheme ss ON ss.id = sa.scheme_id
WHERE company in ('Wasabi', 'Harvey Nichols', 'Iceland', 'ASOS', 'Squaremeal')
GROUP BY  ss.company, DATE(sa.created)
""", psycopg2.connect(
    host=env.hostref,
    database=env.databasenameref,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))

# print(df_LC[:5])

dff_LC_table = df_LC.groupby(['Merchant'])['Total Card Count'].sum().reset_index()

#%%
# ------------------------------------------------------------------------------
# App layout - everything in the dash goes in here including the HTML
layout = dbc.Container([

    dbc.Row([
        dbc.Col(
                [
                html.H2("Total Loyalty Cards Created by Merchant",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'}),
                html.Br(),
                dash_table.DataTable(
                    dff_LC_table.to_dict('records'),
                    [{"name": i, "id": i} for i in dff_LC_table.columns], 
                    id='LC_by_merchant_table',
                    style_cell={'textAlign': 'left',
                        'font-family': 'Roboto, sans-serif', 'fontSize': '25', 'font-weight': 300},
                    style_cell_conditional=[
                        {'if': {'column_id': 'company'},
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
                dcc.Dropdown(id="slct_year",
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
                html.Div(id='output_container', children=[]),
                ],
            xs=12, sm=12, md=12, lg=6, xl=6
            )
        ]),

    dbc.Row([
        dbc.Col(
            [
                html.H2(id = 'bar_graph_title', children=[]),
                dcc.Graph(id='LC_by_merchant', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2(id = 'pie_graph_title', children=[]),
                dcc.Graph(id='Pie_by_merchant', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around'),
], fluid=True)



# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='LC_by_merchant', component_property='figure'),
     Output(component_id='Pie_by_merchant', component_property='figure'),
     Output(component_id='bar_graph_title', component_property='children'),
     Output(component_id='pie_graph_title', component_property='children')],
    [Input(component_id='slct_year', component_property='value')]
)
def update_graph(option_slctd):
    # print(option_slctd)
    # print(type(option_slctd))

    container = f"The year chosen by user was: {option_slctd}"
    bar_title = f"Loyalty Cards Created by Day ({option_slctd})"
    pie_title = f"Loyalty Cards Pie Chart ({option_slctd})"

    dff_LC = df_LC.copy()
    dff_LC['Creation Date'] = pd.to_datetime(dff_LC['Creation Date'])
    dff_LC['Year'] = df_LC['Creation Date'].astype(str).str[:4]
    dff_LC['Year'] = dff_LC['Year'].astype('int32')
    dff_LC = dff_LC[dff_LC["Year"] == option_slctd]
    

    # Plotly Express
    fig_bar = px.bar(
        data_frame=dff_LC,
        x='Creation Date',
        y='Total Card Count',
        color='Merchant',
        hover_data=['Merchant', 'Total Card Count'],
        template='plotly_dark'
    )
    fig_pie = px.pie(
        data_frame=dff_LC,
        values='Total Card Count',
        names='Merchant',
        template='plotly_dark'
    )

    return container, fig_bar, fig_pie, bar_title, pie_title #This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns