import json
import os

import boto3 as boto3
from sqlalchemy import create_engine, text, MetaData, Integer, Column, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}  # specify the schema here

    id = Column(UUID(as_uuid=True), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    status = Column(String)
    alert_status = Column(String)
    reset_key = Column(String)


class UserCredential(Base):
    __tablename__ = 'user_credentials'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    password = Column(String)
    temp_password = Column(String)




def lambda_handler(event, context):
    try:
        user_id = event.get('user_id')
        if user_id is None:
            return {
                'statusCode': 400,
                'body': 'Error: user_id not present in the payload.'
            }
        
        host = event.get('DB_HOST')
        database = event.get('DB_DATABASE')
        user = event.get('DB_USER')
        password = event.get('DB_PASSWORD')
        port = event.get('DB_PORT')
        schema = event.get('DB_SCHEMA')
        base_url = event.get('BaseUrl')
        print(event)
        if host == 'localhost':  ## for testing
            print('local testing')
            host = 'host.docker.internal'
        # create sql alchemy engine
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')

        Session = sessionmaker(bind=engine)
        session = Session()

        user = session.query(User).get(user_id)

        recipient_email = user.email  # Replace with the recipient's email address

        # Define the message_data that corresponds to the placeholders in your template
        message_data = {
            # Update the message_data with the new template variables as needed
            'full_name': f'{user.first_name} {user.last_name}',
            'message_mailData_passwordChangeURL': '',
            'email':user.email

        }

        ses_region = 'us-east-2'  # Replace with your desired SES region

        try:
            response = send_email_with_template(recipient_email, message_data, ses_region)
            print("Email sent successfully!")
            print("Message ID:", response['MessageId'])
            return {
                'statusCode': 200,
                'body': response
            }

        except Exception as e:
            print("Error sending email:", str(e))
            return {
                'statusCode': 500,
                'body': str(e)
            }
    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }


def send_email_with_template(recipient_email, message_data, region):
    ses_client = boto3.client('ses', region_name=region)


    response = ses_client.send_email(
        Source='alerts@therapydesk.com',  # Replace with your SES-verified sender email address
        Destination={
            'ToAddresses': [recipient_email]
        },
        Message={
            'Subject': {
                'Data': 'Therapy Desk : Reset your password'
            },
            'Body': {
                # 'Text': {
                #     'Data': text_body
                # },
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
