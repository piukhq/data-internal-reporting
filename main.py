from flask import Flask, redirect, url_for, render_template, send_file
from multiprocessing import connection
from pickle import TRUE
from sqlite3 import Cursor
import psycopg2
import env
import pandas as pd
import matplotlib.pyplot as plt
from graphs import QueryGroupPivotPlotStackedTimeSeriesBar
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import seaborn as sns

app = Flask(__name__)

fig, ax = plt.subplots(figsize=(2,2))
ax=sns.set_style(style="darkgrid")

x = [i for i in range(100)]
y = [i for i in range(100)]

@app.route('/', methods=['GET','POST'])
def home():
    return render_template('home.html')

@app.route("/visualize")
def visualise():
     sns.lineplot(x,y)
     canvas = FigureCanvas(fig)
     img = io.BytesIO()
     fig.savefig(img)
     img.seek(0)
     return send_file(img,mimetype="img/png")

if __name__ == "__main__":
    app.run()