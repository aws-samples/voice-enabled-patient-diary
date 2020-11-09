
import os
from datetime import datetime

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MED_DIARY_TABLE = os.getenv('MED_DIARY_TABLE', 'EproVoice-dev-MedicationDiary')
SYMPTOM_TABLE = os.getenv('SYMPTOM_TABLE', 'EproVoice-dev-Symptoms')

PROFILE_TABLE = os.getenv('PROFILE_TABLE', 'EproVoice-dev-PatientProfile')
SURVEY_COMPLETION_TABLE = os.getenv('SURVEY_COMPLETION_TABLE', 'EproVoice-dev-SurveyCompletion')
SURVEY_COMPLETE_COL = 'Surveys_Completed'
SURVEY_TBC_COL = 'Surveys_To_Complete'
OUTREACH_STATUS_COL = 'Outreach_Status'
TRIAL_CONFIG_TABLE = os.getenv('TRIAL_CONFIG_TABLE', 'EproVoice-dev-TrialConfig')

PINPOINT_REGION = os.getenv('AWS_REGION', 'us-east-1')
PINPOINT_ORIGIN_NUMBER = os.getenv('PINPOINT_ORIGIN_NUMBER', '')
PINPOINT_PROJECT_ID = os.getenv('PINPOINT_PROJECT_ID', '')
PINPOINT_KEYWORD = os.getenv('PINPOINT_KEYWORD', '')
PINPOINT_EMAIL_SENDER = "Health Services x AWS"
PINPOINT_SENDER_ID = 'Demo'
OUTREACH_WORKFLOW = os.getenv('OUTREACH_WORKFLOW', None)

TIME_FMT = "%Y-%m-%dT%H:%M:%SZ%z"
DATE_FMT = "%Y/%m/%d"
TIME_ONLY_FMT = '%H:%M'


def parse_date_time_from_str(date_time_str):
    return datetime.strptime(date_time_str, TIME_FMT)


def format_date_time_to_str(date_time):
    return datetime.strftime(date_time, TIME_FMT)


def parse_date_from_str(date_str):
    return datetime.strptime(date_str, DATE_FMT)


def format_date_to_str(date):
    return datetime.strftime(date, DATE_FMT)


def format_only_time_to_str(date_time):
    return datetime.strftime(date_time, TIME_ONLY_FMT)
