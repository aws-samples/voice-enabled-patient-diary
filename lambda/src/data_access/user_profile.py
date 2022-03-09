
from datetime import datetime, timezone

import pytz

from data_access.data_config import PROFILE_TABLE
from data_access.ddb_util import query_item_ddb, get_item_ddb
import logging
from data_access.data_config import LOG_LEVEL
from boto3.dynamodb.conditions import Key

logger = logging.getLogger('UserProfile')
logger.setLevel(LOG_LEVEL)


class UserProfile:
    def __init__(self, uid, phone=None, first_name=None, auth_code=None, timezone='UTC', caretaker_num=None,
                 provider_num=None, provider_email=None):
        self.uid = uid
        self.phone = phone
        self.first_name = first_name
        self.auth_code = auth_code
        self.timezone = timezone
        self.caretaker_num = caretaker_num
        self.provider_num = provider_num
        self.provider_email = provider_email

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.uid == other.uid and \
                   self.phone == other.phone and \
                   self.first_name == other.first_name and \
                   self.auth_code == other.auth_code and \
                   self.timezone == other.timezone and \
                   self.caretaker_num == other.caretaker_num and \
                   self.provider_num == other.provider_num
        return False

    def __hash__(self):
        return hash(self.uid)

    def __str__(self):
        return f'ID={self.uid};' \
               f'phone={self.phone};' \
               f'timezone={self.timezone};' \
               f'auth_code={self.auth_code};'


TEST_USER = UserProfile(uid='TEST_ID',
                        phone='+12345678901',
                        first_name='test user',
                        auth_code='123456',
                        timezone='US/Eastern',
                        caretaker_num=None,
                        provider_num='+12345678901',
                        provider_email=None
                        )


def user_from_entry(user_item):
    return UserProfile(uid=user_item['Patient_ID'],
                       phone=user_item.get('Phone_Num', None),
                       first_name=user_item.get('First_Name', None),
                       auth_code=user_item.get('Auth_Code', None),
                       timezone=user_item.get('Time_Zone', 'UTC'),
                       caretaker_num=user_item.get('Caretaker_Phone_Num', None),
                       provider_num=user_item.get('Provider_Phone_Numer', None),
                       provider_email=user_item.get('Provider_Email', None)
                       )


def lookup_user_by_id(uid, ddb_client=None):
    user_key = {
        'Patient_ID': uid
    }
    user_item = get_item_ddb(table_name=PROFILE_TABLE, ddb_client=ddb_client, Key=user_key)
    if not user_item:
        logger.info(f'did not find user with uid {uid}')
        return None
    return user_from_entry(user_item)


def lookup_user_by_phone(phone_num, ddb_client=None):
    query_params = {
        'IndexName': 'Patient_by_Phone',
        'KeyConditionExpression': Key('Phone_Num').eq(phone_num)
    }
    user_items = query_item_ddb(PROFILE_TABLE, ddb_client=ddb_client, **query_params)
    if not user_items:
        logger.info(f'did not find user with phone: {phone_num}')
        return None
    user_item = user_items[0]
    logger.info('Found user for phone number.')
    return user_from_entry(user_item)


def get_current_time_for_user(user):
    return datetime.now(tz=timezone.utc).astimezone(pytz.timezone(user.timezone))
