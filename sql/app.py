import MySQLdb
from sqlalchemy import create_engine, text
import pandas as pd
import boto3
from botocore.exceptions import ClientError
import json
from dash import Dash, html, dcc
import plotly.express as px
import plotly.io as pio
import country_converter as coco

def get_secret(secret_name, region_name):
    """Returns the password for secret_name/region"""
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


secret = get_secret("mysql_classicmodels_db", "eu-central-1")

username = secret["username"]
password = secret["password"]
host = secret["host"]
port = "3306"
database = "webapp-db"

engine = create_engine(f"mysql+mysqldb://{username}:{password}@{host}:{port}/classicmodels")
connection = engine.connect()

def dist_orders_mnt():
    """Returns the distribution of orders per month."""
    stmt = text("SELECT COUNT(orderNumber) as Orders, DATE_FORMAT(orderDate, '%M %Y') as Month FROM orders GROUP BY YEAR(orderDate), MONTH(orderDate)")
    dist_orders_pd = pd.read_sql(stmt, connection)
    return dist_orders_pd

def best_customers():
    """Returns the best customers based on most orders."""
    stmt = text("SELECT customerName as Customer, COUNT(orderNumber) as Orders FROM orders INNER JOIN customers USING (customerNumber) GROUP BY customerName ORDER BY COUNT(orderNumber) DESC LIMIT 10")
    best_customers_pd = pd.read_sql(stmt, connection)
    return best_customers_pd

def best_rep():
    """Returns the busiest sales rep based on most customers."""
    stmt = text("SELECT firstName AS First_Name, lastName AS Last_Name, employeeNumber, COUNT(salesRepEmployeeNumber) AS Number_Customers FROM customers INNER JOIN employees ON salesRepEmployeeNumber = employeeNumber GROUP BY employeeNumber ORDER BY COUNT(salesRepEmployeeNumber) DESC LIMIT 10")
    busiest_sales_rep_pd = pd.read_sql(stmt, connection)
    return busiest_sales_rep_pd

def customer_overview():
    """Returns the customer Overview with number of customers per land"""
    stmt = text("SELECT country AS Country, COUNT(customerNumber) AS Number_of_Customers FROM customers GROUP BY country ORDER BY country")
    customer_overview_pd = pd.read_sql(stmt, connection)
    return customer_overview_pd

def customer_co_overview():
    """Returns the customer Overview with number of customers per land on map"""
    stmt = text("SELECT country AS Country, COUNT(customerNumber) AS Number_of_Customers FROM customers GROUP BY country ORDER BY country")
    customer_overview_df = pd.read_sql(stmt, connection)
    cc= coco.CountryConverter()
    customer_overview_df['Country'] = cc.convert(names=customer_overview_df['Country'], to='ISO3')
    return customer_overview_df


app = Dash(__name__)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
    }
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
do_df = dist_orders_mnt()
fig1 = px.bar(do_df, x="Month", y="Orders", barmode="group")
fig1.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

bc_df = best_customers()
fig2 = px.bar(bc_df, x="Customer", y="Orders", barmode="group")
fig2.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

br_df = best_rep()
fig3 = px.bar(br_df, x="Last_Name", y="Number_Customers", barmode="group")
fig3.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

co_df = customer_overview()
fig4 = px.bar(co_df, x="Country", y="Number_of_Customers", barmode="group")
fig4.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

co_map_df = customer_co_overview()
fig5 =  px.scatter_geo(co_map_df,
            locations='Country', 
            color='Number_of_Customers',
            projection='natural earth', 
            hover_name='Country',
            title='Number of Customers per Country')


app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.Div([
        html.Div([
            html.H1(
                children='Distribution of orders per month',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }
            ),

            dcc.Graph(
                id='graph-1',
                figure=fig1
            ),
        ], className='six columns'),

        html.Div([
            html.H1(
                children='Best customers based on most orders.',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }
            ),
        
            dcc.Graph(
                id='graph-2',
                figure=fig2
            )
        ], className='six columns'),
    ], className='row'),
    
    html.Div([
        html.Div([
            html.H1(
                children='Busiest sales rep based on most customers',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }
            ),
        
            dcc.Graph(
                id='example-graph-3',
                figure=fig3
            )
        ], className='six columns'),
        
        html.Div([
            html.H1(
                children='Customer Overview with number of customers per land',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }
            ),
        
            dcc.Graph(
                id='example-graph-5',
                figure=fig5
            )
        ], className='six columns'),
    ], className='row')
])

if __name__ == '__main__':
    app.run_server(debug=True)