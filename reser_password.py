# Import required libraries
import json
import os
import boto3 as boto3
from sqlalchemy import create_engine, text, MetaData, Integer, Column, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

# Create base class for SQLAlchemy models
Base = declarative_base()


# Define User model for the users table
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}  # Set database schema

    # Define user table columns
    id = Column(UUID(as_uuid=True), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    status = Column(String)
    alert_status = Column(String)
    reset_key = Column(String)  # Stores password reset token


# Define UserCredential model for storing user authentication data
class UserCredential(Base):
    __tablename__ = 'user_credentials'
    __table_args__ = {'schema': 'public'}

    # Define credential table columns
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), index=True)  # Indexed for faster lookups
    password = Column(String)  # Stores hashed password
    temp_password = Column(String)  # Stores temporary password during reset


# Main Lambda handler for password reset email functionality
def lambda_handler(event, context):
    try:
        # Extract user_id from event and validate
        user_id = event.get('user_id')
        if user_id is None:
            return {
                'statusCode': 400,
                'body': 'Error: user_id not present in the payload.'
            }
        
        # Extract database configuration from event
        host = event.get('DB_HOST')
        database = event.get('DB_DATABASE')
        user = event.get('DB_USER')
        password = event.get('DB_PASSWORD')
        port = event.get('DB_PORT')
        schema = event.get('DB_SCHEMA')
        base_url = event.get('BaseUrl')
        print(event)

        # Handle local testing environment
        if host == 'localhost':
            print('local testing')
            host = 'host.docker.internal'

        # Initialize database connection
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
        Session = sessionmaker(bind=engine)
        session = Session()

        # Fetch user details from database
        user = session.query(User).get(user_id)

        # Prepare email data
        recipient_email = user.email
        message_data = {
            'full_name': f'{user.first_name} {user.last_name}',
            'message_mailData_passwordChangeURL': '',  # Password reset URL should be generated
            'email': user.email
        }

        # Set AWS SES region
        ses_region = 'us-east-2'

        try:
            # Send password reset email
            response = send_email_with_template(recipient_email, message_data, ses_region)
            print("Email sent successfully!")
            print("Message ID:", response['MessageId'])
            return {
                'statusCode': 200,
                'body': response
            }

        except Exception as e:
            # Handle email sending errors
            print("Error sending email:", str(e))
            return {
                'statusCode': 500,
                'body': str(e)
            }
    except Exception as e:
        # Handle general errors
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }


# Function to send password reset email using AWS SES
def send_email_with_template(recipient_email, message_data, region):
    # Initialize SES client
    ses_client = boto3.client('ses', region_name=region)

    # Send email using SES
    response = ses_client.send_email(
        Source='alerts@therapydesk.com',  # Sender email address
        Destination={
            'ToAddresses': [recipient_email]
        },
        Message={
            'Subject': {
                'Data': 'Therapy Desk : Reset your password'
            },
            'Body': {
               
                'Html': {
                    'Data': f'''<!DOCTYPE html>
<html>

<head>
    <meta charset=\"UTF-8\">
</head>

<body>
    <div style=\"margin:0;padding:0;background:#fff;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif\"></div>
    <p style=\"padding: 0 0 10px 0; font-size:14px;\">Dear <b>{message_data.get('full_name')}</b>,</p>
    <p style=\"padding: 0 0 10px 0; font-size:14px;\">We received a request to reset your Therapy Desk account's password for
        {message_data.get('email')}.<br>Reset your password by clicking the link below</p><a
        href={message_data.get('message_mailData_passwordChangeURL')} target=\"_blank\">Reset Password</a>
    <p style=\"padding: 0 0 10px 0; font-size:14px;\">Thanks & Regards!<br>Therapy Desk team</p>
</body>

</html>
'''
                }
            }
        }
    )
    return response
