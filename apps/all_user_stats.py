#%%
import datetime
import logging
from random import randint
from socket import timeout
from turtle import left, width

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import psycopg2
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output  # pip install dash (version 2.0.0 or higher)
from flask_caching import Cache

from app import app, cache, color_mapping
from supporting_files import env

TIMEOUT = 60

host = env.hostref
user = env.usernameref
password = env.passwordref
port = env.portref

# %%
# ====================Generate column with loop==============================
def generate_headers(user_dict):
    output = []
    length = len(user_dict)
    for key in user_dict:
        output.append(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5(f"{key}", className="text-center")),
                        dbc.CardBody([html.H3(f"{user_dict[key]}", className="text-center card-title")]),
                    ],
                    color="dark",
                    inverse=True,
                ),
                xs=max(6, 12 / length),
                sm=max(6, 12 / length),
                md=max(6, 12 / length),
                lg=max(3, 12 / length),
                xl=max(3, 12 / length),
            )
        )
    return output


# %%
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2(
                            f"Total Consented Users by Channel",
                            id="total_UA",
                            className="text-center text-secondary, mb-4",
                            style={"text-align": "center"},
                        ),
                        dbc.Tooltip(
                            "Total Consented Users by Channel = Total count of users in the Bink and Barclays channel with a service consent. Testers are excluded. Barclays users are counted by Barclays customer ref. Bink users are counted by Bink internal user ref. Note Bink channel users cannot remove consent from service.",
                            target="total_UA",
                            placement="top",
                        ),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
            ],
            justify="around",
        ),
        dbc.Row(id="user_headers", children=[]),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2(
                            f"Total Active PLL Loyalty Cards by Merchant",
                            id="total_PLL",
                            className="text-center text-secondary, mb-4",
                            style={"text-align": "center"},
                        ),
                        dbc.Tooltip(
                            "Total Active PLL Loyalty Cards by Merchant = Total count of PLL ready loyalty cards in an active status. Loyalty cards in tester wallets are excluded.",
                            target="total_PLL",
                            placement="top",
                        ),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
            ],
            justify="around",
        ),
        dbc.Row(id="LC_headers", children=[]),
        html.Hr(),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H6("Select dates to filter graphs", id="date_filter_text"),
                        dbc.Tooltip(
                            "Select dates to filer below graphs. Clearing filters will show all data. Large date ranges may make graphs unreadable.",
                            target="date_filter_text",
                            placement="top",
                        ),
                        dcc.DatePickerRange(
                            id="date_picker",
                            month_format="MMMM Y",
                            end_date=datetime.date.today(),
                            start_date=datetime.date.today() - datetime.timedelta(days=90),
                            display_format="DD-MM-YYYY",
                            clearable=True,
                            persistence=True,
                            persisted_props=["start_date", "end_date"],
                            style={
                                # 'width': "40%",
                                "color": "#212121"
                            },
                        ),
                        html.Br(),
                    ],
                    xs=6,
                    sm=6,
                    md=3,
                    lg=3,
                    xl=3,
                ),
                dbc.Col(
                    [
                        html.H6("Select channel to filter graphs", id="channel_filter_text"),
                        dbc.Tooltip(
                            "Select channel to filter below graphs. Clearing filters will show all data including cards not in wallets. It does not currently filter the headline numbers at the top of the page.",
                            target="channel_filter_text",
                            placement="top",
                        ),
                        dcc.Dropdown(
                            id="slct_channel",
                            options=[
                                {"label": "Barclays", "value": "Barclays Mobile Banking"},
                                {"label": "Bink", "value": "Bink"},
                            ],
                            placeholder="No channel filter selected - all data showing",
                            multi=True,
                            value=["Barclays Mobile Banking", "Bink"],
                            style={
                                # 'width': "40%",
                                "color": "#212121"
                            },
                            persistence=True,
                            persistence_type="local",
                        ),
                        html.Div(id="output_container", children=[]),
                    ],
                    xs=6,
                    sm=6,
                    md=3,
                    lg=3,
                    xl=3,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2(id="lc_bar_graph_title", children=[]),
                        dbc.Tooltip(
                            "Loyalty Cards Created by Day = Count of all loyalty cards created on each day. PLL ready and active status are not requirements for this metric. Loyalty cards in tester wallets are excluded. Historic values may decrement if channel filters are selected, remove channel filters to see a static view. Loyalty cards are counted by bink internal ref therefore multiple counts for same loyalty card may exist due to existance of loyalty cards in error states.",
                            target="lc_bar_graph_title",
                            placement="top",
                        ),
                        html.Br(),
                        dcc.Graph(id="lc_by_merchant", figure={}),
                    ],  # width ={'size':6, 'offset':0,'order':1}
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
                dbc.Col(
                    [
                        html.H2(id="lc_pie_graph_title", children=[]),
                        dbc.Tooltip(
                            "Loyalty Cards Pie Chart = Total count of PLL ready loyalty cards in an active status. Loyalty cards in tester wallets are excluded. Loyalty cards are counted by bink internal ref.",
                            target="lc_pie_graph_title",
                            placement="top",
                        ),
                        html.Br(),
                        dcc.Graph(id="lc_Pie_by_merchant", figure={}),
                    ],  # width ={'size':6, 'offset':0,'order':2}
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
            ],
            justify="around",
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2(id="UA_line_title", children=[]),
                        dbc.Tooltip(
                            "Users Created by Day = Total count of users on each day. Service consent is not a requirement for this metric. Testers are excluded. Barclays users are counted by Barclays customer ref. Bink users are counted by Bink internal user ref.",
                            target="UA_line_title",
                            placement="top",
                        ),
                        html.Br(),
                        dcc.Graph(id="UA_by_channel", figure={}),
                    ],  # width ={'size':6, 'offset':0,'order':1}
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
                dbc.Col(
                    [
                        html.H2(id="pc_pie_graph_title", children=[]),
                        dbc.Tooltip(
                            "Payment Cards Pie Chart = Total count of unexpired payment cards in an active status. Paymemt cards in tester wallets are excluded. Payment Cards are counted by fingerprint (PAN).",
                            target="pc_pie_graph_title",
                            placement="top",
                        ),
                        html.Br(),
                        dcc.Graph(id="Pie_by_issuer_pc", figure={}),
                    ],  # width ={'size':6, 'offset':0,'order':2}
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
            ],
            justify="around",
        ),
    ],
    fluid=True,
)


# ------------------------------------------------------------------------------
def con_db(database):
    try:
        logging.info("Opening DataBase connection")
        connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        logging.info("Database connected")
        return connection
    except (psycopg2.DatabaseError) as error:
        logging.error(error)


# Connect the Plotly graphs with Dash Components
@cache.cached(timeout=TIMEOUT, key_prefix="user")
def user_query():

    print("User cache refresh in progress")

    # ====================User SQL query===================================
    df_UA = pd.read_sql(
        """SELECT COUNT(DISTINCT (CASE WHEN ca.name = 'Barclays Mobile Banking' THEN u.external_id::varchar WHEN ca.name = 'Bink' THEN u.id::varchar END)) "Total User Count", DATE(u.date_joined) "Creation Date", ca.name "Channel", ((ca.name = 'Barclays Mobile Banking' AND (usc.user_id IS NOT NULL)) OR ca.name = 'Bink') "Consented"
        FROM "user" u
        LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id
        LEFT JOIN ubiquity_serviceconsent usc ON usc.user_id = u.id
        WHERE 
        DATE(u.date_joined) < current_date
        AND
        (NOT (email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\') OR email IS NULL)
        GROUP BY  ca.name, DATE(u.date_joined), ((ca.name = 'Barclays Mobile Banking' AND (usc.user_id IS NOT NULL)) OR ca.name = 'Bink')
        """,
        con_db("hermes"),
    )

    # Create user headline figures
    total_user_headline = df_UA[df_UA["Consented"] == True].groupby("Channel").sum().to_dict()["Total User Count"]

    # ====================PC SQL query==============================
    df_PC = pd.read_sql(
        """
        SELECT COUNT(Distinct pca.fingerprint) "Total Card Count", pc.name "Card Issuer", ca.name "Channel", DATE(pca.created) "Creation Date"
        FROM payment_card_paymentcardaccount pca
        LEFT JOIN payment_card_paymentcard pc ON pc.id = pca.payment_card_id
        LEFT JOIN ubiquity_paymentcardaccountentry upcae ON upcae.payment_card_account_id = pca.id
        LEFT JOIN "user" u ON u.id = upcae.user_id
        LEFT JOIN user_clientapplication ca ON u.client_id = ca.client_id AND (ca.name = 'Bink' OR ca.name = 'Barclays Mobile Banking')
        WHERE pca.status = 1 AND make_date(pca.expiry_year,pca.expiry_month,01) > current_date 
        AND 
        DATE(pca.created) < current_date
        AND
        (NOT (email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\') OR email IS NULL)
        GROUP BY  pc.name, ca.name, DATE(pca.created)
        """,
        con_db("hermes"),
    )

    # ====================LC SQL query==============================
    df_LC = pd.read_sql(
        """
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
        (NOT (email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\') OR email IS NULL)
        GROUP BY  ss.company, DATE(sa.created), upse.active_link, sa.status = 1, ca.name
        """,
        con_db("hermes"),
    )

    # Create Headline totals
    df_LC_PLL_totals = (
        df_LC[(df_LC["PLL Ready"] == True) & (df_LC["Active"] == True)]
        .groupby("Merchant")
        .sum()
        .to_dict()["Total Card Count"]
    )

    # Create dataframe for LC Pie Chart
    df_LC_PLL = df_LC[(df_LC["PLL Ready"] == True) & (df_LC["Active"] == True)].sort_values("Merchant")

    print("User cache refresh complete")

    return {
        "df_UA": df_UA,
        "total_user_headline": total_user_headline,
        "df_PC": df_PC,
        "df_LC": df_LC,
        "df_LC_PLL_totals": df_LC_PLL_totals,
        "df_LC_PLL": df_LC_PLL,
    }


@app.callback(
    [
        Output(component_id="lc_by_merchant", component_property="figure"),
        Output(component_id="lc_Pie_by_merchant", component_property="figure"),
        Output(component_id="lc_bar_graph_title", component_property="children"),
        Output(component_id="lc_pie_graph_title", component_property="children"),
        Output(component_id="UA_by_channel", component_property="figure"),
        Output(component_id="UA_line_title", component_property="children"),
        Output(component_id="Pie_by_issuer_pc", component_property="figure"),
        Output(component_id="pc_pie_graph_title", component_property="children"),
        Output(component_id="user_headers", component_property="children"),
        Output(component_id="LC_headers", component_property="children"),
    ],
    [
        Input(component_id="date_picker", component_property="start_date"),
        Input(component_id="date_picker", component_property="end_date"),
        Input(component_id="slct_channel", component_property="value"),
    ],
)
def user_update_graph(start_date, end_date, channel):

    user_dict = user_query()

    df_LC = user_dict["df_LC"].copy()
    df_LC_PLL = user_dict["df_LC_PLL"].copy()
    df_UA = user_dict["df_UA"].copy()
    total_user_headline = user_dict["total_user_headline"].copy()
    df_PC = user_dict["df_PC"].copy()
    df_LC_PLL_totals = user_dict["df_LC_PLL_totals"].copy()

    if start_date is None:
        start_date = datetime.datetime(2000, 1, 1)
    if end_date is None:
        end_date = datetime.datetime(2200, 1, 1)
    # print(start_date)
    # print(end_date)
    # print(type(end_date))

    pd.to_datetime(start_date)
    pd.to_datetime(end_date)

    # Create DataFrames for Loyalty Cards
    lc_bar_title = f"Loyalty Cards Created by Day"
    lc_pie_title = f"Loyalty Cards Pie Chart"
    ua_line_title = f"Users Created by Day"
    pc_pie_title = f"Payment Cards Pie Chart"

    # Dataframe for bar chart
    dff_LC = df_LC
    dff_LC["Creation Date"] = pd.to_datetime(dff_LC["Creation Date"])
    dff_LC = dff_LC[(dff_LC["Creation Date"] >= start_date) & (dff_LC["Creation Date"] <= end_date)]
    if len(channel) != 0:
        dff_LC = dff_LC[dff_LC["Channel"].isin(channel)]
    dff_LC = dff_LC.groupby(["Creation Date", "Merchant"]).sum().reset_index().sort_values("Merchant")

    # Dataframe for pie chart
    dff_LC_PLL = df_LC_PLL
    dff_LC_PLL["Creation Date"] = pd.to_datetime(dff_LC_PLL["Creation Date"])
    dff_LC_PLL = dff_LC_PLL[(dff_LC_PLL["Creation Date"] >= start_date) & (dff_LC_PLL["Creation Date"] <= end_date)]
    if len(channel) != 0:
        dff_LC_PLL = dff_LC_PLL[dff_LC_PLL["Channel"].isin(channel)]
    dff_LC_PLL = dff_LC_PLL.groupby("Merchant").sum().reset_index().sort_values("Merchant")

    # Create Graphs for Loyalty Cards
    lc_fig_bar = px.bar(
        data_frame=dff_LC,
        x="Creation Date",
        y="Total Card Count",
        color="Merchant",
        hover_data=["Merchant", "Total Card Count"],
        template="plotly_dark",
        color_discrete_map=color_mapping,
    )
    lc_fig_pie = px.pie(
        data_frame=dff_LC_PLL,
        values="Total Card Count",
        color="Merchant",
        names="Merchant",
        template="plotly_dark",
        color_discrete_map=color_mapping,
    )

    # Create LC Headlines
    LC_header = generate_headers(df_LC_PLL_totals)

    # Create Dataframes for User
    dff_UA = df_UA
    dff_UA["Creation Date"] = pd.to_datetime(dff_UA["Creation Date"])
    dff_UA = dff_UA[(dff_UA["Creation Date"] >= start_date) & (dff_UA["Creation Date"] <= end_date)]
    if len(channel) != 0:
        dff_UA = dff_UA[dff_UA["Channel"].isin(channel)]
    dff_UA = dff_UA.groupby(["Channel", "Creation Date"]).sum().reset_index()

    # Create graphs for users
    fig_lin_ua = px.line(
        data_frame=dff_UA,
        x="Creation Date",
        y="Total User Count",
        color="Channel",
        hover_data=["Channel", "Total User Count"],
        template="plotly_dark",
        color_discrete_map=color_mapping,
    )

    # Create User Headers
    user_header = generate_headers(total_user_headline)

    # Create Dataframes for payment cards
    dff_PC = df_PC
    dff_PC["Creation Date"] = pd.to_datetime(dff_PC["Creation Date"])
    dff_PC = dff_PC[(dff_PC["Creation Date"] >= start_date) & (dff_PC["Creation Date"] <= end_date)]
    if len(channel) != 0:
        dff_PC = dff_PC[dff_PC["Channel"].isin(channel)]
    dff_PC = dff_PC.groupby("Card Issuer").sum().reset_index()

    # Create pie chart for
    pc_fig_pie = px.pie(
        data_frame=dff_PC,
        values="Total Card Count",
        names="Card Issuer",
        template="plotly_dark",
        color_discrete_map=color_mapping,
    )

    return (
        lc_fig_bar,
        lc_fig_pie,
        lc_bar_title,
        lc_pie_title,
        fig_lin_ua,
        ua_line_title,
        pc_fig_pie,
        pc_pie_title,
        user_header,
        LC_header,
    )  # This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns


# %%

# %%
