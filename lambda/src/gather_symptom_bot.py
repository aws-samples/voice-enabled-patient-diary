import logging
from lex_bot_handler import LexBotHandler
from common.lex_config import LOG_LEVEL, INTENT_NO_SYMPTOM, INTENT_REPORT_SYMPTOM, INTENT_YES_SYMPTOM, \
    INTENT_SYMPTOM_FALLBACK, SLOT_SYMPTOM_ONE, SLOT_BODY_PART, SLOT_BODY_PART_MODIFIER, SLOT_PAIN_LEVEL, \
    BOT_SYMPTOM_NAME, INTENSITY_THRESHOLD
from common import lex_helper as helper
from common import msg_strings
from data_access import symptom_reporter
from data_access.survey_completion import update_survey_completion, get_next_survey_bot
from data_access.user_profile import get_current_time_for_user
import json

UNKNOWN_SYMPTOM_ATTR = 'unknownSymptom'
SYMPTOM_ATTR = 'Symptoms'
NOTIFY_PROVIDER_ATTR = 'NotifyProvider'

logging.basicConfig()
logger = logging.getLogger("GatherSymptomBot")
logger.setLevel(LOG_LEVEL)

localized_symptom = set(['itch', 'pain', 'swelling', 'rash', 'cramp'])
intensity_symptom = set(['headache', 'pain', 'cramp'])


descriptor_to_symptom = {
    'are experiencing {}': {'pain'},
    'have a {}': {'itch', 'chills', 'fever', 'swelling', 'diarrhea', 'cough', 'cramp', 'rash', 'headache',
                  'sore throat', 'stroke', 'heart attack'},
    'are feeling {}': {'dizzy', 'tired', 'nauseous', 'light-headed'},
    'are having {}': {'sneezes'}
}

BODY_PART_PREPOSITION = {
    'skin': 'on your',
    'all over': ''
}

symptom_to_descriptor = {s: d for d, symptoms in descriptor_to_symptom.items() for s in symptoms}


def find_descriptor_for_symptom(symptom):
    if symptom in symptom_to_descriptor:
        return symptom_to_descriptor[symptom].format(symptom)
    else:
        return 'are having {}'.format(symptom)


def validate_symptom_input(intent_name, session_attributes, slot_details, slots):
    symptom_name = slots.get(SLOT_SYMPTOM_ONE, None)
    # TODO: add support for multiple symptoms
    if not symptom_name:  # did not get symptom
        symptom_slot_detail = helper.get_attribute(slot_details, SLOT_SYMPTOM_ONE, {})
        unknown_symptom = symptom_slot_detail.get('originalValue', None)
        if unknown_symptom:
            logger.info(f'encountered unknown symptom: {unknown_symptom}')
            helper.append_session_attr(session_attributes, UNKNOWN_SYMPTOM_ATTR, unknown_symptom)
            symptom_name = unknown_symptom
            slots[SLOT_SYMPTOM_ONE] = symptom_name
        else:
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_SYMPTOM_ONE,
                                      msg_strings.get('ASK_SYMPTOM'))

    pain_level = slots.get(SLOT_PAIN_LEVEL, None)
    if symptom_name in intensity_symptom and pain_level:
        try:
            int(pain_level)
        except ValueError:
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_PAIN_LEVEL,
                                      msg_strings.get('PAIN_LEVEL_VALIDATION_FAILED').format(symptom_name))
        # verify within range
        if int(pain_level) < 0 or int(pain_level) > 10:
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_PAIN_LEVEL,
                                      msg_strings.get('PAIN_LEVEL_VALIDATION_FAILED').format(symptom_name))
        else:
            # confirm intensity level if it's above threshold
            if int(pain_level) >= INTENSITY_THRESHOLD:
                msg = msg_strings.get('CONFIRM_INTENSITY').format(symptom_name, pain_level)
                return helper.confirm_intent(session_attributes, intent_name, slots, msg)
            return helper.delegate(session_attributes, slots)
    else:
        if symptom_name in localized_symptom:
            # need to distinguish which body part has the symptom
            body_part = slots.get(SLOT_BODY_PART, None)
            if not body_part:
                return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_BODY_PART,
                                          msg_strings.get('ASK_SYMPTOM_BODY_PART').format(symptom_name))
            else:
                modifier = slots.get(SLOT_BODY_PART_MODIFIER, None)
                return confirm_symptom(session_attributes, intent_name, slots, symptom_name, body_part, modifier)
        else:
            return confirm_symptom(session_attributes, intent_name, slots, symptom_name)


