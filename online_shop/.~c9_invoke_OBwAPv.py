from dash import Dash, html, Input, Output, dcc
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from datetime import datetime
import plotly.express as px
import boto3
import csv
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import pandas as pd
import time

class Table:
    """Encapsulates an Amazon DynamoDB table of employee data."""
    def __init__(self, table):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        :param table_name: The name of the DynamoDB table to use.
        """
        self.table = table

    def new_order(self, customerID, orderID, product, qantity, firstname, lastname, country):
        """
        Updates personal data for an order in the table.

        :param customerID: The unique customer ID to update <Email Address>.
        :param orderID: The orderID to update in form <Year><Month><Day>.
        :param product: The product name <shoes|book|plant>.
        :param quantity: The quantity of ordered product.
        :param firstname: The first name of the customer.
        :param lastname: The last name of the customer.
        :param country: The country of customer order <English Country Name>.
        :return: The fields that were updated, with their new values.
        """
        try:
        # First check if the key exists in the table
            response = self.table.get_item(
                Key={'customerID': customerID},
                ProjectionExpression='customerID'
                )
            if 'Item' not in response:
                response = self.table.put_item(
                    Item = {
                    'customerID': customerID,
                    'orderID': orderID,
                    'product': product,
                    'qantity': qantity,
                    'firstname': firstname,
                    'lastname': lastname,
                    'country': country
                    }
                )
                return response
            else:
                print("customerID already used")
        except ClientError as err:
            logging.error(
                "Couldn't update %s in table %s. Here's why: %s: %s",
                customerID, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
                
    def product_productorders_timerange(self, product):
        """Returns all the orders for a product"""
        response = self.table.query(
            IndexName='Products',
            KeyConditionExpression=Key('product').eq(product)
        )
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = self.table.query(
                IndexName='Products',
                KeyConditionExpression=Attr('product').eq(product),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])
        df = pd.DataFrame(items)
        return df
    
    def get_total_orders(self, product_name):
        """Returns the total number of this Product ordered"""
        response = self.table.query(
            IndexName='Products',
            KeyConditionExpression="product = :product_name",
            ExpressionAttributeValues={
                ":product_name": product_name
            },
            ProjectionExpression='quantity'
        )
        
        total_quantity = sum(int(item['quantity']) for item in response['Items'])
        return total_quantity

table = boto3.resource('dynamodb').Table("Orders")
orders = Table(table)
# Define the initial product and graph heading
input_product = 'plant'
graph_headding = f'Sales of {input_product.capitalize()}.'
# Retrieve the data for the initial product
graph_df = orders.product_productorders_timerange(input_product)
graph_df['orderID'] = pd.to_datetime(graph_df['orderID'], format= '%Y%m%d')
orders_grouped = graph_df.groupby(['orderID', 'product']).sum().reset_index() 
# Create the initial graph
fig = px.line(orders_grouped, x='orderID', y='quantity', color='product')
fig.update_layout(
    xaxis_title='Date',
    yaxis=dict(title='Orders', type='linear')
)
book_orders = orders.get_total_orders('book')
shoes_orders = orders.get_total_orders('shoes')
plant_orders = orders.get_total_orders('plant')
# set 10 second interval
interval = dcc.Interval(
    id='interval-component',
    interval=10*1000,  # update every 10 seconds
    n_intervals=0
)
# Create the Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])

"""
        new_order:
Updates personal data for an order in the table.

        :param customerID: The unique customer ID to update <Email Address>.
        :param orderID: The orderID to update in form <Year><Month><Day>.
        :param product: The product name <shoes|book|plant>.
        :param quantity: The quantity of ordered product.
        :param firstname: The first name of the customer.
        :param lastname: The last name of the customer.
        :param country: The country of customer order <English Country Name>.
        
        :return: The fields that were updated, with their new values.
