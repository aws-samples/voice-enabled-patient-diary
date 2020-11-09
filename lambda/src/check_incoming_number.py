from common import lex_helper as helper

from data_access.data_config import LOG_LEVEL
import logging
import json

logger = logging.getLogger('IncomingNumberCheck')
logger.setLevel(LOG_LEVEL)


def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event, indent=2))
    user = helper.lookup_user(event['Details']['Parameters'])
    if user is None:
        logger.info('incoming number not registered.')
        return {'NumberRegistered': "NotRegistered"}
    else:
        logger.info(f'found registered number for {user.uid}')
        return {'NumberRegistered': "Registered"}
