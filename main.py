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
            (name = \'Bink\' OR name = \'Barclays Mobile Banking\') AND 
            date_joined < CURRENT_DATE
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
    labels = df['date_joined'].astype(str).tolist()
    bink = df['Bink'].astype(str).tolist()
    barclays = df['Barclays Mobile Banking'].astype(str).tolist()

    query = """
        SELECT
            user_clientapplication.name,
            company,
            jsonb_array_length(pll_links) <> 0 pll_link,
            COUNT( DISTINCT card_number) cards
        FROM
            scheme_schemeaccount
        INNER JOIN
            scheme_scheme ON scheme_schemeaccount.scheme_id = scheme_scheme.id
        INNER JOIN
            ubiquity_schemeaccountentry ON scheme_schemeaccount.id = ubiquity_schemeaccountentry.scheme_account_id
        INNER JOIN
            \"user\" ON ubiquity_schemeaccountentry.user_id = \"user\".id
        INNER JOIN
            user_clientapplication ON \"user\".client_id = user_clientapplication.client_id
        WHERE
            (user_clientapplication.name = \'Bink\' OR user_clientapplication.name = \'Barclays Mobile Banking\') AND 
            is_deleted = FALSE AND status = 1
        GROUP BY
            company,
            user_clientapplication.name,
            jsonb_array_length(pll_links) <> 0
    """

    df = pd.read_sql(query, conn)
    comps = ['Harvey Nichols', 'Iceland', 'SquareMeal', 'Wasabi']
    bink_lc = df[
        (df['pll_link']==True) & (df['name']=='Bink') & (df['company'].isin(comps))
        ][['company','cards']].rename(columns={'cards':'Bink'})
    barc_lc = df[
        (df['pll_link']==True) & (df['name']=='Barclays Mobile Banking') & (df['company'].isin(comps))
        ][['company','cards']].rename(columns={'cards':'Barclays'})

    lcs = pd.merge(bink_lc,barc_lc,'outer','company').fillna(0)
    lcs['Barclays'] = lcs['Barclays'].astype(int)

    lcs_label = lcs['company'].tolist()
    lcs_bink = lcs['Bink'].tolist()
    lcs_barc = lcs['Barclays'].tolist()

    return render_template('home.html', 
        labels=labels,bink=bink,barclays=barclays,bink_users=bink_users,barclays_users=barclays_users,
        lcs_label=lcs_label,lcs_bink=lcs_bink,lcs_barc=lcs_barc)

if __name__ == "__main__":
    app.run(debug=True)