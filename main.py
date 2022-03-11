from datetime import datetime, timedelta
from flask import Flask, render_template
import pandas as pd
import psycopg2, env

pg_host = env.pg_host
pg_user = env.pg_user
pg_pass = env.pg_pass

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def home():
    conn = psycopg2.connect(host=pg_host, database="hermes", user=pg_user, password=pg_pass, sslmode="require")
    query = """
        SELECT
            date_joined::DATE,
            name,
            user_id IS NULL consent,
            COUNT(DISTINCT \"user\".id) users
        FROM
            \"user\"
        INNER JOIN
            user_clientapplication ON \"user\".client_id = user_clientapplication.client_id
        LEFT JOIN
            ubiquity_serviceconsent ON \"user\".id = ubiquity_serviceconsent.user_id
        WHERE
            name = \'Bink\' OR name = \'Barclays Mobile Banking\'
        GROUP BY
            date_joined::DATE,
            name,
            consent
"""

    df = pd.read_sql(query,conn)
    bink_users = df.groupby(df['name']).agg({'users':'sum'})['users']['Bink']
    barclays_users = df.groupby(df['name']).agg({'users':'sum'})['users']['Barclays Mobile Banking']
    df = df.drop('consent',axis=1).groupby(['date_joined','name']).agg({'users':'sum'}).reset_index().pivot(index='date_joined',columns='name',values='users').fillna(0).reset_index()
    day = (datetime.today() - timedelta(days=60)).strftime('%Y/%m/%d')
    df = df[pd.to_datetime(df['date_joined']) >= day]
    labels = list(set(df['date_joined'].astype(str).tolist()))
    bink = df['Bink'].astype(str).tolist()
    barclays = df['Barclays Mobile Banking'].astype(str).tolist()
    return render_template('home.html', labels=labels,bink=bink,barclays=barclays,bink_users=bink_users,barclays_users=barclays_users)

if __name__ == "__main__":
    app.run(debug=True)