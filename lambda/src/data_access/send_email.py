
import boto3
from botocore.exceptions import ClientError
from data_access.data_config import PINPOINT_PROJECT_ID, PINPOINT_REGION, PINPOINT_EMAIL_SENDER, LOG_LEVEL
import logging
import json

logger = logging.getLogger('SendEmail')
logger.setLevel(LOG_LEVEL)

pinpoint_client = boto3.client('pinpoint', region_name=PINPOINT_REGION)

# The character encoding that you want to use for the subject line and message
# body of the email.
CHARSET = "UTF-8"


def send_email(destination_email, subject, body_text, body_html):
    try:
        response = pinpoint_client.send_messages(
            ApplicationId=PINPOINT_PROJECT_ID,
            MessageRequest={
                'Addresses': {
                    destination_email: {
                        'ChannelType': 'EMAIL'
                    }
                },
                'MessageConfiguration': {
                    'EmailMessage': {
                        'FromAddress': PINPOINT_EMAIL_SENDER,
                        'SimpleEmail': {
                            'Subject': {
                                'Charset': CHARSET,
                                'Data': subject
                            },
                            'HtmlPart': {
                                'Charset': CHARSET,
                                'Data': body_text
                            },
                            'TextPart': {
                                'Charset': CHARSET,
                                'Data': body_html
                            }
                        }
                    }
                }
            }
        )
    except ClientError as e:
        logger.error(f'Sending email to {destination_email} failed.')
        logger.error(e.response['Error']['Message'])
    else:
        logger.info("Message sent! " + json.dumps(response['MessageResponse']['Result']))
