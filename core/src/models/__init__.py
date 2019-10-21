from .user import *

from etc import settings
if settings.RUNNING_TESTS:
    def setup_db():
        from core.src import database
        s = database.db()
        Base.metadata.create_all(s.bind)
    setup_db()
