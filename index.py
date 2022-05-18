from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import all_user_stats, transaction_graphs


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        dbc.Nav([
            dbc.NavLink("All User Stats", href="/apps/all_user_stats"),
            dbc.NavLink("Transactions", href="/apps/txn_graphs")
        ])
    ),
    html.Div(dbc.Row([
        dbc.Col(
            html.H1("Bink Internal Reporting",
            className='text-center text-primary, mb-4', style={'text-align': 'center'}),
            width = 12

            )
    ])),

    html.Div(id='page-content', children=[]),

    dcc.Store(id="store-dropdown-value", data=None)

])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/txn_graphs':
        return transaction_graphs.layout
    if pathname == '/apps/all_user_stats':
        return all_user_stats.layout
    else:
        return all_user_stats.layout

if __name__ == '__main__':
    app.run_server(debug=True)