"""
app.layout = html.Div([
    html.H1('New Order'),
    html.H5('CustomerID <Email Address>, Product <shoes|book|plant>, quantity, first name, last name, country'),
    dcc.Input(id='customerID', placeholder='CustomerID <Email Address>', type='text', style={'text-align': 'center', 'width': '20%'}),
    dcc.Input(id='product', placeholder='Product <shoes|book|plant>', type='text', style={'textAlign': 'center', 'width': '20%'}),
    dcc.Input(id='quantity', placeholder='Enter quantity', type='number', style={'textAlign': 'center', 'width': 'auto'}),
    dcc.Input(id='firstname', placeholder='Enter first name', type='text', style={'textAlign': 'center', 'width': 'auto'}),
    dcc.Input(id='lastname', placeholder='Enter last name', type='text', style={'textAlign': 'center', 'width': 'auto'}),
    dcc.Input(id='country', placeholder='Enter country', type='text', style={'textAlign': 'center', 'width': 'auto'}),
    html.Br(),
    html.Button('Submit', id='submit-button', n_clicks=0, className='btn btn-primary', style={'display': 'block', 'margin-top': '20px'}),
    html.Strong("Please enter new customer order information."),
    html.Div(id='output-message'),
    html.H1(id='product-header'),
    dcc.Graph(id='orders-chart', figure=fig),
    dcc.RadioItems(
        options=[
            {'label': 'Book', 'value': 'book'},
            {'label': 'Shoes', 'value': 'shoes'},
            {'label': 'Plant', 'value': 'plant'}
        ],
        value='plant',
        id='loading-demo-dropdown'
    ),
    dcc.Loading([html.Div(id="loading-demo")]),
    html.Br(),
    html.H1('Overview of Worldwide Product Orders'),
    html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Book"),
                                dbc.CardBody(
                                    [
                                        html.Img(src=app.get_asset_url('book.png'), style={'width': '100%', 'height': '100%', 'object-fit': 'contain'}),
                                    ]
                                ),
                                dbc.CardFooter(html.P(f'Number of orders: {book_orders}', id='book-orders')),
                            ],
                            color="info", 
                            outline=True,
                            style={"width": "100%"},
                            className="my-3",
                        ),
                        width={"size": 3, "order": 3},
                        style={"flex-basis": "calc(33.33% - 20px)"},
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Shoes"),
                                dbc.CardBody(
                                    [
                                        html.Img(src=app.get_asset_url('sneakers.png'), style={'width': '100%', 'height': '100%', 'object-fit': 'contain'}),
                                    ]
                                ),
                                dbc.CardFooter(html.P(f'Number of orders: {shoes_orders}', id='shoes-orders')),
                            ],
                            color="warning", 
                            outline=True,
                            style={"width": "100%"},
                            className="my-3",
                        ),
                        width={"size": 3, "order": 3},
                        style={"flex-basis": "calc(33.33% - 20px)"},
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Plant"),
                                dbc.CardBody(
                                    [
                                        html.Img(src=app.get_asset_url('spider-plant.png'), style={'width': '100%', 'height': '100%', 'object-fit': 'contain'}),
                                    ]
                                ),
                                dbc.CardFooter(html.P(f'Number of orders: {plant_orders}', id='plant-orders')),
                            ],
                            color="primary", 
                            outline=True,
                            style={"width": "100%"},
                            className="my-3",
                        ),
                        width={"size": 3, "order": 3},
                        style={"flex-basis": "calc(33.33% - 20px)"},
                    ),
                ]
            ),
            interval,
        ]
    )
])

@app.callback(
    Output('output-message', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('customerID', 'value'),
     State('product', 'value'),
     State('quantity', 'value'),
     State('firstname', 'value'),
     State('lastname', 'value'),
     State('country', 'value')]
)
def add_order_callback(n_clicks, customerID, product, quantity, firstname, lastname, country):
    if n_clicks > 0:
        if not customerID or not product or not quantity or not firstname or not lastname or not country:
            return 'Please fill in all fields.'
        if product not in ['shoes', 'book', 'plant']:
            return 'Invalid product.'
        if not isinstance(quantity, int):
            return 'Quantity must be an integer.'
        if quantity < 0:
            return 'Quantity must be greater than zero.'
        # Call your pre-written function to add the order to your DynamoDB table
        orderID = datetime.now().strftime('%Y%m%d')
        orders.new_order(customerID, orderID, product, quantity, firstname, lastname, country)
        return 'Order added successfully.'

@app.callback(
    Output('product-header', 'children'),
    [Input('loading-demo-dropdown', 'value')]
)
def update_header(value):
    return f'Sales of {value.capitalize()}.'

@app.callback(
    Output('orders-chart', 'figure'),
    [Input('loading-demo-dropdown', 'value')]
)
def update_chart(value):
    graph_df = orders.product_productorders_timerange(value)
    graph_df['orderID'] = pd.to_datetime(graph_df['orderID'], format= '%Y%m%d')
    orders_grouped = graph_df.groupby(['orderID', 'product']).sum().reset_index()    
    fig = px.line(orders_grouped, x='orderID', y='quantity', color='product')
    fig.update_layout(
    xaxis_title='Date',
    yaxis=dict(title='Orders', type='linear')
    )
    fig.update_traces(fill='tozeroy', fillcolor='blue', opacity=0.5)

    return fig

@app.callback(Output('book-orders', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_book_orders(n):
    book_orders = orders.get_total_orders('book')
    return f'Number of orders: {book_orders}'

@app.callback(Output('shoes-orders', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_shoes_orders(n):
    shoes_orders = orders.get_total_orders('shoes')
    return f'Number of orders: {shoes_orders}'

@app.callback(Output('plant-orders', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_plant_orders(n):
    plant_orders = orders.get_total_orders('plant')
    return f'Number of orders: {plant_orders}'

if __name__ == '__main__':
    app.run_server(debug=True)
    