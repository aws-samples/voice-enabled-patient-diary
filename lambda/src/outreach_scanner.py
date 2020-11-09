from data_access.data_config import TRIAL_CONFIG_TABLE, SURVEY_COMPLETION_TABLE, LOG_LEVEL, parse_date_from_str, \
    format_date_to_str, OUTREACH_WORKFLOW
from data_access.ddb_util import get_item_ddb, DDBUpdateBuilder, scan_item_ddb
from data_access import user_profile
from data_access.survey_completion import initialize_survey_to_complete, already_scheduled_outreach
from data_access.outreach_config import OUTREACH_BEFORE_TEXT_USER_DELAY
from datetime import datetime, timezone
import pytz
import boto3
import json
import logging

logger = logging.getLogger('SymptomReporter')
logger.setLevel(LOG_LEVEL)

sfn_client = boto3.client('stepfunctions')


def get_trial_config(trial_id, ddb_client=None):
    key = {
        'Trial_ID': trial_id
    }
    trial_config_item = get_item_ddb(TRIAL_CONFIG_TABLE, ddb_client=ddb_client, Key=key)
    if not trial_config_item:
        logger.info(f'Did not find trail with id {trial_id}')
        return None
    return trial_config_item


def schedule_outreach_for_participant(participant_id, start_date_str, end_date_str, surveys):
    user = user_profile.lookup_user_by_id(participant_id)
    user_local_tz = pytz.timezone(user.timezone)
    today = datetime.now(tz=timezone.utc).astimezone(user_local_tz)

    if not check_trial_start_and_enddate(participant_id, user_local_tz, start_date_str, end_date_str, today):
        return
    if already_scheduled_outreach(participant_id, today):
        return

    surveys_to_take = []
    for survey_name in surveys:
        # TODO: filter out surveys that are not daily and not due today
        survey = surveys[survey_name]
        surveys_to_take.append(survey)
    surveys_to_take.sort(key=lambda x: x['Priority'])
    initialize_survey_to_complete(participant_id, today, surveys_to_take)

    initial_outreach_wait_time = OUTREACH_BEFORE_TEXT_USER_DELAY  # seconds
    schedule_outreach_input = {
        'UserId': participant_id,
        'TimeZone': user.timezone,
        'Date': format_date_to_str(today),
        'wait': {
            'mode': 'SECONDS',
            'seconds': initial_outreach_wait_time
        }
    }

    execution_arn = None
    if OUTREACH_WORKFLOW:
        response = sfn_client.start_execution(
            stateMachineArn=OUTREACH_WORKFLOW,
            input=json.dumps(schedule_outreach_input)
        )
        execution_arn = response['executionArn']
        logger.info(f'scheduled outreach: {execution_arn}')

    with DDBUpdateBuilder(
            key={'Patient_ID': participant_id, 'Report_Date': format_date_to_str(today)},
            table_name=SURVEY_COMPLETION_TABLE) as ddb_update_builder:
        if execution_arn:
            ddb_update_builder.update_attr('Execution_ID', execution_arn)


def check_trial_start_and_enddate(participant_id, user_local_tz, start_date_str, end_date_str, today):
    start_date = user_local_tz.localize(parse_date_from_str(start_date_str))
    end_date = user_local_tz.localize(parse_date_from_str(end_date_str))
    if today < start_date:
        logger.info(f"Trial hasn't started for {participant_id}")
        return False
    elif today > end_date:
        logger.info(f"Trial already complete for {participant_id}")
        return False
    else:
        logger.info(f'Trial in progress for {participant_id}')
        return True


def schedule_outreach_for_trial(trial_id, ddb_client=None):
    trial_config = get_trial_config(trial_id, ddb_client)
    if trial_config is None:
        return

    participants = trial_config['Participants']
    surveys = trial_config['Surveys']
    for p in participants:
        schedule_outreach_for_participant(p['ID'], p['StartDate'], p['EndDate'], surveys)


def scan_trials():
    trials = scan_item_ddb(TRIAL_CONFIG_TABLE)
    for trial_config in trials:
        participants = trial_config['Participants']
        surveys = trial_config['Surveys']
        for p in participants:
            schedule_outreach_for_participant(p['ID'], p['StartDate'], p['EndDate'], surveys)


def lambda_handler(event, context):
    scan_trials()
