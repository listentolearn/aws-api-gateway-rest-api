# aws-api-gateway-rest-api

This repository consists of lambda function code in python 3.8 that enables you to handle api requests from api gateway. It also includes json swagger documentation of a basic CRUD API along with the iam policy to be attached with the lambda. 

## Things to do

1. Add two environment variables to the lambda function.
    1. DYNAMODB_TABLE - DynamoDB table name
    2. HASH_KEY - DynamoDB hash key name
2. Add a new role with the policy (use the contents of the lambda-policy.json) and attach it as the execution role of the lambda. Replace the <accountId> with actual account id, <bucketName> with actual s3 bucket name and <tableName> with actual DynamoDB table name within the file.
3. The zip file Archive.zip contains the lambda function along with the dependant python 3.8 packages which can be uploaded to the lambda function code. If you are using a different python version, please use the corresponding packages.
