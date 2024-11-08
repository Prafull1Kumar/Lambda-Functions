import json
import boto3 as boto3
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

# Create base class for SQLAlchemy models
Base = declarative_base()


# Define User model corresponding to the users table in database
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}  # Specify the database schema

    # Define table columns
    id = Column(UUID(as_uuid=True), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    status = Column(String)


def lambda_handler(event, context):
    print('starting processing')
    
    # Extract database configuration from event
    host = 'localhost'
    database = 'app'
    user = 'postgres'
    password = 'Pra@1ful'
    port = '5432'
    print(event)

    # Handle local testing scenario
    if host == 'localhost':
        print('local testing')
        host = 'host.docker.internal'

    # Create database connection
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query users with 'PROCESSING' status
    users = session.query(User).filter(User.status == 'PROCESSING').all()
    
    # Initialize dictionaries to track success and errors
    errors = {}
    success = {}

    # Process each user
    for user in users:
        recipient_email = user.email
        verification_url = ''  # URL should be generated based on your verification system
        
        # Prepare email template data
        message_data = {
            'message_mailData_name': f'''{user.first_name} {user.last_name}''',
            'message_mailData_verificationURL': verification_url
        }

        # Set AWS SES region
        ses_region = 'us-east-2'

        try:
            # Send verification email
            response = send_email_with_template(recipient_email, message_data, ses_region)
            print("Email sent successfully!")
            print("Message ID:", response['MessageId'])
            print(response)
            
            # Record successful email send
            success[recipient_email] = response
            
            # Update user status to 'NOT_VERIFIED'
            user.status = 'NOT_VERIFIED'
            session.commit()

        except Exception as e:
            # Handle and record any errors
            print("Error sending email:", str(e))
            errors[recipient_email] = e

    # Return response with success and error information
    return {
        'statusCode': 200,
        'body': json.dumps({'success': success, 'errors': errors})
    }


# Function to send email using AWS SES
def send_email_with_template(recipient_email, message_data, region):
    # Initialize SES client
    ses_client = boto3.client('ses', region_name=region)

    # Send email using SES
    response = ses_client.send_email(
        Source='alert@therapydesk.com',  # Sender email address
        Destination={
            'ToAddresses': [recipient_email]
        },
        Message={
            'Subject': {
                'Data': 'Welcome to Therapy Desk - Please Verify Your Account'
            },
            'Body': {
                'Html': {
                    'Data': f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <div style="margin:0;padding:0;background:#fff;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif">
        <p style="font-size:14px;">
            Dear <b>{message_data.get('message_mailData_name')}</b>,
        </p>
        <p style="font-size:14px;">
            Welcome to Therapy Desk! We're excited to have you join our community of mental health professionals.
        </p>
        <p style="font-size:14px;">
            To get started, please verify your account by clicking on the link below:
        </p>
        <p style="font-size:14px;">
            <a href="{message_data.get('message_mailData_verificationURL')}" target="_blank">Verify Your Account</a>
        </p>
        <p style="font-size:14px;">
            Once verified, you can set up your practitioner profile and explore our scheduling tools.
        </p>
        <p style="font-size:14px;">
            If you need any assistance, our support team is here for you at <a href="mailto:support@therapydesk.com">support@therapydesk.com</a>.
        </p>
        <p style="font-size:14px;">
            We hope Therapy Desk helps streamline your practice management!
        </p>
        <p style="font-size:14px;">
            Best regards,<br>
            The Therapy Desk Team
        </p>
    </div>
</body>
</html>
'''
                }
            }
        }
    )
    return response
