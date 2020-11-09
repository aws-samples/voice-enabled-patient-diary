
import boto3
from botocore.exceptions import ClientError
from data_access.data_config import PINPOINT_KEYWORD, PINPOINT_ORIGIN_NUMBER, PINPOINT_PROJECT_ID, PINPOINT_REGION, \
    PINPOINT_SENDER_ID, LOG_LEVEL
import logging

logger = logging.getLogger('SendSMS')
logger.setLevel(LOG_LEVEL)

pinpoint_client = boto3.client('pinpoint', region_name=PINPOINT_REGION)


def send_sms(destination_number, message):
    try:
        response = pinpoint_client.send_messages(
            ApplicationId=PINPOINT_PROJECT_ID,
            MessageRequest={
                'Addresses': {
                    destination_number: {
                        'ChannelType': 'SMS'
                    }
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'Keyword': PINPOINT_KEYWORD,
                        'MessageType': 'TRANSACTIONAL',
                        'OriginationNumber': PINPOINT_ORIGIN_NUMBER,
                        'SenderId': PINPOINT_SENDER_ID
                    }
                }
            }
        )

    except ClientError as e:
        logger.error(f'Sending SMS to {destination_number} failed.')
        logger.error(e.response['Error']['Message'])
    else:
        logger.info(f"Message sent success to {destination_number}!"
                    f" Message ID: {response['MessageResponse']['Result'][destination_number]['MessageId']}")
