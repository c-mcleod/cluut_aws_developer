import boto3
import csv

class Employee:
    """Encapsulates an Amazon DynamoDB table of employee data."""
    def __init__(self, table):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        :param table_name: The name of the DynamoDB table to use.
        """
        self.table = table
        
        
    def batch_emp(self, file):
        """Take a .csv file and update it's contents to the table"""
        with open(file, 'r') as f:
            new_emps = csv.DictReader(f)
            with self.table.batch_writer() as batch:
                for row in new_emps:
                    item = {
                        'customerID': row['customerID'],
                        'orderID': row['orderID'],
                        'product': row['product'],
                        'quantity': row['quantity'],
                        'firstname': row['firstname'],
                        'lastname': row['lastname'],
                        'country': row['country']
                    }
                    batch.put_item(Item=item)
    
    
    
if __name__ == "__main__":
    table = boto3.resource('dynamodb').Table("Orders")
    orders = Employee(table)
    
    orders.batch_emp('order_data.csv')