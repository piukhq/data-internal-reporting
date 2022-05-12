#%%
from turtle import left
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from pyparsing import And  # pip install dash (version 2.0.0 or higher)
import env
import psycopg2

# -- Import and clean data (importing csv into pandas)
# df = pd.read_csv("intro_bees.csv")


"""SELECT COUNT(*) "Total User Count", DATE(u.date_joined) "Creation Date", ca.name "Channel"
FROM "user" u
LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id
GROUP BY  ca.name, DATE(u.date_joined)"""

df_wasabi_vouchers = pd.read_sql(
"""SELECT
    jsonb_array_elements(vouchers)->>'date_issued'::TEXT AS issue_date,
    jsonb_array_elements(vouchers)->>'code'::TEXT AS code,
    scheme_scheme.company AS name
FROM
    scheme_schemeaccount
LEFT JOIN 
    scheme_scheme ON scheme_schemeaccount.scheme_id = scheme_scheme.id
WHERE
    vouchers!= '{}'
    AND
    company = 'Wasabi'""",
psycopg2.connect(
    host=env.hostref,
    database="hermes",
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))


df_wasabi_vouchers

df_ASOS_vouchers = pd.read_sql(
"""select COUNT(DISTINCT code) "Voucher Count", 
retailer_slug "Merchant", 
DATE(issued_date) "Issued Date"
FROM account_holder_reward
where retailer_slug = 'asos'
GROUP BY Date(issued_date), retailer_slug""",
psycopg2.connect(
    host=env.hostref,
    database="polaris",
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))
df_ASOS_vouchers

df_wasabi_vouchers = df_wasabi_vouchers[df_wasabi_vouchers['code'].notnull()]
df_wasabi_vouchers['Issued Date'] = pd.to_datetime(df_wasabi_vouchers['issue_date'],unit='s').dt.date
df_wasabi_vouchers = df_wasabi_vouchers.groupby(['Issued Date', 'name']).code.nunique().reset_index()
df_wasabi_vouchers.columns = ["Issued Date", "Merchant", "Voucher Count"]
df_wasabi_vouchers

df_vouchers = pd.concat([df_ASOS_vouchers,df_wasabi_vouchers], ignore_index=True).reset_index()
df_vouchers.drop('index',1,inplace=True)
df_vouchers
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
from dash import Dash, html, dcc, Input, Output

import datetime as dt

import numpy as np
import pandas as pd
from dash.dependencies import Input, Output
from flask_caching import Cache

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

TIMEOUT = 60

@cache.memoize(timeout=TIMEOUT)
def query_data():
    # This could be an expensive data querying step
    np.random.seed(0)  # no-display
    df = pd.DataFrame(
        np.random.randint(0, 100, size=(100, 4)),
        columns=list('ABCD')
    )
    now = dt.datetime.now()
    df['time'] = [now - dt.timedelta(seconds=5*i) for i in range(100)]
    return df.to_json(date_format='iso', orient='split')


def dataframe():
    return pd.read_json(query_data(), orient='split')

app.layout = html.Div([
    html.Div('Data was updated within the last {} seconds'.format(TIMEOUT)),
    dcc.Dropdown(dataframe().columns, 'A', id='live-dropdown'),
    dcc.Graph(id='live-graph')
])


@app.callback(Output('live-graph', 'figure'),
              Input('live-dropdown', 'value'))
def update_live_graph(value):
    df = dataframe()
    now = dt.datetime.now()
    return {
        'data': [{
            'x': df['time'],
            'y': df[value],
            'line': {
                'width': 1,
                'color': '#0074D9',
                'shape': 'spline'
            }
        }],
        'layout': {
            # display the current position of now
            # this line will be between 0 and 60 seconds
            # away from the last datapoint
            'shapes': [{
                'type': 'line',
                'xref': 'x', 'x0': now, 'x1': now,
                'yref': 'paper', 'y0': 0, 'y1': 1,
                'line': {'color': 'darkgrey', 'width': 1}
            }],
            'annotations': [{
                'showarrow': False,
                'xref': 'x', 'x': now, 'xanchor': 'right',
                'yref': 'paper', 'y': 0.95, 'yanchor': 'top',
                'text': 'Current time ({}:{}:{})'.format(
                    now.hour, now.minute, now.second),
                'bgcolor': 'rgba(255, 255, 255, 0.8)'
            }],
            # aesthetic options
            'margin': {'l': 40, 'b': 40, 'r': 20, 't': 10},
            'xaxis': {'showgrid': False, 'zeroline': False},
            'yaxis': {'showgrid': False, 'zeroline': False}
        }
    }


