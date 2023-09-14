import boto3
import csv
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import pandas as pd

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
    
    def customer_list(self):
        """Returns a list of all customer IDs."""
        response = self.table.query(
            IndexName='CustomerName',
            ProjectionExpression='CustomerID, lastname',
            ScanIndexForward=True
        )
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = self.table.query(
                IndexName='CustomerName',
                ProjectionExpression='customerID, lastname',
                ExclusiveStartKey=response['LastEvaluatedKey'],
                ScanIndexForward=True
            )
            items.extend(response['Items'])
        customer_ids = pd.DataFrame(items)
        return customer_ids    
    
    def first_names(self, customerID):
        if customerID:
            response = table.query(
                KeyConditionExpression=Key('customerID').eq(customerID)
            )
            firstnames = list(set([item['firstname'] for item in response['Items']]))
            return [{'label': name, 'value': name} for name in firstnames]
        else:
            return []
    
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
    
if __name__ == "__main__":
    table = boto3.resource('dynamodb').Table("Orders")
    orders = Table(table)
    
    # products = orders.product_productorders_timerange('book')
    # print(products)
    
    # products = ['book', 'shoes', 'plant']
    # for product in products:
    #     total_quantity = orders.get_total_orders(product)
    #     print(f"Total orders for {product}: {total_quantity}")
    
    
    # print(orders.customer_list())

    print(orders.get_customer_info('td@shoes.de'))




