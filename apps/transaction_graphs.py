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

# -- Import and clean data (importing csv into pandas)

df_txn, df_active_user = query_functions.QueryGroupHarm("""
select mt.id txn_id, mt.transaction_date txn_d, ls.slug slug, mt.card_token token
FROM matched_transaction mt
INNER JOIN merchant_identifier mi ON mi.id = mt.merchant_identifier_id
INNER JOIN loyalty_scheme ls ON ls.id = mi.loyalty_scheme_id
""", "txn_d", "slug", "txn_id", "token", "2018-01-01","2022-05-01")

print(df_txn[:5])
df_txn.rename(columns={
        "txn_d": "Transaction Date",
        "txn_id": "Transaction Count",
        "slug": "Merchant"}
                 ,inplace=True)

df_active_user.rename(columns={
        "txn_d": "Transaction Date",
        "token": "User Count",
        "slug": "Merchant"}
                 ,inplace=True)

dff_txn_table = df_txn.groupby(['Merchant'])['Transaction Count'].sum().reset_index()

#%%
# ------------------------------------------------------------------------------
# App layout - everything in the dash goes in here including the HTML
layout = dbc.Container([

    dbc.Row([
        dbc.Col(
                [
                html.H2("Total Matched Transactions by Merchant",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'}),
                html.Br(),
                dash_table.DataTable(
                    dff_txn_table.to_dict('records'),
                    [{"name": i, "id": i} for i in dff_txn_table.columns], 
                    id='txn_by_merchant',
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
                dcc.Dropdown(id="slct_year_txn",
                    options=[
                        {"label": "2019", "value": 2019},
                        {"label": "2020", "value": 2020},
                        {"label": "2021", "value": 2021},
                        {"label": "2022", "value": 2022}],
                    multi=False,
                    value=2019,
                    style={'width': "40%"},
                    persistence=True,
                    persistence_type='local'
                    ),
                html.Div(id='output_container_txn', children=[]),
                ],
            xs=12, sm=12, md=12, lg=6, xl=6
            )
        ]),

    dbc.Row([
        dbc.Col(
            [
                html.H2(id = 'bar_graph_title_txn', children=[]),
                dcc.Graph(id='txn_by_merchant', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2(id = 'pie_graph_title_txn', children=[]),
                dcc.Graph(id='Pie_by_merchant_txn', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around'),
    
    dbc.Row([
        dbc.Col(
            [
                html.H2(id = 'active_user_title', children=[]),
                dcc.Graph(id='active_user_bar', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2(id = 'hold1', children=[]),
                dcc.Graph(id='hold2', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around'),
], fluid=True)



# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container_txn', component_property='children'),
     Output(component_id='txn_by_merchant', component_property='figure'),
     Output(component_id='Pie_by_merchant_txn', component_property='figure'),
     Output(component_id='bar_graph_title_txn', component_property='children'),
     Output(component_id='pie_graph_title_txn', component_property='children'),
     Output(component_id='active_user_bar', component_property='figure')],
    [Input(component_id='slct_year_txn', component_property='value')]
)
def update_graph(option_slctd):
    print(option_slctd)
    print(type(option_slctd))

    container = f"The year chosen by user was: {option_slctd}"
    bar_title = f"Matched Transactions by Day ({option_slctd})"
    pie_title = f"Transactions Pie Chart ({option_slctd})"

    dff_txn = df_txn.copy()
    dff_txn['Transaction Date'] = pd.to_datetime(dff_txn['Transaction Date'])
    dff_txn['Year'] = df_txn['Transaction Date'].astype(str).str[:4]
    dff_txn['Year'] = dff_txn['Year'].astype('int32')
    dff_txn = dff_txn[dff_txn["Year"] == option_slctd]

    dff_active_user = df_active_user.copy()
    dff_active_user['Transaction Date'] = pd.to_datetime(dff_active_user['Transaction Date'])
    dff_active_user['Year'] = df_active_user['Transaction Date'].astype(str).str[:4]
    dff_active_user['Year'] = dff_active_user['Year'].astype('int32')
    dff_active_user = dff_active_user[dff_active_user["Year"] == option_slctd]
    

    # Plotly Express
    fig_bar = px.bar(
        data_frame=dff_txn,
        x='Transaction Date',
        y='Transaction Count',
        color='Merchant',
        hover_data=['Merchant', 'Transaction Count'],
        template='plotly_dark'
    )
    fig_pie = px.pie(
        data_frame=dff_txn,
        values='Transaction Count',
        names='Merchant',
        template='plotly_dark'
    )

    fig_bar_active = px.bar(
        data_frame=dff_active_user,
        x='Transaction Date',
        y='User Count',
        color='Merchant',
        hover_data=['Merchant', 'User Count'],
        template='plotly_dark'
    )



    return container, fig_bar, fig_pie, bar_title, pie_title, fig_bar_active #This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns