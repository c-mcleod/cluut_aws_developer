import boto3
import logging
from botocore.exceptions import ClientError
import csv
from boto3.dynamodb.conditions import Attr

class Employee:
    """Encapsulates an Amazon DynamoDB table of employee data."""
    def __init__(self, table):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        :param table_name: The name of the DynamoDB table to use.
        """
        self.table = table
    
    
    def update_employee(self, LoginAlias, ManagerLoginAlias='', FirstName='', LastName='', Skills=[]):
        """
        Updates personal data for an employee in the table.

        :param LoginAlias: The login alias of the employee to update.
        :param ManagerLoginAlias: The manager of the employee to update.
        :param FirstName: The first name to the give the employee.
        :param LastName: The last name to give the employee.
        :param Skills: The skills to give the employee.
        :return: The fields that were updated, with their new values.
        """
        try:
        # First check if the key exists in the table
            response = self.table.get_item(
                Key={'LoginAlias': LoginAlias},
                ProjectionExpression='LoginAlias'
                )
            if 'Item' not in response:
                response = self.table.put_item(
                    Item = {
                    'LoginAlias': LoginAlias,
                    'ManagerLoginAlias': ManagerLoginAlias,
                    'FirstName': FirstName,
                    'LastName': LastName,
                    }
                )
            else:
                print("Employee LoginAlias already used")
        except ClientError as err:
            logging.error(
                "Couldn't update %s in table %s. Here's why: %s: %s",
                LoginAlias, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
                

    def batch_emp(self, file):
        """Take a .csv file and update it's contents to the table"""
        with open(file, 'r') as f:
            new_emps = csv.DictReader(f)
            with self.table.batch_writer() as batch:
                for row in new_emps:
                    item = {
                        'LoginAlias': row['LoginAlias'],
                        'FirstName': row['FirstName'],
                        'LastName': row['LastName'],
                        'ManagerLoginAlias': row['ManagerLoginAlias']
                    }
                    batch.put_item(Item=item)
    
    def select_table(self):
        """returns all items from table"""
        response = self.table.scan()
        return response['Items']
    # response_scan = client_statment(Statment='SELECT * FROM Empolyee')
    
    def select_item(self, LoginAlias):
        """Returns LoginAlais item"""
        response = self.table.get_item(
            Key={
                'LoginAlias': LoginAlias
            }
        )
        print(response['Item'])
    # response_diego = table.get_item(Key={"LoginAlias": "diegor"})
    # response_diego = client.execute_statment(Statment='SELECT * FROM Employee WHERE LoginAlias = \'diegor\'')
    
    def get_employees_with_manager(self, manager_alias):
        response = self.table.scan(
            FilterExpression=Attr('ManagerLoginAlias').eq(manager_alias)
        )
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = self.table.query(
                FilterExpression=Attr('ManagerLoginAlias').eq(manager_alias),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])
        return items
        # responsae_manager = client.execute_statment(Statment='SELECT FirstName FROM Employee.DirectReports WHERE ManagerLoginAlias =\'johns\'')
    
    def insert_new_employee(self, LoginAlias, ManagerLoginAlias, FirstName, LastName, Skills):
        """Inserts new employee into table"""
        response = self.table.put_item(
            Item = { 
                'LoginAlias': LoginAlias,
                'ManagerLoginAlias': ManagerLoginAlias,
                'FirstName' : FirstName,
                'LastName' : LastName,
                'Skills' : {Skills}
            }
        )
        return response

    
    def update_employee_skills(self, LoginAlias, Skills):
        """Updates exsisting employee record"""
        response = self.table.update_item(
            Key={'LoginAlias': LoginAlias},
            UpdateExpression="ADD Skills :s",
            ExpressionAttributeValues={':s': set(Skills)}
        )
        return response
    # response_update = client.execute_statement(Statment="UPDATE Employee SET Skills =set_add(Skills, <<\'operation\">>) WHERE LoginAlias = \'mateoj\'")
if __name__ == "__main__":
    table = boto3.resource('dynamodb').Table("Employee")
    emp = Employee(table)
    # emp.update_employee('mariok', 'marthar', 'Kauer', 'Mario', [])
            
    # emp.batch_emp('employee.csv')
    
    # employee_tab = emp.select_table()
    # for emps in employee_tab:
    #     print(emps)
    
    # print(emp.select_item('diegor'))
    
    # u_john = emp.get_employees_with_manager('johns')
    # for emp in u_john:
    #     print(emp)
    
    # print(emp.insert_new_employee('sarahk', 'marthar', 'Sarah', 'Klein', 'software'))
    
    # print(emp.update_employee_skills('mateoj', ['operations']))