from flask import request

from core.src.websocket.requests import WebsocketWorldCommandsInterface
from core.src.websocket.messages import WebsocketMessagesFactory
from core.src.websocket.types import WebsocketContext
from core.src.websocket.utilities import WSCommandsInterfaceFactory

ws_messages_factory = WebsocketMessagesFactory()

_ws_world_commands_interface = WebsocketWorldCommandsInterface(WebsocketContext.WORLD)

_ws_world_commands_interface.add_command(
    'di',
    lambda *x: request.user_token['user']['user_id'] + ' dice "' + ' '.join(x) + '"'
)
_ws_world_commands_interface.add_command(
    'guarda',
    lambda *a, **kw: "Guarda pure, ma non c'è niente, ti ho detto che non c'è niente.\n",
    aliases=['g', 'gu', 'gua']
)
_ws_world_commands_interface.add_command(
    'grida',
    lambda *x: request.user_token['user']['user_id'] + ' grida "' + ' '.join(x) + '"'
)

ws_commands_extractor_factory = WSCommandsInterfaceFactory()
ws_commands_extractor_factory.add_interface(_ws_world_commands_interface)
