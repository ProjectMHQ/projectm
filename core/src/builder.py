from core.src.repositories.character_repository import CharacterRepositoryImpl
from core.src.websocket.messages import WebsocketMessagesFactory
from etc import settings
from core.src import database
from core.src.repositories.user_repository import UserRepositoryImpl
from core.src.services.authentication import AuthenticationServiceImpl
from core.src.services.encryption import AESCipherServiceImpl

encryption_service = AESCipherServiceImpl(
    key=settings.ENCRYPTION_KEY,
    iv=settings.ENCRYPTION_IV
)
character_repository = CharacterRepositoryImpl(database.db)
user_repository = UserRepositoryImpl(database.db)
auth_service = AuthenticationServiceImpl(encryption_service, user_repository)
ws_messages_factory = WebsocketMessagesFactory()

