import logging
import pytz
from datetime import datetime, timezone
from lex_bot_handler import LexBotHandler
from common.lex_config import LOG_LEVEL, INTENT_VERIFY_IDENTITY, SLOT_ZIPCODE, AUTH_RESULT_ATTR
from common import lex_helper as helper
from common import msg_strings

from data_access.survey_completion import get_next_survey_bot

ATTEMPT_COUNT_ATTR = 'Attempts'
MAX_RETRY = 2

logging.basicConfig()
logger = logging.getLogger("VerifyIdentityBot")
logger.setLevel(LOG_LEVEL)


def verify_identity(intent_request):
    """
    Handler for the verifying identity
    :param intent_request:
    :return:
    """
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    current_intent = helper.get_attribute(intent_request, 'currentIntent')
    slots = helper.get_attribute(current_intent, 'slots')

    user = helper.lookup_user(session_attributes)

    zipcode_input = helper.get_attribute(slots, SLOT_ZIPCODE, None)
    if zipcode_input == user.zip_code:
        logger.info('zip code match!')
        user_local_tz = pytz.timezone(user.timezone)
        today = datetime.now(tz=timezone.utc).astimezone(user_local_tz)

        session_attributes['NextBot'] = get_next_survey_bot(user.uid, today)
        session_attributes[AUTH_RESULT_ATTR] = 'AuthSuccess'
        msg = verify_success_msg(user)
        return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                            message_content=msg,
                            message_type='PlainText')
    else:
        logger.info('zip code mismatch!')
        msg = msg_strings.get('ZIP_CODE_MISMATCH').format(zipcode_input)
        attempt_count = int(helper.get_attribute(session_attributes, ATTEMPT_COUNT_ATTR, "1"))
        if attempt_count >= MAX_RETRY:
            msg += msg_strings.get('ZIP_CODE_GOODBYE')
            logger.info(f'attempt count ({attempt_count}) reached max retry count. failed authentication.')
            session_attributes[AUTH_RESULT_ATTR] = 'AuthFail'
            return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                                message_content=helper.wrap_ssml_tag(msg), message_type='SSML')
        else:
            session_attributes[ATTEMPT_COUNT_ATTR] = attempt_count + 1
            msg += msg_strings.get('ZIP_CODE_RETRY')
            logger.info(f'attempt count ({attempt_count}) less than max retry count {MAX_RETRY}.')
            return helper.elicit_slot(session_attributes, INTENT_VERIFY_IDENTITY, slots, SLOT_ZIPCODE,
                                      message_content=helper.wrap_ssml_tag(msg),
                                      message_type='SSML')


def verify_success_msg(user):
    msg = 'Thank you'
    if user.first_name:
        msg += f' {user.first_name}'
    msg += ', verification successful.'
    return msg


def lambda_handler(event, context):
    bot_handler = LexBotHandler()
    bot_handler.register_intent(INTENT_VERIFY_IDENTITY, verify_identity)
    return bot_handler.handle_lambda(event, context)
