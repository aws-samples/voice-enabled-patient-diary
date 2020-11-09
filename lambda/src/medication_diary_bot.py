import logging

from data_access.user_profile import get_current_time_for_user

from lex_bot_handler import LexBotHandler
from common.lex_config import LOG_LEVEL, SLOT_MED_TIME, SLOT_MED_TIME_OF_DAY, INTENT_MEDICATION_TIME, \
    INTENT_YES_MEDICATION, INTENT_NO_MEDICATION, BOT_MEDICATION_NAME
from common import lex_helper as helper
from common import msg_strings
from data_access import medication_diary as med_diary
from data_access.survey_completion import update_survey_completion, get_next_survey_bot
from data_access.data_config import format_only_time_to_str

from collections import namedtuple
import pytz
from datetime import datetime

from data_access.send_sms import send_sms

logging.basicConfig()
logger = logging.getLogger("MedicationDiaryBot")
logger.setLevel(LOG_LEVEL)

CARETAKER_MED_MISSING_MESSAGE = "Trial Assistant: Patient {} has not taken their medication as of {} today. "

PERIOD_TO_AMPM = {
    'MO': 'AM',
    'AF': 'PM',
    'EV': 'PM',
    'NI': 'PM'
}

TimeDetail = namedtuple('TimeDetail', ['time_str', 'time_of_day', 'finished'])


def parse_time_input(time_val, time_of_day_val, time_val_alts=[]):
    if time_val is None:
        if time_val_alts:  # e.g. ["05:00", "17:00" ] ambiguous AM or PM
            time_val_alts.sort()  # pick the smaller one
            if time_of_day_val is None:
                time_val = time_val_alts[0]
                return TimeDetail(time_str=time_val, time_of_day=None, finished=False)
            elif time_of_day_val == 'AM':
                time_val = time_val_alts[0]
                return TimeDetail(time_str=time_val, time_of_day=time_of_day_val, finished=True)
            else:  # PM
                time_val = time_val_alts[1]
                return TimeDetail(time_str=time_val, time_of_day=time_of_day_val, finished=True)
        else:
            # did not get time value
            return TimeDetail(time_str=None, time_of_day=time_of_day_val, finished=False)
    else:
        # case: time_val is one of "NI", "MO", "AF", "EV"
        if time_val in PERIOD_TO_AMPM:
            time_of_day_val = PERIOD_TO_AMPM[time_val]
            return TimeDetail(time_str=None, time_of_day=time_of_day_val, finished=False)
        elif time_of_day_val is not None:
            if time_of_day_val == 'PM':
                hour = int(time_val.split(':')[0])
                if hour < 12:
                    hour += 12
                    time_val = str(hour) + time_val[2:]
            return TimeDetail(time_str=time_val, time_of_day=time_of_day_val, finished=True)
        else:
            hour = int(time_val.split(':')[0])
            logger.info(f'hour: {hour}')
            time_of_day_val = 'AM' if hour < 12 else 'PM'
            return TimeDetail(time_str=time_val, time_of_day=time_of_day_val, finished=True)


def medication_time(intent_request):
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
    if helper.is_validation_request(intent_request):
        return validate_medication_time(intent_name, session_attributes, slot_details, slots)

    med_taken_time = slots[SLOT_MED_TIME]
    hh = int(med_taken_time.split(':')[0])
    mm = int(med_taken_time.split(':')[1])

    user = helper.lookup_user(session_attributes)
    local_time_reported = get_current_time_for_user(user)
    now_with_no_timezone = datetime.now()
    med_taken_datetime = now_with_no_timezone.replace(hour=hh, minute=mm, second=0)
    local_med_time = pytz.timezone(user.timezone).localize(med_taken_datetime)

    # TODO: for production, handle cases when user reported the same info multiple times.
    med_diary.log_med(user.uid, time_reported=local_time_reported, med_taken=True, time_taken=local_med_time)

    update_survey_completion(user.uid, local_time_reported, BOT_MEDICATION_NAME)
    session_attributes['NextBot'] = get_next_survey_bot(user.uid, local_time_reported)
    return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                        message_content=msg_strings.get('FINISH_MED_DIARY'))


def validate_medication_time(intent_name, session_attributes, slot_details, slots):
    time_slot_val = slots.get(SLOT_MED_TIME, None)
    time_of_day_slot_val = slots.get(SLOT_MED_TIME_OF_DAY, None)
    time_val_resolutions = slot_details.get(SLOT_MED_TIME, {}).get('resolutions', []) if slot_details.get(
        SLOT_MED_TIME, {}) else []
    time_detail = parse_time_input(time_slot_val, time_of_day_slot_val,
                                   time_val_alts=[res['value'] for res in time_val_resolutions])
    slots[SLOT_MED_TIME] = time_detail.time_str
    slots[SLOT_MED_TIME_OF_DAY] = time_detail.time_of_day
    if time_detail.finished:
        return helper.delegate(session_attributes, slots)
    else:
        if time_detail.time_str is not None:
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_MED_TIME_OF_DAY,
                                      f'<speak>Do you mean '
                                      f'<say-as interpret-as="time" >{time_detail.time_str}</say-as> '
                                      f'AM, or PM?</speak>',
                                      message_type='SSML')
        elif time_detail.time_of_day:
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_MED_TIME,
                                      f'<speak>Can you tell the exact time in the '
                                      f'{time_detail.time_of_day}?</speak>',
                                      message_type='SSML')
        else:
            return helper.elicit_slot(session_attributes, intent_name, slots, SLOT_MED_TIME,
                                      '<speak>What time did you take your medication?</speak>',
                                      message_type='SSML')


def yes_med(intent_request):
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
    current_intent = helper.get_attribute(intent_request, 'currentIntent')
    slots = helper.get_attribute(current_intent, 'slots')
    return helper.elicit_slot(session_attributes, INTENT_MEDICATION_TIME, slots, SLOT_MED_TIME,
                              '<speak>Great. When did you take your medication today?</speak>',
                              message_type='SSML')


def no_med(intent_request):
    session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')

    user = helper.lookup_user(session_attributes)
    current_time = get_current_time_for_user(user)
    if user.caretaker_num:
        logger.info(f'Will send notification to care taker: {user.caretaker_num}')
        time_str = format_only_time_to_str(current_time)
        msg = CARETAKER_MED_MISSING_MESSAGE.format(user.uid, time_str)
        send_sms(user.caretaker_num, msg)
    else:
        logger.info('No caretaker to notify.')

    med_diary.log_med(user.uid, time_reported=current_time, med_taken=False)
    update_survey_completion(user.uid, current_time, BOT_MEDICATION_NAME)
    session_attributes['NextBot'] = get_next_survey_bot(user.uid, current_time)

    return helper.close(session_attributes, helper.FulfillmentState.FULFILLED,
                        message_content=msg_strings.get('DID_NOT_TAKE_MED'))


def lambda_handler(event, context):
    bot_handler = LexBotHandler()
    bot_handler.register_intent(INTENT_MEDICATION_TIME, medication_time)
    bot_handler.register_intent(INTENT_YES_MEDICATION, yes_med)
    bot_handler.register_intent(INTENT_NO_MEDICATION, no_med)
    return bot_handler.handle_lambda(event, context)
