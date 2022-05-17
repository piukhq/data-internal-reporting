from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# Connect to main app.py file
from app import app
from app import server
from app import cache

# Connect to your app pages
from apps import all_user_stats, lc_graphs


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        dbc.Nav([
            dbc.NavLink("Loyalty Cards", active=True, href="/apps/lc_graphs")
            # dbc.NavLink("Bink Users", href="/apps/user_graphs"),
            # dbc.NavLink("Payment Cards", href="/apps/pc_graphs"),
            # dbc.NavLink("Transactions", href="/apps/txn_graphs"),
            # dbc.NavLink("All User Stats", href="/apps/all_user_stats")
        ])
    ),
    html.Div(dbc.Row([
        dbc.Col(
            html.H1(f"Bink Internal Reporting",
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
    if pathname == '/apps/lc_graphs':
        return lc_graphs.layout
    # if pathname == '/apps/user_graphs':
        # return user_graphs.layout
    # if pathname == '/apps/pc_graphs':
        # return pc_graphs.layout
    # if pathname == '/apps/txn_graphs':
        # return transaction_graphs.layout
    # if pathname == '/apps/all_user_stats':
    #     return all_user_stats.layout
    else:
        return "404 Page Error! Please choose a link"


if __name__ == '__main__':
    app.run_server(debug=True)