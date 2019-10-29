from flask import request
from core.src.websocket.requests import WebsocketWorldCommandsInterface
from core.src.websocket.messages import WebsocketMessagesFactory
from core.src.websocket.types import WebsocketContext
from core.src.websocket.utilities import WSCommandsInterfaceFactory

ws_messages_factory = WebsocketMessagesFactory()

_ws_world_commands_interface = WebsocketWorldCommandsInterface(WebsocketContext.WORLD)

_ws_world_commands_interface.add_command(
    'echo',
    lambda *x: request.user_token['user']['user_id'] + '> ' + ' '.join(x)
)

ws_commands_extractor_factory = WSCommandsInterfaceFactory()
ws_commands_extractor_factory.add_interface(_ws_world_commands_interface)
