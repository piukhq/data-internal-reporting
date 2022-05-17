#%%
# from turtle import left, width
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
from app import color_mapping

host = env.hostref
user = env.usernameref
password = env.passwordref
port = env.portref

#====================Export Transactions SQL Query==============================

con_har = psycopg2.connect(
    host=host,
    database="harmonia",
    user=user,
    password=password,
    port=port)

sql = """
    SELECT DISTINCT
        id,
        transaction_id,
        feed_type,
        transaction_date,
        created_at,
        provider_slug,
        spend_amount,
        loyalty_id,
        user_id
    FROM
        export_transaction
    WHERE
        (provider_slug = \'squaremeal\' OR
        provider_slug = \'iceland-bonus-card\' OR
        provider_slug = \'bpl-asos\' OR
        provider_slug = \'wasabi-club\') AND
        status = \'EXPORTED\' AND
        spend_amount > 0
"""

df_live = pd.read_sql(sql,con_har)
max_arch = df_live['created_at'].min().strftime("%Y-%m-%d")
df_live.drop(['created_at'],axis=1,inplace=True)

con_har = psycopg2.connect(
    host=host,
    database="20220405_harmonia",
    user=user,
    password=password,
    port=port)

sql = f"""
    SELECT DISTINCT
        id,
        transaction_id,
        feed_type,
        transaction_date,
        provider_slug,
        spend_amount,
        loyalty_id,
        user_id
    FROM
        export_transaction
    WHERE
        (provider_slug = \'squaremeal\' OR
        provider_slug = \'iceland-bonus-card\' OR
        provider_slug = \'bpl-asos\' OR
        provider_slug = \'wasabi-club\') AND
        status = \'EXPORTED\' AND
        spend_amount > 0 AND
        created_at < \'{max_arch}\'
"""
df_arch = pd.read_sql(sql,con_har)
df_arch.head()

df = pd.concat([df_live,df_arch])
df['spend_amount'] = df['spend_amount']/100
df.drop(df[df['feed_type']=='AUTH'].index, inplace=True)
df.drop(['feed_type'],axis=1, inplace=True)
df.replace({
    'bpl-asos':'ASOS',
    'iceland-bonus-card':'Iceland',
    'squaremeal':'SquareMeal',
    'wasabi-club':'Wasabi'},inplace=True)

con_her = psycopg2.connect(
    host=host,
    database="hermes",
    user=user,
    password=password,
    port=port)

#====================Test Users SQL Query==============================

sql = """
    SELECT
        id user_id,
        email
    FROM
        \"user\"
    WHERE
        email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\'
"""

testers = pd.read_sql(sql,con_her)
#====================Filter Testers==============================
df = pd.merge(df,testers,'left','user_id')
df = df[df['email'].isna()]
#====================Aggregate values and format==============================
avg_dict = df.groupby(['provider_slug']).aggregate({'spend_amount':'mean'}).to_dict()['spend_amount']

#====================Generate column with loop==============================
def generate_headers(dict):
    output = []
    length = len(dict)
    for key in dict:
        output.append(dbc.Col(
                [
                dbc.Row([html.H4(f"{key}",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'})]),
                dbc.Row([html.H4(f"£{dict[key]:.2f}",
                className='text-center text-info, mb-4', style={'text-align': 'center'})])
                ], 
                xs=max(6,12/length), sm=max(6,12/length), md=max(6,12/length), lg=max(3,12/length), xl=max(3,12/length)))
    return output
#%%
# ------------------------------------------------------------------------------
# App layout - everything in the dash goes in here including the HTML
layout = dbc.Container([
    # Title
    dbc.Row([
        dbc.Col(
                [
                html.H4(f"Average Transaction Amount",
                className='text-center text-secondary, mb-4', style={'text-align': 'center'})
                ], 
            xs=12, sm=12, md=12, lg=6, xl=6),
        ], justify='around'),
    # Headlines
    dbc.Row(
        generate_headers(avg_dict)
    ),
    # Filter
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
        )
    ]),
    # First ChartRow
    dbc.Row([
        dbc.Col(
            [
                html.H4(id = 'bar_graph_title_txn', children=[]),
                dcc.Graph(id='txn_by_merchant', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        ),
        dbc.Col(
            [
                html.H4(id = 'active_user_title', children=[]),
                dcc.Graph(id='active_user_bar', figure={})
                ]
                , #width ={'size':6, 'offset':0,'order':1}
                xs=12, sm=12, md=12, lg=6, xl=6
        )
    ], justify='around')
], fluid=True)



# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [
    #  Output(component_id='output_container_txn', component_property='children'),
     Output(component_id='txn_by_merchant', component_property='figure'),
     Output(component_id='bar_graph_title_txn', component_property='children'),
     Output(component_id='active_user_bar', component_property='figure'),
     Output(component_id='active_user_title', component_property='children')
     ],
     [Input(component_id='date_picker', component_property='start_date'),
    Input(component_id='date_picker', component_property='end_date')]
)
def update_graph(start_date, end_date):
    if start_date is None:
        start_date = datetime.datetime(2000,1,1)
    if end_date is None:
        end_date = datetime.datetime(2200,1,1)
    # container = f"The year chosen by user was: {option_slctd}"
    bar_title = f"Transactions by Day"
    active_user_title = f"Active Users by Month"

    df_tr = df
    df_tr['transaction_date'] = pd.to_datetime(df_tr['transaction_date'])
    df_tr = df_tr[(df_tr["transaction_date"]>=start_date) & (df_tr['transaction_date']<=end_date)]

    dff_txn = df_tr.groupby([df_tr['transaction_date'].dt.date,'provider_slug']).aggregate({'transaction_id':'count'}).reset_index()
    dff_txn.columns = ['Transaction Date', 'Merchant', 'No. of Transactions']
    dff_txn.sort_values(by='Merchant',inplace=True)

    active_df = df_tr.groupby([df_tr['transaction_date'].dt.to_period('m'),'provider_slug']).aggregate({'user_id':'nunique'}).reset_index()
    active_df.columns = ['Transaction Date', 'Merchant', 'No. of Users']
    active_df.sort_values(by='Merchant',inplace=True)
    active_df['Transaction Date'] = active_df['Transaction Date'].astype('datetime64')



    # Plotly Express
    fig_bar = px.bar(
        data_frame=dff_txn,
        x='Transaction Date',
        y='No. of Transactions',
        color='Merchant',
        hover_data=['Merchant', 'No. of Transactions'],
        template='plotly_dark',
        color_discrete_map=color_mapping
    )

    fig_bar_active = px.bar(
        data_frame=active_df,
        x='Transaction Date',
        y='No. of Users',
        color='Merchant',
        hover_data=['Merchant', 'No. of Users'],
        template='plotly_dark',
        color_discrete_map=color_mapping
    )

    # Trialing hover templates to clean up formatting
    # fig_bar.update_layout(
    #     hoverlabel=dict(
    #         bgcolor="white",
    #         font_size=16,
    #         font_family="Rockwell"
    #     )
    # )
    
    return fig_bar, bar_title, fig_bar_active, active_user_title #This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns