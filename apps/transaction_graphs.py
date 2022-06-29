#%%
# from turtle import left, width
import datetime
import logging
import os
from random import randint

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

TIMEOUT = 60


# ====================Generate column with loop==============================
def generate_headers(txn_dict):
    output = []
    length = len(txn_dict)
    for key in txn_dict:
        output.append(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4(f"{key}", className="text-center")),
                        dbc.CardBody([html.H4(f"£{txn_dict[key]:,.2f}", className="text-center card-title")]),
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


#%%
# ------------------------------------------------------------------------------
# App layout - everything in the dash goes in here including the HTML
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4(
                            f"Total Spend to Date",
                            id="total_spend",
                            className="text-center text-secondary, mb-4",
                            style={"text-align": "center"},
                        ),
                        dbc.Tooltip(
                            "Total Spend to Date: The total amount of all transactions exported by Bink. Should be noted that this just takes into account positive transactions and not refunds.",
                            target="total_spend",
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
        dbc.Row(id="tv_headers", children=[]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4(
                            f"Average Spend",
                            id="avg_spend",
                            className="text-center text-secondary, mb-4",
                            style={"text-align": "center"},
                        ),
                        dbc.Tooltip(
                            "Average Spend: The average spend amount per transaction. Should be noted that this just takes into account positive transactions and not refunds.",
                            target="avg_spend",
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
        dbc.Row(id="avg_headers", children=[]),
        # Filter
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H6("Select dates to filter graphs"),
                        dbc.Tooltip(
                            "This date filter can be applied to filter the charts below. It does not currently also filter the headline numbers at the top of the page.",
                            target="date_picker",
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
                )
            ]
        ),
        # First ChartRow
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4(id="bar_graph_title_txn", children=[]),
                        dbc.Tooltip("", target="bar_graph_title_txn", placement="top"),
                        dcc.Graph(id="txn_by_merchant", figure={}),
                    ],  # width ={'size':6, 'offset':0,'order':1}
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,
                ),
                dbc.Col(
                    [
                        html.H4(id="active_user_title", children=[]),
                        dbc.Tooltip(
                            "Active users is a unique count of loyalty accounts for which we have exported transactions.",
                            target="active_user_title",
                            placement="top",
                        ),
                        dcc.Graph(id="active_user_bar", figure={}),
                    ],  # width ={'size':6, 'offset':0,'order':1}
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


def con_db(database):
    try:
        logging.info("Opening DataBase connection")
        connection = psycopg2.connect(os.getenv("POSTGRES_DSN").format(database))
        logging.info("Database connected")
        return connection
    except (psycopg2.DatabaseError) as error:
        logging.error(error)


@cache.cached(timeout=TIMEOUT, key_prefix="txn")
def txn_query():

    print("txn cache in progress")
    # ====================Export Transactions SQL Query==============================

    con_har = con_db("harmonia")

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

    df_live = pd.read_sql(sql, con_har)
    # max_arch = df_live["created_at"].min().strftime("%Y-%m-%d")
    df_live.drop(["created_at"], axis=1, inplace=True)

    # con_har = con_db("20220405_harmonia")

    # sql = f"""
    #     SELECT DISTINCT
    #         id,
    #         transaction_id,
    #         feed_type,
    #         transaction_date,
    #         provider_slug,
    #         spend_amount,
    #         loyalty_id,
    #         user_id
    #     FROM
    #         export_transaction
    #     WHERE
    #         (provider_slug = \'squaremeal\' OR
    #         provider_slug = \'iceland-bonus-card\' OR
    #         provider_slug = \'bpl-asos\' OR
    #         provider_slug = \'wasabi-club\') AND
    #         status = \'EXPORTED\' AND
    #         spend_amount > 0 AND
    #         created_at < \'{max_arch}\'
    # """
    # df_arch = pd.read_sql(sql, con_har)
    # df_arch.head()

    # df = pd.concat([df_live, df_arch])
    df = df_live
    df["spend_amount"] = df["spend_amount"] / 100
    df.drop(df[df["feed_type"] == "AUTH"].index, inplace=True)
    df.drop(["feed_type"], axis=1, inplace=True)
    df.replace(
        {"bpl-asos": "ASOS", "iceland-bonus-card": "Iceland", "squaremeal": "SquareMeal", "wasabi-club": "Wasabi"},
        inplace=True,
    )

    con_her = con_db("hermes")

    # ====================Test Users SQL Query==============================

    sql = """
        SELECT
            id user_id,
            email
        FROM
            \"user\"
        WHERE
            email LIKE \'%@bink%\' OR email LIKE \'%@testbink%\' OR email LIKE \'%@e2e.bink.com%\'
    """

    testers = pd.read_sql(sql, con_her)
    # ====================Filter Testers==============================
    df = pd.merge(df, testers, "left", "user_id")
    df = df[df["email"].isna()]
    # ====================Aggregate values and format==============================
    avg_txn_dict = df.groupby(["provider_slug"]).aggregate({"spend_amount": "mean"}).to_dict()["spend_amount"]
    tv_txn_dict = df.groupby(["provider_slug"]).aggregate({"spend_amount": "sum"}).to_dict()["spend_amount"]

    print("txn cache complete")

    return {"df": df, "avg_txn_dict": avg_txn_dict, "tv_txn_dict": tv_txn_dict}


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [
        Output(component_id="txn_by_merchant", component_property="figure"),
        Output(component_id="bar_graph_title_txn", component_property="children"),
        Output(component_id="active_user_bar", component_property="figure"),
        Output(component_id="active_user_title", component_property="children"),
        Output(component_id="avg_headers", component_property="children"),
        Output(component_id="tv_headers", component_property="children"),
    ],
    [
        Input(component_id="date_picker", component_property="start_date"),
        Input(component_id="date_picker", component_property="end_date"),
    ],
)
def update_graph(start_date, end_date):
    if start_date is None:
        start_date = datetime.datetime(2000, 1, 1)
    if end_date is None:
        end_date = datetime.datetime(2200, 1, 1)
    bar_title = f"Transactions by Day"
    active_user_title = f"Active Users by Month"

    txn_dict = txn_query()

    df = txn_dict["df"].copy()
    avg_txn_dict = txn_dict["avg_txn_dict"].copy()
    tv_txn_dict = txn_dict["tv_txn_dict"].copy()

    # Create headline numbers
    avg_header = generate_headers(avg_txn_dict)
    tv_header = generate_headers(tv_txn_dict)

    df_tr = df
    df_tr["transaction_date"] = pd.to_datetime(df_tr["transaction_date"])
    df_tr = df_tr[(df_tr["transaction_date"] >= start_date) & (df_tr["transaction_date"] <= end_date)]

    dff_txn = (
        df_tr.groupby([df_tr["transaction_date"].dt.date, "provider_slug"])
        .aggregate({"transaction_id": "count"})
        .reset_index()
    )
    dff_txn.columns = ["Transaction Date", "Merchant", "No. of Transactions"]
    dff_txn.sort_values(by="Merchant", inplace=True)

    active_df = (
        df_tr.groupby([df_tr["transaction_date"].dt.to_period("m"), "provider_slug"])
        .aggregate({"user_id": "nunique"})
        .reset_index()
    )
    active_df.columns = ["Transaction Date", "Merchant", "No. of Users"]
    active_df.sort_values(by="Merchant", inplace=True)
    active_df["Transaction Date"] = active_df["Transaction Date"].astype("datetime64")

    # Plotly Express
    fig_bar = px.bar(
        data_frame=dff_txn,
        x="Transaction Date",
        y="No. of Transactions",
        color="Merchant",
        hover_data=["Merchant", "No. of Transactions"],
        template="plotly_dark",
        color_discrete_map=color_mapping,
    )

    fig_bar_active = px.bar(
        data_frame=active_df,
        x="Transaction Date",
        y="No. of Users",
        color="Merchant",
        hover_data=["Merchant", "No. of Users"],
        template="plotly_dark",
        color_discrete_map=color_mapping,
    )

    return (
        fig_bar,
        bar_title,
        fig_bar_active,
        active_user_title,
        avg_header,
        tv_header,
    )  # This is what is being returned to the outputs in the callbacks 2 outputs = 2 returns