def confirm_symptom(session_attributes, intent_name, slots, symptom_name, body_part=None, modifier=None):
    message = 'You said you '

    message += find_descriptor_for_symptom(symptom_name)
    if body_part:
        if body_part in BODY_PART_PREPOSITION:
            message += f' {BODY_PART_PREPOSITION[body_part]} '
        else:
            message += ' in your '
        if modifier:
            message += '{} {}'.format(modifier, body_part)
        else:
            message += '{}'.format(body_part)
    message += '. Right?'
    return helper.confirm_intent(session_attributes, intent_name, slots, message_content=message,
                                 message_type='PlainText')


def yes_symptom(intent_request):
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    symptoms = helper.get_list_from_session(session_attributes, SYMPTOM_ATTR)
    msg = msg_strings.get('ASK_SYMPTOM_FOLLOW_UP') if symptoms else msg_strings.get('ASK_SYMPTOM_DETAIL')
    return helper.elicit_intent(session_attributes, message_content=msg)


def no_symptom(intent_request):
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    symptoms = helper.get_list_from_session(session_attributes, SYMPTOM_ATTR)
    current_intent = helper.get_attribute(intent_request, 'currentIntent')
    slots = helper.get_attribute(current_intent, 'slots')
    confirmation_status = helper.get_attribute(current_intent, 'confirmationStatus')
    intent_name = helper.get_attribute(current_intent, 'name')
    if confirmation_status == helper.ConfirmationStatus.NONE.value:
        if len(symptoms) == 0:
            # add confirmation for no symptoms
            return helper.confirm_intent(session_attributes, intent_name, slots,
                                         message_content=msg_strings.get('NO_SYMPTOM_CONFIRM'))
    elif confirmation_status == helper.ConfirmationStatus.DENIED.value:
        return helper.elicit_slot(session_attributes,
                                  INTENT_REPORT_SYMPTOM, slots, SLOT_SYMPTOM_ONE,
                                  message_content=msg_strings.get('ASK_SYMPTOM_DETAIL'))

    # ready to log symptoms
    user = helper.lookup_user(session_attributes)
    local_time_reported = get_current_time_for_user(user)
    unknown_symptoms = helper.get_list_from_session(session_attributes, UNKNOWN_SYMPTOM_ATTR)
    symptom_reporter.report(user.uid, local_time_reported, symptoms, unknown_symptoms)

    update_survey_completion(user.uid, local_time_reported, BOT_SYMPTOM_NAME)
    session_attributes['NextBot'] = get_next_survey_bot(user.uid, local_time_reported)

    return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                        message_content=msg_strings.get('FINISH_SYMPTOM_REPORT'))


