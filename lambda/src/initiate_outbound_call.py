import boto3
import os
import logging
import json
from data_access.user_profile import lookup_user_by_id
from data_access.ddb_util import DDBUpdateBuilder
from data_access.data_config import LOG_LEVEL, OUTREACH_STATUS_COL, SURVEY_COMPLETION_TABLE
from data_access.outreach_config import OutreachStatus

CONNECT_INSTANCE_ID = os.getenv('CONNECT_INSTANCE_ID', None)
CONNECT_FLOW_ID = os.getenv('CONNECT_FLOW_ID', None)
SOURCE_NUMBER = os.getenv('SOURCE_NUMBER', None)
connect_client = boto3.client('connect')

logger = logging.getLogger('InitiateOutboundCall')
logger.setLevel(LOG_LEVEL)


def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event, indent=2))
    user_id = event['UserId']
    date = event['Date']

    user = lookup_user_by_id(user_id)
    if not user:
        raise AttributeError(f'Could not find user by id of {user_id}')
    logger.debug(f'found user number: {user.phone}')
    response = connect_client.start_outbound_voice_contact(
        DestinationPhoneNumber=user.phone,
        ContactFlowId=CONNECT_FLOW_ID,
        InstanceId=CONNECT_INSTANCE_ID,
        SourcePhoneNumber=SOURCE_NUMBER,
        Attributes={}
    )

    logger.info('connect response event: %s', json.dumps(response, indent=2))
    logger.info('successfully initiated outbound call.')

    outreach_status = OutreachStatus.CalledUser.value
    with DDBUpdateBuilder(
            key={'Patient_ID': user_id, 'Report_Date': date},
            table_name=SURVEY_COMPLETION_TABLE) as ddb_update_builder:
        ddb_update_builder.update_attr(OUTREACH_STATUS_COL, outreach_status)

    event[OUTREACH_STATUS_COL] = outreach_status
    return event
