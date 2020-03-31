import boto3
import os


iam = boto3.client('iam')
paginator = iam.get_paginator('list_users')
for response in paginator.paginate():
    for user in response['Users']:
        print(user['UserName'])