def report_symptom(intent_request):
    """
    Handler for the medication time intent
    :param intent_request: lex intent request
    :return:
    """
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    current_intent = helper.get_attribute(intent_request, 'currentIntent')
    slots = helper.get_attribute(current_intent, 'slots')
    slot_details = helper.get_attribute(current_intent, 'slotDetails')
    intent_name = helper.get_attribute(current_intent, 'name')

    confirmation_status = helper.get_attribute(current_intent, 'confirmationStatus')
    symptom = slots.get(SLOT_SYMPTOM_ONE, None)
    body_part = slots.get(SLOT_BODY_PART, None)
    modifier = slots.get(SLOT_BODY_PART_MODIFIER, None)
    intensity = slots.get(SLOT_PAIN_LEVEL, None)
    unknown_symptoms = helper.get_list_from_session(session_attributes, UNKNOWN_SYMPTOM_ATTR)

    if confirmation_status == helper.ConfirmationStatus.NONE.value:
        if helper.is_validation_request(intent_request):
            return validate_symptom_input(intent_name, session_attributes, slot_details, slots)
    elif confirmation_status == helper.ConfirmationStatus.DENIED.value:
        # deny could be for intensity level or for symptoms

        if symptom == unknown_symptoms[-1]:
            unknown_symptoms.pop()
        session_attributes[UNKNOWN_SYMPTOM_ATTR] = json.dumps(unknown_symptoms)
        slots = {}
        return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_SYMPTOM_ONE,
                                  msg_strings.get('AFTER_SYMPTOM_DENY'))

    msg = ''
    # after confirming the first symptom, say sorry to hear to show sympathy. However, only say this once per session
    if not helper.get_attribute(session_attributes, 'alreadySaidSorry'):
        if symptom in unknown_symptoms:
            msg += 'Sorry to hear that. '
        else:
            msg += 'Sorry to hear that you ' + find_descriptor_for_symptom(symptom) + ". "
        session_attributes['alreadySaidSorry'] = 'true'

    if symptom in intensity_symptom:
        # gather pain level
        if not intensity:
            msg += msg_strings.get('RATE_PAIN_PROMPT')
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_PAIN_LEVEL, msg)
        elif int(intensity) >= INTENSITY_THRESHOLD:
            user = helper.lookup_user(session_attributes)
            local_time_reported = get_current_time_for_user(user)
            symptom_reporter.severe_symptom_report(user, local_time_reported, body_part, intensity)
            msg += f'We will notify your medical provider of your {symptom}. '
        else:
            msg += f"Got it. That's a {intensity} out of 10. "

    symptom_obj = {'symptom': symptom}
    if body_part:
        symptom_obj['bodyPart'] = body_part
    if modifier:
        symptom_obj['modifier'] = modifier
    if intensity:
        symptom_obj['intensity'] = int(intensity)
    helper.append_session_attr(session_attributes, SYMPTOM_ATTR, symptom_obj)

    msg += msg_strings.get('ADDITIONAL_SYMPTOM_QUERY')
    return helper.elicit_intent(session_attributes, message_content=msg)


def fall_back(intent_request):
    # if no prev intent or prev intent is asking for symptoms
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    current_intent = helper.get_attribute(intent_request, 'currentIntent')
    slots = helper.get_attribute(current_intent, 'slots')

    confirmation_status = helper.get_attribute(current_intent, 'confirmationStatus')
    # TODO: if prev intent is asking for body part
    # TODO: too many failed attempts should terminate.

    if confirmation_status == helper.ConfirmationStatus.NONE.value:
        user_utterance = intent_request['inputTranscript']
        if user_utterance == '':
            return helper.elicit_slot(session_attributes, INTENT_REPORT_SYMPTOM, slots, SLOT_SYMPTOM_ONE,
                                      msg_strings.get('CLARIFICATION'))
        message = f"your said '{user_utterance}', is that right?"
        slots[SLOT_SYMPTOM_ONE] = user_utterance
        helper.append_session_attr(session_attributes, UNKNOWN_SYMPTOM_ATTR, user_utterance)
        return helper.confirm_intent(session_attributes, INTENT_REPORT_SYMPTOM, slots, message_content=message,
                                     message_type='PlainText')
    elif confirmation_status == helper.ConfirmationStatus.DENIED.value:
        return helper.elicit_slot(session_attributes, INTENT_REPORT_SYMPTOM, slots, SLOT_SYMPTOM_ONE,
                                  msg_strings.get('AFTER_SYMPTOM_DENY'))
    else:
        return helper.elicit_slot(session_attributes, INTENT_REPORT_SYMPTOM, slots, SLOT_SYMPTOM_ONE,
                                  msg_strings.get('CLARIFICATION'))


def lambda_handler(event, context):
    bot_handler = LexBotHandler()
    bot_handler.register_intent(INTENT_REPORT_SYMPTOM, report_symptom)
    bot_handler.register_intent(INTENT_NO_SYMPTOM, no_symptom)
    bot_handler.register_intent(INTENT_YES_SYMPTOM, yes_symptom)
    bot_handler.register_intent(INTENT_SYMPTOM_FALLBACK, fall_back)
    return bot_handler.handle_lambda(event, context)
