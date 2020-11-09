import logging
from lex_bot_handler import LexBotHandler
from common.lex_config import LOG_LEVEL, INTENT_YES_REPORT_NOW, INTENT_NO_LATER

from common import lex_helper as helper
from common import msg_strings

logging.basicConfig()
logger = logging.getLogger("ConfirmTimeToReport")
logger.setLevel(LOG_LEVEL)


def report_now(intent_request):
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                        message_content=msg_strings.get('AFTER_USER_CONFIRM_TIME'))


def no_later(intent_request):
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                        message_content=msg_strings.get('AFTER_USER_DENY_TIME'))


def lambda_handler(event, context):
    bot_handler = LexBotHandler()
    bot_handler.register_intent(INTENT_YES_REPORT_NOW, report_now)
    bot_handler.register_intent(INTENT_NO_LATER, no_later)
    return bot_handler.handle_lambda(event, context)
