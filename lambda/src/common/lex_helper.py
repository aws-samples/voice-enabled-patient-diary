import logging
import json
from enum import Enum
from collections import namedtuple
from common.lex_config import LOG_LEVEL
from data_access.user_profile import lookup_user_by_phone, TEST_USER

#
# See additional configuration parameters at bottom
#

logger = logging.getLogger('LexHelper')
logger.setLevel(LOG_LEVEL)

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """
ValidationResult = namedtuple('ValidationResult', ['isValid', 'violatedSlot', 'message'])


class FulfillmentState(Enum):
    FULFILLED = 'Fulfilled'
    FAILED = 'Failed'
    READY = 'ReadyForFulfillment'


class ConfirmationStatus(Enum):
    CONFIRMED = 'Confirmed'
    DENIED = 'Denied'
    NONE = 'None'


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message_content=None,
                message_type='PlainText'):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {
                'contentType': message_type,
                'content': message_content
            }
        }
    }


def elicit_intent(session_attributes, message_content=None, message_type='PlainText'):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitIntent',
            'message': {
                'contentType': message_type,
                'content': message_content
            }
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message_content=None, message_type='PlainText'):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': {
                'contentType': message_type,
                'content': message_content
            }
        }
    }


def close(session_attributes, fulfillment_state, message_content=None, message_type='PlainText'):
    logger.info("response-message: %s", message_content)
    logger.debug("session: {}".format(session_attributes))
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state.value,
            'message': {
                'contentType': message_type,
                'content': message_content
            }
        }
    }

    return response


def delegate(session_attributes, slots):
    logger.debug("session: {}".format(session_attributes))
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def build_validation_result(is_valid, violated_slot=None, message_content=None, message_type='PlainText'):
    return ValidationResult(isValid=is_valid,
                            violatedSlot=violated_slot,
                            message={
                                'contentType': message_type,
                                'content': message_content}
                            )


""" --- Helper Functions --- """


def is_validation_request(intent_request):
    return intent_request['invocationSource'] == 'DialogCodeHook'


def extract_phone_number(session_attributes):
    source = get_attribute(session_attributes, 'Source', None)
    if not source:
        return None
    if source == 'AmazonConnect':
        logger.info('Request is from Connect')
        return get_attribute(session_attributes, 'IncomingNumber', None)


def lookup_user(session_attributes):
    phone_number = extract_phone_number(session_attributes)
    if phone_number:
        return lookup_user_by_phone(phone_number)
    else:
        logger.info('no incoming phone number, use mock user')
        return TEST_USER


def get_attribute(event, attr, default_val={}):
    """
    Retrieve attribute from request. if it's null or doesn't exist, return default value.
    """
    return default_val if attr not in event or event[attr] is None else event[attr]


def get_map_from_session(session_attributes, attr_key):
    return json.loads(get_attribute(session_attributes, attr_key, '{}'))


def get_list_from_session(session_attributes, attr_key):
    return json.loads(get_attribute(session_attributes, attr_key, '[]'))


def append_session_attr(session_attributes, attr_key, attr_value):
    values = get_list_from_session(session_attributes, attr_key)
    values.append(attr_value)
    session_attributes[attr_key] = json.dumps(values)


def wrap_ssml_tag(msg):
    return '<speak>' + msg + '</speak>'
