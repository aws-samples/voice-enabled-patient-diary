import logging
import json
from datetime import datetime
from common.lex_config import LOG_LEVEL, INTENT_NOT_SUPPORTED
from common import lex_helper as helper
from common import msg_strings

logging.basicConfig()
logger = logging.getLogger("LexBotHandler")
logger.setLevel(LOG_LEVEL)


class LexBotHandler:
    def __init__(self):
        self.intent_handlers = {INTENT_NOT_SUPPORTED: self.not_supported_intent_handler}

    @staticmethod
    def not_supported_intent_handler(intent_request):
        session_attributes = helper.get_attribute(intent_request, 'sessionAttributes')
        return helper.close(session_attributes, helper.FulfillmentState.FAILED,
                            message_content=msg_strings.get('NOT_SUPPORTED'))

    @staticmethod
    def decorate_transcript(intent_request):
        logger.debug("spoken text: {}".format(intent_request['inputTranscript']))
        # consider using a intercepter for this
        intent_request['sessionAttributes'] = helper.get_attribute(intent_request, 'sessionAttributes')
        conversation_history_serialized = intent_request['sessionAttributes'].get('transcripts', '[]')
        conversation_history = json.loads(conversation_history_serialized)
        conversation_history.append({
            'time': datetime.now().isoformat(),
            'user': intent_request['inputTranscript']
        })
        intent_request['sessionAttributes']['transcripts'] = json.dumps(conversation_history)

    def register_intent(self, intent_name, intent_handler):
        self.intent_handlers[intent_name] = intent_handler

    def dispatch(self, intent_request):
        # no need for this because lex conversation logs
        # self.decorate_transcript(intent_request)

        intent_name = intent_request['currentIntent']['name']
        logger.info('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_name))

        if intent_name in self.intent_handlers:
            intent_handler = self.intent_handlers[intent_name]
            return intent_handler(intent_request)
        else:
            return self.intent_handlers[INTENT_NOT_SUPPORTED](intent_request)

    def handle_lambda(self, event, context):
        logger.info('Received event: %s', json.dumps(event, indent=2))
        logger.debug('context: {}'.format(context))

        logger.debug('event.bot.name={}'.format(event['bot']['name']))

        """
        Route the incoming request based on intent.
        """
        response = self.dispatch(event)
        logger.info('response: {}'.format(json.dumps(response)))
        return response
