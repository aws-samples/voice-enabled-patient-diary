from data_access.outreach_config import OutreachStatus

from data_access.outreach_config import OUTREACH_AFTER_TEXT_USER_DELAY, OUTREACH_AFTER_CALL_USER_DELAY
from data_access.data_config import LOG_LEVEL, SURVEY_TBC_COL
from data_access.survey_completion import get_survey_completion_entry
import boto3
import logging
from collections import namedtuple

logger = logging.getLogger('SymptomReporter')
logger.setLevel(LOG_LEVEL)

sfn_client = boto3.client('stepfunctions')

OutreachNextStep = namedtuple('OutreachNextStep', ['nextStep', 'waitTimeAfterNextStep'])

outreach_map = {
    OutreachStatus.NoOutreach: OutreachNextStep(nextStep='TextPatient',
                                                waitTimeAfterNextStep=OUTREACH_AFTER_TEXT_USER_DELAY),
    OutreachStatus.TextedUser: OutreachNextStep(nextStep='CallPatient',
                                                waitTimeAfterNextStep=OUTREACH_AFTER_CALL_USER_DELAY),
    OutreachStatus.CalledUser: OutreachNextStep(nextStep='TextProvider',
                                                waitTimeAfterNextStep=0),
    OutreachStatus.NotifiedProvider: OutreachNextStep(nextStep=None,
                                                      waitTimeAfterNextStep=0),
}


def lambda_handler(event, context):
    user_id = event['UserId']
    date = event['Date']
    entry = get_survey_completion_entry(user_id, date)
    if SURVEY_TBC_COL not in entry or len(entry[SURVEY_TBC_COL]) == 0:
        logger.info(f'{user_id} completed all surveys for {date}')
        return {
            'completed': True
        }
    # survey not completed. determine next step and wait time
    outreach_status = OutreachStatus(entry.get('Outreach_Status', 'None'))
    logger.info(f'outreach status: {outreach_status}')
    next_step = outreach_map[outreach_status]
    if not next_step.nextStep:
        event['completed'] = True
        return event

    event['completed'] = False
    event['outreach'] = next_step.nextStep
    event['wait'] = {
        'mode': 'SECONDS',
        'seconds': next_step.waitTimeAfterNextStep
    }
    return event
