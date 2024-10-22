# Email Service Lambda Functions

This repository contains AWS Lambda functions for handling email operations in the Therapy Desk application.

## Functions

### 1. Welcome Email Verification
- Function Name: `send-verification-email`
- Triggers on user registration
- Sends email verification link to new users
- Updates user status in database
- Handles verification tracking

### 2. Password Reset Email
- Function Name: `send-reset-password-email`
- Handles password reset requests
- Sends secure reset links
- Manages reset attempts and rate limiting

## Prerequisites
- AWS Account
- AWS Lambda access
- AWS SES configured
- PostgreSQL database

## Dependencies
Required Python packages (included in `/dependencies`):
```
boto3==1.34.11
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
```

## Deployment Steps

1. Install dependencies locally:
```bash
pip install -r requirements.txt -t dependencies/
```

2. Create deployment package:
- Copy Lambda function code to root directory
- Copy `dependencies` folder
- Zip everything together:
```bash
zip -r lambda-deploy.zip .
```

3. Upload to AWS Lambda:
- Create new Lambda function
- Upload `lambda-deploy.zip`
- Set environment variables:
  - DB_HOST
  - DB_DATABASE
  - DB_USER
  - DB_PASSWORD
  - DB_PORT
  - DB_SCHEMA

## Configuration
- Runtime: Python 3.9
- Memory: 128 MB (adjustable)
- Timeout: 30 seconds
- Handler: `lambda_function.lambda_handler`

## Testing
Include following test event format:
```json
{
  "DB_HOST": "your-host",
  "DB_DATABASE": "your-database",
  "DB_USER": "your-user",
  "DB_PASSWORD": "your-password",
  "DB_PORT": "your-port",
  "DB_SCHEMA": "your-schema"
}
```

## Note
Make sure AWS SES email addresses are verified before testing.