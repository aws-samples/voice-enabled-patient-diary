
import os
from enum import Enum

OUTREACH_BEFORE_TEXT_USER_DELAY = int(os.getenv('OUTREACH_BEFORE_TEXT_USER_DELAY', '60'))
OUTREACH_AFTER_TEXT_USER_DELAY = int(os.getenv('OUTREACH_AFTER_TEXT_USER_DELAY', '60'))
OUTREACH_AFTER_CALL_USER_DELAY = int(os.getenv('OUTREACH_AFTER_CALL_USER_DELAY', '90'))


class OutreachStatus(Enum):
    NoOutreach = 'None'
    TextedUser = 'TextedUser'
    CalledUser = 'CalledUser'
    NotifiedProvider = 'NotifiedProvider'
