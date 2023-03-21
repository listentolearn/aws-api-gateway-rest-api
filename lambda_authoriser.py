def lambda_handler(event, context):
    
    if event['authorizationToken'] == '1234':
        auth_status = 'Allow'
    else:
        auth_status = 'Deny'
    
    authResponse = {
        'policyDocument': { 
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Resource': [
                        event['methodArn']
                    ], 
                    'Effect': auth_status
                }
            ]
        }
    }
    return authResponse