if __name__ == '__main__':
    app.run_server(debug=True)
#%%
from turtle import left
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from pyparsing import And  # pip install dash (version 2.0.0 or higher)
import env
import psycopg2

df_LC = pd.read_sql("""
SELECT COUNT(Distinct sa.id) "Total Card Count", DATE(sa.created) "Creation Date", ss.company "Merchant", upse.active_link "PLL Ready", sa.status = 1 "Active", ca.name "Channel"
FROM scheme_schemeaccount sa
INNER JOIN scheme_scheme ss ON ss.id = sa.scheme_id
LEFT JOIN ubiquity_paymentcardschemeentry upse ON upse.scheme_account_id = sa.id
LEFT JOIN ubiquity_schemeaccountentry usae ON usae.scheme_account_id = sa.id
LEFT JOIN "user" u ON u.id = usae.user_id
LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id AND (ca.name = 'Bink' OR ca.name = 'Barclays Mobile Banking')
WHERE company in ('Wasabi', 'Iceland', 'ASOS', 'SquareMeal')
GROUP BY  ss.company, DATE(sa.created), upse.active_link, sa.status = 1, ca.name
""", psycopg2.connect(
    host=env.hostref,
    database=env.databasenameref,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))

#Create Headline totals
df_LC_PLL_totals = df_LC[(df_LC['PLL Ready']==True) & (df_LC['Active']==True)].groupby('Merchant').sum().to_dict()['Total Card Count']
df_LC_PLL_totals

#Create dataframe for LC Pie Chart
df_LC_PLL = df_LC[df_LC['PLL Ready']==True]

df_LC_PLL_totals

# %%

for key in df_LC_PLL_totals:
    print(df_LC_PLL_totals[key])
    
len(df_LC_PLL_totals)

min(2, len(df_LC_PLL_totals))
# %%
df_UA = pd.read_sql("""SELECT COUNT(*) "Total User Count", DATE(u.date_joined) "Creation Date", ca.name "Channel"
FROM "user" u
LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id
LEFT JOIN ubiquity_serviceconsent usc ON usc.user_id = u.id
WHERE (ca.name = 'Barclays Mobile Banking' AND (usc.user_id IS NOT NULL))
OR
ca.name = 'Bink'
GROUP BY  ca.name, DATE(u.date_joined)
""", psycopg2.connect(
    host=env.hostref,
    database=env.databasenameref,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))

#%%
#Create user headline figures
total_user_headline = df_UA.groupby('Channel').sum().to_dict()['Total User Count']
total_user_headline['Barclays Mobile Banking']
# %%
type(total_user_headline)
# %%
df_LC = pd.read_sql("""
SELECT COUNT(Distinct sa.id) "Total Card Count", DATE(sa.created) "Creation Date", ss.company "Merchant", upse.active_link "PLL Ready", sa.status = 1 "Active", ca.name "Channel"
FROM scheme_schemeaccount sa
INNER JOIN scheme_scheme ss ON ss.id = sa.scheme_id
LEFT JOIN ubiquity_paymentcardschemeentry upse ON upse.scheme_account_id = sa.id
LEFT JOIN ubiquity_schemeaccountentry usae ON usae.scheme_account_id = sa.id
LEFT JOIN "user" u ON u.id = usae.user_id
LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id AND (ca.name = 'Bink' OR ca.name = 'Barclays Mobile Banking')
WHERE company in ('Wasabi', 'Iceland', 'ASOS', 'SquareMeal')
GROUP BY  ss.company, DATE(sa.created), upse.active_link, sa.status = 1, ca.name
""", psycopg2.connect(
    host=env.hostref,
    database=env.databasenameref,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref))

#Create Headline totals
df_LC_PLL_totals = df_LC[(df_LC['PLL Ready']==True) & (df_LC['Active']==True)].groupby('Merchant').sum().to_dict()['Total Card Count']
df_LC_PLL_totals
# %%
type(df_LC_PLL_totals)
# %%
from datetime import datetime

x = datetime.datetime()