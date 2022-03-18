from flask import Flask, redirect, url_for, render_template, request, send_file
from multiprocessing import connection
from pickle import TRUE
from sqlite3 import Cursor
import psycopg2
from supporting_files import env
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import seaborn as sns
import dash_bootstrap_components as dbc

def QueryGroup(query, date_field, group_field, count_field, start_date,end_date):
    conn = psycopg2.connect(
    host=env.hostref,
    database=env.databasenameref,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref)

    cur = conn.cursor()
    df = pd.read_sql(query, conn, parse_dates=date_field)
    cur.close()
    conn.close()

    df[date_field] = df[date_field].dt.date
    grouped_df =  df.groupby([date_field,group_field])[count_field].nunique().reset_index()
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()
    grouped_df = grouped_df.loc[(grouped_df[date_field]>=start_date)&(grouped_df[date_field]<=end_date)]
    
    return grouped_df

def QueryGroupHarm(query, date_field, group_field, count_field, start_date,end_date):
    conn = psycopg2.connect(
    host=env.hostref,
    database=env.databasenamerefharm,
    user=env.usernameref,
    password=env.passwordref,
    port=env.portref)

    cur = conn.cursor()
    df = pd.read_sql(query, conn, parse_dates=date_field)
    cur.close()
    conn.close()

    df[date_field] = df[date_field].dt.date
    grouped_df =  df.groupby([date_field,group_field])[count_field].nunique().reset_index()
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()
    grouped_df = grouped_df.loc[(grouped_df[date_field]>=start_date)&(grouped_df[date_field]<=end_date)]
    
    return grouped_df