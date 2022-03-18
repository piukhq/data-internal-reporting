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

df_PC = query_functions.QueryGroup("""
SELECT pca.id AS pc_id,  u.id AS u_id, u.client_id, pca.created, pc.name
FROM payment_card_paymentcardaccount pca
LEFT JOIN ubiquity_paymentcardaccountentry upa ON upa.payment_card_account_id = pca.id
LEFT JOIN "user" u ON u.id = upa.user_id
LEFT JOIN payment_card_paymentcard pc ON pc.id = pca.payment_card_id
WHERE client_id LIKE 'neik%' AND u.id > 500000
""", "created", "name", "u_id", "2018-01-01","2022-05-01")

print(df_PC[:5])
df_PC.rename(columns={
        "created": "Creation Date",
        "u_id": "Total User Count",
        "name": "Card Issuer"}
                 ,inplace=True)
dff_PC_table = df_PC.groupby(['Card Issuer'])['Total User Count'].sum().reset_index()

#%%
# ------------------------------------------------------------------------------
# App layout - everything in the dash goes in here including the HTML
layout = dbc.Container([

    dbc.Row([
        dbc.Col(
                [
                html.H2("Total Payment Cards Created by Issuer",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'}),
                html.Br(),
                dash_table.DataTable(
                    dff_PC_table.to_dict('records'),
                    [{"name": i, "id": i} for i in dff_PC_table.columns], 
                    id='PC_by_card_issuer',
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
                dcc.Dropdown(id="slct_year_pc",
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
                html.Div(id='output_container_pc', children=[]),
                ],
            xs=12, sm=12, md=12, lg=6, xl=6
            )
        ]),

    dbc.Row([
        dbc.Col(
            [
                html.H2(id = 'bar_graph_title_pc', children=[]),
                dcc.Graph(id='PC_by_issuer', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2(id = 'pie_graph_title_pc', children=[]),
                dcc.Graph(id='Pie_by_issuer_pc', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around'),
], fluid=True)



# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container_pc', component_property='children'),
     Output(component_id='PC_by_issuer', component_property='figure'),
     Output(component_id='Pie_by_issuer_pc', component_property='figure'),
     Output(component_id='bar_graph_title_pc', component_property='children'),
     Output(component_id='pie_graph_title_pc', component_property='children')],
    [Input(component_id='slct_year_pc', component_property='value')]
)
def update_graph(option_slctd):
    print(option_slctd)
    print(type(option_slctd))

    container = f"The year chosen by user was: {option_slctd}"
    bar_title = f"Payment Cards Created by Day ({option_slctd})"
    pie_title = f"Payment Cards Pie Chart ({option_slctd})"

    dff_PC = df_PC.copy()
    dff_PC['Creation Date'] = pd.to_datetime(dff_PC['Creation Date'])
    dff_PC['Year'] = df_PC['Creation Date'].astype(str).str[:4]
    dff_PC['Year'] = dff_PC['Year'].astype('int32')
    dff_PC = dff_PC[dff_PC["Year"] == option_slctd]
    

    # Plotly Express
    fig_bar = px.bar(
        data_frame=dff_PC,
        x='Creation Date',
        y='Total User Count',
        color='Card Issuer',
        hover_data=['Card Issuer', 'Total User Count'],
        template='plotly_dark'
    )
    fig_pie = px.pie(
        data_frame=dff_PC,
        values='Total User Count',
        names='Card Issuer',
        template='plotly_dark'
    )

    return container, fig_bar, fig_pie, bar_title, pie_title #This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns