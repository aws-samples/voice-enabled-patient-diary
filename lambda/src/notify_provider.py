from data_access.data_config import LOG_LEVEL, OUTREACH_STATUS_COL, SURVEY_COMPLETION_TABLE
from data_access.user_profile import lookup_user_by_id
from data_access.ddb_util import DDBUpdateBuilder
from data_access.send_email import send_email
import logging
from data_access.outreach_config import OutreachStatus

logger = logging.getLogger('TextOutreach')
logger.setLevel(LOG_LEVEL)

SUBJECT = '[Warn] Patient did not enter diary'
# The content of the SMS message.
SEVERE_SYMPTOM_BODY_TEXT = """Patient {} has not reported his/her outcome after multiple reminders."""

# The body of the email for recipients whose email clients can display HTML content.
SEVERE_SYMPTOM_BODY_HTML = """<html>
<head></head>
<body>
  <h1>Missing patient diary</h1>
  <p>Patient {} has not reported his/her outcome after multiple reminders.</p>
</body>
</html>"""


def lambda_handler(event, context):
    # send text message
    # update outreach status
    user_id = event['UserId']
    date = event['Date']
    user = lookup_user_by_id(user_id)
    if user.provider_email:
        logger.info(f'Found provider email: {user.provider_email}')
        body_text = SEVERE_SYMPTOM_BODY_TEXT.format(user_id)
        body_html = SEVERE_SYMPTOM_BODY_HTML.format(user_id)
        send_email(user.provider_email, SUBJECT, body_text, body_html)
    else:
        logger.info('no provider email. do nothing')

    outreach_status = OutreachStatus.NotifiedProvider.value
    with DDBUpdateBuilder(
            key={'Patient_ID': user_id, 'Report_Date': date},
            table_name=SURVEY_COMPLETION_TABLE) as ddb_update_builder:
        ddb_update_builder.update_attr(OUTREACH_STATUS_COL, outreach_status)

    event[OUTREACH_STATUS_COL] = outreach_status
    return event
