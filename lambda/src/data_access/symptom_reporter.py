import logging
from data_access.data_config import SYMPTOM_TABLE, format_date_time_to_str, LOG_LEVEL
from data_access.ddb_util import put_item_ddb
from data_access.send_email import send_email
from data_access.data_config import format_only_time_to_str

logger = logging.getLogger('SymptomReporter')
logger.setLevel(LOG_LEVEL)

SEVERE_SYMPTOM_SUBJECT = "[Alert] Severe symptom reported by patient"

SEVERE_SYMPTOM_BODY_TEXT = """Patient {} has reported at {} with a severe pain in his/her {} ( self-rated {} out 10).
            """

# The body of the email for recipients whose email clients can display HTML content.
SEVERE_SYMPTOM_BODY_HTML = """<html>
<head></head>
<body>
  <h1>Severe symptom reported by patient</h1>
  <p>Patient {} has reported at {} with a severe pain in his/her {} ( self-rated {} out 10).</p>
</body>
</html>"""


def report(patient_id, time_reported, symptoms, unknown_symptoms=[]):
    no_symptom = symptoms is None or symptoms == []
    logger.info('has_symptom')
    item = {
        'Patient_ID': patient_id,
        'Time_Reported': format_date_time_to_str(time_reported),
        'Symptoms': symptoms,
        'Has_Symptom': not no_symptom
    }
    if unknown_symptoms:
        item['Unknown_Symptoms'] = unknown_symptoms
    put_item_ddb(SYMPTOM_TABLE, item)


def severe_symptom_report(user, report_time, symptom_location, intensity):
    if not user.provider_email:
        logger.info('User has no provider email. no op')
        return

    time_str = format_only_time_to_str(report_time)
    body_text = SEVERE_SYMPTOM_BODY_TEXT.format(user.uid, time_str, symptom_location, intensity)
    body_html = SEVERE_SYMPTOM_BODY_HTML.format(user.uid, time_str, symptom_location, intensity)
    send_email(user.provider_email, subject=SEVERE_SYMPTOM_SUBJECT, body_text=body_text, body_html=body_html)
