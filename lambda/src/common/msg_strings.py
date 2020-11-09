messages = {
    'NOT_SUPPORTED': "Sorry, I'm unable to help with that.",
    'ZIP_CODE_MISMATCH': 'The zip code <say-as interpret-as="digits">{}</say-as>'
                         '<break time="100ms"/> did not match our records. ',
    'ZIP_CODE_GOODBYE': 'Please check your profile on the Angeles app to make sure your info is up-to-date. Goodbye.',
    'ZIP_CODE_RETRY': 'Can you tell me your zip code one more time? ',
    'FINISH_MED_DIARY': "Got it. I have entered a medication dairy for you.",
    'ADDITIONAL_SYMPTOM_QUERY': "Do you have any other symptoms to report?",
    'ASK_SYMPTOM_DETAIL': 'Can you tell me what symptoms you have, one at a time?',
    'ASK_SYMPTOM_FOLLOW_UP': 'What other symptom do you have?',
    'ASK_SYMPTOM': "Sorry I didn't get that. Can you tell me about your symptom, one at a time? ",
    'ASK_SYMPTOM_BODY_PART': "Where do you have the {}?",
    'AFTER_SYMPTOM_DENY': "OK let's try it again. What symptom do you have?",
    "NO_SYMPTOM_CONFIRM": "you mean you have no symptoms, right?",
    'FINISH_SYMPTOM_REPORT': "Got it. I have logged this in the system. ",
    "CONFIRM_INTENSITY": "Your {} is a {} out of 10. Did I get that right?",
    "AFTER_USER_CONFIRM_TIME": "Great! Let's get started.",
    "AFTER_USER_DENY_TIME": "No Problem. We will call you back in 10 minutes.",
    "RATE_PAIN_PROMPT": "On a scale of 0 to 10, 0 being no pain, 10 being worst possible pain, "
                        "what would you rate the pain you've been experiencing?",
    "PAIN_LEVEL_VALIDATION_FAILED": "You need to choose a whole number between 0 and 10. "
                                    "Can you tell me the level of pain one more time?",
    "DID_NOT_TAKE_MED": "OK. Please remember to take your medicine and let me know when you do. ",
    "CLARIFICATION": "Sorry, I didn't get that. Can you say it one more time?",
    "REPEAT_STARTED": "Sure, no problem. "
}


def get(msg_name):
    return messages.get(msg_name, None)
