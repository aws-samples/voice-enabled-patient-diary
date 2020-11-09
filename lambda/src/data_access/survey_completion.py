
from data_access.data_config import format_date_to_str, SURVEY_COMPLETION_TABLE, SURVEY_TBC_COL, SURVEY_COMPLETE_COL, LOG_LEVEL
from data_access.ddb_util import put_item_ddb, get_item_ddb, DDBUpdateBuilder
import logging

logger = logging.getLogger('SurveyCompletion')
logger.setLevel(LOG_LEVEL)


def initialize_survey_to_complete(user_id, report_date, surveys_to_take):
    report_date_str = format_date_to_str(report_date)
    item = {
        'Patient_ID': user_id,
        'Report_Date': report_date_str,
        SURVEY_COMPLETE_COL: [],
        SURVEY_TBC_COL: surveys_to_take,
        'Outreach_Status': 'None'
    }
    put_item_ddb(SURVEY_COMPLETION_TABLE, item)


def already_scheduled_outreach(user_id, report_date):
    entry = get_survey_completion_entry(user_id, format_date_to_str(report_date))
    if not entry:
        logger.info(f'Did not find entry for {user_id} and {report_date}. ')
        return False
    if 'Execution_ID' in entry:
        logger.info(f'{user_id} and {report_date} already have outreach workflow started: {entry["Execution_ID"]}')
        return True
    return False


def get_survey_completion_entry(user_id, report_date_str):
    key = {'Patient_ID': user_id, 'Report_Date': report_date_str}
    entry = get_item_ddb(SURVEY_COMPLETION_TABLE, Key=key)
    return entry


def get_next_survey_bot(user_id, report_date):
    report_date_str = format_date_to_str(report_date)
    survey_entry = get_survey_completion_entry(user_id, report_date_str)
    if not survey_entry:
        return None
    if SURVEY_TBC_COL not in survey_entry or len(survey_entry[SURVEY_TBC_COL]) == 0:
        logger.info(f'No more surveys for {user_id} and {report_date_str}')
        return None
    surveys_to_complete = survey_entry[SURVEY_TBC_COL]
    top_survey = surveys_to_complete[0]
    next_bot = top_survey['BotName']
    logger.info(f'Next bot for {user_id} and {report_date_str} is {next_bot}.')
    return next_bot


def update_survey_completion(user_id, report_date, bot_name, require_follow_up=False):
    report_date_str = format_date_to_str(report_date)
    survey_entry = get_survey_completion_entry(user_id, report_date_str)
    if not survey_entry:
        logger.info('No survey completion entry to update. do nothing.')
        return
    if SURVEY_TBC_COL not in survey_entry or len(survey_entry[SURVEY_TBC_COL]) == 0:
        logger.info('All survey already completed. do nothing')
        return

    surveys_to_complete = survey_entry[SURVEY_TBC_COL]
    survey_completed = survey_entry[SURVEY_COMPLETE_COL]
    new_surveys_to_complete = []
    for s in surveys_to_complete:
        if s['BotName'] == bot_name:
            survey_completed.append(s)
        else:
            new_surveys_to_complete.append(s)
    with DDBUpdateBuilder(
            key={'Patient_ID': user_id, 'Report_Date': report_date_str},
            table_name=SURVEY_COMPLETION_TABLE) as ddb_update_builder:
        ddb_update_builder.update_attr(SURVEY_COMPLETE_COL, survey_completed)
        ddb_update_builder.update_attr(SURVEY_TBC_COL, new_surveys_to_complete)
