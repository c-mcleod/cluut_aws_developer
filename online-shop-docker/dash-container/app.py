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

    def new_order(self, customerID, orderID, product, quantity, firstname, lastname, country):
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
            response = self.table.update_item(
                Key={
                    'customerID': customerID,
                    'orderID': orderID
                },
                UpdateExpression='set product=:p, quantity=:q, firstname=:f, lastname=:l, country=:c',
                ExpressionAttributeValues={
                    ':p': product,
                    ':q': quantity,
                    ':f': firstname,
                    ':l': lastname,
                    ':c': country
                },
                ReturnValues='UPDATED_NEW'
            )
            return response
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
    
    def get_customerIDs(self):
        """
        Returns a list of customerIDs available in the table.
        """
        customerIDs = set()
        for product in ['book', 'shoes', 'plant']:
            response = self.table.query(
                IndexName='Products',
                KeyConditionExpression=Key('product').eq(product),
                ProjectionExpression='customerID'
            )
            for item in response['Items']:
                customerIDs.add(item['customerID'])
            while 'LastEvaluatedKey' in response:
                response = self.table.query(
                    IndexName='Products',
                    KeyConditionExpression=Key('product').eq(product),
                    ProjectionExpression='customerID',
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                for item in response['Items']:
                    customerIDs.add(item['customerID'])
        return sorted(list(customerIDs))
    
    def get_customer_info(self, customerID):
        response = self.table.query(
            KeyConditionExpression=Key('customerID').eq(customerID)
        )
        items = response['Items']
        if not items:
            return None
        customer_info = items[0]
        return {
            'customerID': customer_info['customerID'],
            'firstname': customer_info['firstname'],
            'lastname': customer_info['lastname'],
            'country': customer_info['country']
        }

table = boto3.resource('dynamodb').Table("Orders")
orders = Table(table)
# Set Popover
popover_children = "This fills first/last name and country for selected custommerID. !!!Don't forget product and quantity!!!"
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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])

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
server = app.server  # Make the app callable for Gunicorn

app.layout = dbc.Container([
    html.H1('New Order Entry'),
    html.H5('CustomerID <Email Address>, Product <shoes|book|plant>, quantity, first name, last name, country'),
    html.Div([
        dcc.Dropdown(id='customerID', placeholder='CustomerID <Email>', style={'display': 'inline-block', 'width': '200px'},
            options=[{'label': i, 'value': i} for i in orders.get_customerIDs()],
            value=orders.get_customerIDs()[0] if orders.get_customerIDs() else ''
        ),
        dcc.Dropdown(id='product', options=[
            {'label': 'Shoes', 'value': 'shoes'},
            {'label': 'Book', 'value': 'book'},
            {'label': 'Plant', 'value': 'plant'}
        ], placeholder='Select a product', style={'display': 'inline-block', 'width': '160px', 'textAlign': 'center'}),
        dcc.Input(id='quantity', placeholder='Enter quantity', type='number', style={'textAlign': 'center', 'width': 'auto'}),
        dcc.Input(
            id='firstname', 
            placeholder='Enter first name', type='text', 
            style={'display': 'inline-block', 'width': 'auto', 'textAlign': 'center'},
        ),
        dcc.Input(id='lastname', placeholder='Enter last name', type='text', style={'display': 'inline-block','textAlign': 'center', 'width': 'auto'}),
        dcc.Input(id='country', placeholder='Enter country', type='text', style={'display': 'inline-block','textAlign': 'center', 'width': 'auto'}),
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'center'}),
    html.Div([
        dbc.Button('Auto-fill', id='Auto-fill', n_clicks=0, className="me-1", style={'display': 'inline-block', 'margin-top': '20px', 'margin-right': '20px'}),
        dbc.Popover(popover_children, target="Auto-fill", body=True, trigger="hover"),
        html.Button('Submit', id='submit-button', n_clicks=0, className='btn btn-primary', style={'display': 'inline-block', 'margin-top': '20px', 'margin-right': '20px', 'margin-left': '20px'}),
        html.Button('Clear', id='clear-button', n_clicks=0, className='btn btn-primary', style={'display': 'inline-block', 'margin-top': '20px'}),
    ]),
    html.Strong("Please enter new customer order information."),
    html.Div(id='output-message'),
    html.Br(),
    html.H1(id='product-header'),
    dcc.Graph(id='orders-chart', figure=fig),
    dcc.RadioItems(
        options=[
            {'label': 'Book', 'value': 'book'},
            {'label': 'Shoes', 'value': 'shoes'},
            {'label': 'Plant', 'value': 'plant'}
        ],
        value='plant',
        id='loading-demo-dropdown',
        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
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
    [Output('customerID', 'value'),
     Output('product', 'value'),
     Output('quantity', 'value'),
     Output('firstname', 'value'),
     Output('lastname', 'value'),
     Output('country', 'value'),
     Output('output-message', 'children')],
    [Input('Auto-fill', 'n_clicks'),
     Input('submit-button', 'n_clicks'),
     Input('clear-button', 'n_clicks')],
    [State('customerID', 'value'),
     State('product', 'value'),
     State('quantity', 'value'),
     State('firstname', 'value'),
     State('lastname', 'value'),
     State('country', 'value')],
)
def update_customer_info_and_add_order_and_clear_fields(n_clicks_autofill, n_clicks_submit, n_clicks_clear, customerID, product, quantity, firstname, lastname, country):
    triggered_input = dash.callback_context.triggered[0]['prop_id']
    
    if triggered_input == 'Auto-fill.n_clicks':
        if n_clicks_autofill > 0 and customerID:
            customer_info = orders.get_customer_info(customerID)
            if customer_info:
                firstname = customer_info['firstname']
                lastname = customer_info['lastname']
                country = customer_info['country']
                return customerID, product, quantity, firstname, lastname, country, ''
        return customerID, product, quantity, '', '', '', ''
    
    elif triggered_input == 'submit-button.n_clicks':
        if n_clicks_submit > 0:
            if not customerID or not product or not quantity or not firstname or not lastname or not country:
                return [customerID, product, quantity, firstname, lastname, country, 'Please fill in all fields']
            if product not in ['shoes', 'book', 'plant']:
                return 'Invalid product.'
            if not isinstance(quantity, int):
                return 'Quantity must be an integer.'
            if quantity <= 0:
                return 'Quantity must be greater than zero.'
            # Call your pre-written function to add the order to your DynamoDB table
            orderID = datetime.now().strftime('%Y%m%d')
            response = orders.new_order(customerID, orderID, product, quantity, firstname, lastname, country)
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return '', '', None, '', '', '', 'Order added successfully.'
            else:
                return customerID, product, quantity, firstname, lastname, country, '!!!There was a problem - Your order has not been placed.!!!'
    
    elif triggered_input == 'clear-button.n_clicks':
        return '', '', None, '', '', '', ''
    
    else:
        return customerID, product, quantity, firstname, lastname, country, ''
    
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

@app.callback(
    [Output('book-orders', 'children'),
     Output('shoes-orders', 'children'),
     Output('plant-orders', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_orders(n):
    products = ['book', 'shoes', 'plant']
    order_counts = [orders.get_total_orders(p) for p in products]
    order_outputs = [f'Number of orders: {c}' for c in order_counts]
    return order_outputs

if __name__ == '__main__':
    app.run_server(debug=True)
    
    