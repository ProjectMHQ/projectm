import json
import time

from sendgrid import SendGridAPIClient

from etc import settings
from core.src.builder import user_repository, encryption_service
from core.src.business.user.types import UserStatus
from core.src.database import atomic, init_db, db
from core.src.logging_factory import LOGGER
from core.src.services.email_service import EmailServiceImpl

sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
email_service = EmailServiceImpl(sendgrid_client)


def process_locked_users():
    """
    send the confirmation email to locked users.

    after a signup a new user turn into LOCKED status if settings.EMAIL_MUST_BE_CONFIRMED == True
    """
    users = user_repository.get_multiple_users_by_field('status', UserStatus.LOCKED.value)
    for user in users:
        token = encryption_service.encrypt(
            json.dumps({
                'ttl': settings.EMAIL_CONFIRMATION_LINK_TTL,
                'created_at': int(time.time()),
                'email': user.email
            })
        )
        email_service.send_email_address_confirmation(
            email_address=user.email,
            email_token=token
        )
        user = user.mark_activation_email_as_sent()
        user_repository.update_user(user)
        db.commit()


@atomic
def discard_expired_users():
    """
    unconfirmed stales accounts are deleted after settings.EMAIL_CONFRIMATION_LINK_TTL seconds after creation.
    """
    now = int(time.time())
    users = user_repository.get_multiple_users_by_field('status', UserStatus.EMAIL_CONFIRMATION_PENDING.value)
    for user in users:
        if now - user.activation_email_sent_at > settings.EMAIL_CONFIRMATION_LINK_TTL:
            user_repository.delete(user)


tasks = [
    process_locked_users,
    discard_expired_users
]

if __name__ == '__main__':
    init_db(db)
    for task in tasks:
        try:
            task()
        except:
            LOGGER.core.exception('Error processing %s', task)
