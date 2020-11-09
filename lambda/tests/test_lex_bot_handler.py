

import os
import sys

from lex_bot_handler import LexBotHandler
from utils import load_json_file

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'events')


def test_handler():
    lex_handler = LexBotHandler()
    test_context = None
    test_event = load_json_file(os.path.join(TEST_DATA_DIR, 'test_med_time.json'))

    # test registering new intent handlers
    expected_response = '1234'
    lex_handler.register_intent('MedicationTime', lambda event: expected_response)
    assert lex_handler.handle_lambda(test_event, test_context) == expected_response

    # test when intent is not supported, gracefully respond to user
    not_supported_test_event = load_json_file(os.path.join(TEST_DATA_DIR, 'not_supported_intent.json'))
    response = lex_handler.handle_lambda(not_supported_test_event, test_context)
    assert 'Sorry' in response['dialogAction']['message']['content']
