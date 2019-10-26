from flask import request

from core.src.websocket.requests import WebsocketRequestsProcessorInterface
from core.src.websocket.messages import WebsocketMessagesFactory


ws_messages_factory = WebsocketMessagesFactory()
ws_commands_processor = WebsocketRequestsProcessorInterface()

ws_commands_processor.add_command(
    'di',
    lambda *x: request.user_token['user']['user_id'] + ' dice "' + ' '.join(x) + '"'
)
ws_commands_processor.add_command(
    'guarda',
    lambda *a, **kw: "Guarda pure, ma non c'è niente, ti ho detto che non c'è niente.\n",
    aliases=['g', 'gu', 'gua']
)
