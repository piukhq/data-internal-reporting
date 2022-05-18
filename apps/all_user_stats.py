#%%
from socket import timeout
from turtle import left, width
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output  # pip install dash (version 2.0.0 or higher)
from app import app
import dash_bootstrap_components as dbc
from supporting_files import env
import psycopg2
import datetime


from app import cache
from app import color_mapping
from random import randint
from flask_caching import Cache

TIMEOUT = 60

# %%
#====================Generate column with loop==============================
def generate_headers(dict):
    output = []
    length = len(dict)
    for key in dict:
        output.append(dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5(f"{key}", className="text-center")),
                dbc.CardBody(
                    [
                        html.H3(f"{dict[key]}", className="text-center card-title")
                        
                    ]
                ),
            ], color="dark", inverse=True),
                xs=max(6,12/length), sm=max(6,12/length), md=max(6,12/length), lg=max(3,12/length), xl=max(3,12/length)))
    return output

# %%
layout = dbc.Container([


    dbc.Row([
        dbc.Col(
                [
                html.H2(f"Total Consented Users by Channel",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'})
                ], 
            xs=12, sm=12, md=12, lg=6, xl=6),

        ], justify='around'),
    
    dbc.Row(id = "user_headers",
        children =[]
    ),

    html.Br(),

    dbc.Row([
        dbc.Col(
                [
                html.H2(f"Total Active PLL Loyalty Cards by Merchant",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'})
                ], 
            xs=12, sm=12, md=12, lg=6, xl=6),

        ], justify='around'),
    
    dbc.Row(
        id = "LC_headers",
        children =[]
    ),

    html.Hr(),
    html.Br(),

    dbc.Row([
        dbc.Col(
            [   html.H6("Select dates to filter graphs"),
                dcc.DatePickerRange(
                    id = 'date_picker',
                    month_format='MMMM Y',
                    end_date=datetime.date.today(),
                    start_date=datetime.date.today()- datetime.timedelta(days=90),
                    display_format = 'DD-MM-YYYY',
                    clearable=True,
                    persistence=True,
                    persisted_props=['start_date', 'end_date'],
                    style={
                        # 'width': "40%",
                                      'color': '#212121'}
                    ),
                html.Br()
                ],
            xs=6, sm=6, md=3, lg=3, xl=3
            ),
        dbc.Col(
            [
                html.H6("Select channel to filter graphs"),
                dcc.Dropdown(id="slct_channel",
                    options=[
                        {"label": "Barclays", "value": "Barclays Mobile Banking"},
                        {"label": "Bink", "value": "Bink"}],
                    multi=True,
                    value=["Barclays Mobile Banking", "Bink"],
                    style={
                        # 'width': "40%",
                                      'color': '#212121'},
                    persistence=True,
                    persistence_type='local'
                    ),
                html.Div(id='output_container', children=[]),
                ],
            xs=6, sm=6, md=3, lg=3, xl=3
            )
        ]),

    dbc.Row([
        dbc.Col(
            [
                html.H2(id = 'lc_bar_graph_title', children=[]),
                html.H6("Insert description here............"),
                html.Br(),
                dcc.Graph(id='lc_by_merchant', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2(id = 'lc_pie_graph_title', children=[]),
                html.H6("Insert description here............"),
                html.Br(),
                dcc.Graph(id='lc_Pie_by_merchant', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around'),

    html.Br(),

    dbc.Row([
        dbc.Col(
            [
                html.H2(id = 'UA_line_title', children=[]),
                html.H6("Insert description here............"),
                html.Br(),
                dcc.Graph(id='UA_by_channel', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col([
                html.H2(id = 'pc_pie_graph_title', children=[]),
                html.H6("Insert description here............"),
                html.Br(),
                dcc.Graph(id='Pie_by_issuer_pc', figure={})
        ]
                , #width ={'size':6, 'offset':0,'order':2}
                xs=12, sm=12, md=12, lg=6, xl=6
        )        
    ], justify='around')

], fluid=True)



# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@cache.cached(timeout=TIMEOUT)
def query():
    #====================User SQL query===================================
    df_UA = pd.read_sql("""SELECT COUNT(Distinct u.id) "Total User Count", DATE(u.date_joined) "Creation Date", ca.name "Channel"
        FROM "user" u
        LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id
        LEFT JOIN ubiquity_serviceconsent usc ON usc.user_id = u.id
        WHERE ((ca.name = 'Barclays Mobile Banking' AND (usc.user_id IS NOT NULL))
        OR
        ca.name = 'Bink')
        AND
        DATE(u.date_joined) < current_date
        AND
        NOT (email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\')
        GROUP BY  ca.name, DATE(u.date_joined)
        """, psycopg2.connect(
            host=env.hostref,
            database=env.databasenameref,
            user=env.usernameref,
            password=env.passwordref,
            port=env.portref))
    
    #Create user headline figures
    total_user_headline = df_UA.groupby('Channel').sum().to_dict()['Total User Count']

    #====================PC SQL query==============================
    df_PC = pd.read_sql("""
        SELECT COUNT(Distinct pca.id) "Total Card Count", pc.name "Card Issuer", ca.name "Channel", DATE(pca.created) "Creation Date"
        FROM payment_card_paymentcardaccount pca
        LEFT JOIN payment_card_paymentcard pc ON pc.id = pca.payment_card_id
        INNER JOIN ubiquity_paymentcardaccountentry upcae ON upcae.payment_card_account_id = pca.id
        LEFT JOIN "user" u ON u.id = upcae.user_id
        INNER JOIN user_clientapplication ca ON u.client_id = ca.client_id AND (ca.name = 'Bink' OR ca.name = 'Barclays Mobile Banking')
        WHERE pca.status = 1 AND make_date(pca.expiry_year,pca.expiry_month,01) > current_date 
        AND 
        DATE(pca.created) < current_date
        AND
        NOT (email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\')
        GROUP BY  pc.name, ca.name, DATE(pca.created)
        """, psycopg2.connect(
            host=env.hostref,
            database=env.databasenameref,
            user=env.usernameref,
            password=env.passwordref,
            port=env.portref))
    
    #====================LC SQL query==============================
    df_LC = pd.read_sql("""
        SELECT COUNT(Distinct sa.id) "Total Card Count", DATE(sa.created) "Creation Date", ss.company "Merchant", upse.active_link "PLL Ready", sa.status = 1 "Active", ca.name "Channel"
        FROM scheme_schemeaccount sa
        INNER JOIN scheme_scheme ss ON ss.id = sa.scheme_id
        LEFT JOIN ubiquity_paymentcardschemeentry upse ON upse.scheme_account_id = sa.id
        LEFT JOIN ubiquity_schemeaccountentry usae ON usae.scheme_account_id = sa.id
        LEFT JOIN "user" u ON u.id = usae.user_id
        LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id AND (ca.name = 'Bink' OR ca.name = 'Barclays Mobile Banking')
        WHERE company in ('Wasabi', 'Iceland', 'ASOS', 'SquareMeal')
        AND
        DATE(sa.created) < current_date
        AND
        NOT (email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\')
        GROUP BY  ss.company, DATE(sa.created), upse.active_link, sa.status = 1, ca.name
        """, psycopg2.connect(
            host=env.hostref,
            database=env.databasenameref,
            user=env.usernameref,
            password=env.passwordref,
            port=env.portref))

    #Create Headline totals
    df_LC_PLL_totals = df_LC[(df_LC['PLL Ready']==True) & (df_LC['Active']==True)].groupby('Merchant').sum().to_dict()['Total Card Count']

    #Create dataframe for LC Pie Chart
    df_LC_PLL = df_LC[(df_LC['PLL Ready']==True)&(df_LC['Active']==True)].sort_values('Merchant')

    print("Cache Refresh in progress")

    return {"df_UA": df_UA, "total_user_headline": total_user_headline, "df_PC": df_PC,"df_LC": df_LC, "df_LC_PLL_totals": df_LC_PLL_totals, "df_LC_PLL": df_LC_PLL}



@app.callback(
    [Output(component_id='lc_by_merchant', component_property='figure'),
     Output(component_id='lc_Pie_by_merchant', component_property='figure'),
     Output(component_id='lc_bar_graph_title', component_property='children'),
     Output(component_id='lc_pie_graph_title', component_property='children'),
     Output(component_id='UA_by_channel', component_property='figure'),
     Output(component_id='UA_line_title', component_property='children'),
     Output(component_id='Pie_by_issuer_pc', component_property='figure'),
     Output(component_id='pc_pie_graph_title', component_property='children'),
     Output(component_id="user_headers", component_property='children'),
     Output(component_id="LC_headers", component_property='children')
     ],
    [Input(component_id='date_picker', component_property='start_date'),
    Input(component_id='date_picker', component_property='end_date'),
    Input(component_id='slct_channel', component_property='value')
    ]
)
def update_graph(start_date, end_date, channel):
    if start_date is None:
        start_date = datetime.datetime(2000,1,1)
    if end_date is None:
        end_date = datetime.datetime(2200,1,1)
    # print(start_date)
    # print(end_date)
    # print(type(end_date))

    pd.to_datetime(start_date)
    pd.to_datetime(end_date)

    #Create DataFrames for Loyalty Cards
    lc_bar_title = f"Loyalty Cards Created by Day"
    lc_pie_title = f"Loyalty Cards Pie Chart"
    ua_line_title = f"Users Created by Day"
    pc_pie_title = f"Payment Cards Pie Chart"

    #Dataframe for bar chart
    dff_LC = query()["df_LC"].copy()
    dff_LC['Creation Date'] = pd.to_datetime(dff_LC['Creation Date'])
    dff_LC = dff_LC[(dff_LC['Creation Date']>=start_date) & (dff_LC['Creation Date']<=end_date)]
    dff_LC = dff_LC[dff_LC["Channel"].isin(channel)]
    dff_LC = dff_LC.groupby(['Creation Date','Merchant']).sum().reset_index().sort_values('Merchant')
    
    #Dataframe for pie chart
    dff_LC_PLL = query()["df_LC_PLL"].copy()
    dff_LC_PLL['Creation Date'] = pd.to_datetime(dff_LC_PLL['Creation Date'])
    dff_LC_PLL = dff_LC_PLL[(dff_LC_PLL['Creation Date']>=start_date) & (dff_LC_PLL['Creation Date']<=end_date)]
    dff_LC_PLL = dff_LC_PLL[dff_LC_PLL["Channel"].isin(channel)]
    dff_LC_PLL = dff_LC_PLL.groupby('Merchant').sum().reset_index().sort_values('Merchant')

    #Create Graphs for Loyalty Cards
    lc_fig_bar = px.bar(
        data_frame=dff_LC,
        x='Creation Date',
        y='Total Card Count',
        color='Merchant',
        hover_data=['Merchant', 'Total Card Count'],
        template='plotly_dark',
        color_discrete_map=color_mapping
    )
    lc_fig_pie = px.pie(
        data_frame=dff_LC_PLL,
        values='Total Card Count',
        color='Merchant',
        names='Merchant',
        template='plotly_dark',
        color_discrete_map=color_mapping
    )

    #Create LC Headlines
    LC_header = generate_headers(query()["df_LC_PLL_totals"])

    #Create Dataframes for User
    dff_UA = query()['df_UA'].copy()
    dff_UA['Creation Date'] = pd.to_datetime(dff_UA['Creation Date'])
    dff_UA = dff_UA[(dff_UA['Creation Date']>=start_date) & (dff_UA['Creation Date']<=end_date)]
    dff_UA = dff_UA[dff_UA["Channel"].isin(channel)]
    
    #Create graphs for users
    fig_lin_ua = px.line(
        data_frame=dff_UA,
        x='Creation Date',
        y='Total User Count',
        color='Channel',
        hover_data=['Channel', 'Total User Count'],
        template='plotly_dark',
        color_discrete_map=color_mapping)

    #Create User Headers
    user_header = generate_headers(query()["total_user_headline"])

    #Create Dataframes for payment cards
    dff_PC = query()["df_PC"].copy()
    dff_PC['Creation Date'] = pd.to_datetime(dff_PC['Creation Date'])
    dff_PC = dff_PC[(dff_PC['Creation Date']>=start_date) & (dff_PC['Creation Date']<=end_date)]
    dff_PC = dff_PC[dff_PC["Channel"].isin(channel)]
    dff_PC = dff_PC.groupby('Card Issuer').sum().reset_index()

    #Create pie chart for 
    pc_fig_pie = px.pie(
        data_frame=dff_PC,
        values='Total Card Count',
        names='Card Issuer',
        template='plotly_dark',
        color_discrete_map=color_mapping
    )

    return lc_fig_bar, lc_fig_pie, lc_bar_title, lc_pie_title, fig_lin_ua, ua_line_title, pc_fig_pie, pc_pie_title, user_header, LC_header   #This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns

# %%
