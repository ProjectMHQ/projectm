import json
from json import JSONDecodeError

from core.src.world.builder import library_repository
from etc import settings


class LibrarySystemService:
    def __init__(self, entity, repository=library_repository):
        self.repository = repository
        self.entity = entity

    async def load(self, location, alias):
        if self.repository.exists(alias):
            return await self.entity.emit_msg('Alias {} already exists'.format(alias))
        if location not in ('json',):
            return await self.entity.emit_msg("Library location must be 'json' or 'python'")
        if location == 'json':
            await self._import_json_library(alias)

    async def _import_json_library(self, alias):
        try:
            with open('{}/json/{}.json'.format(settings.LIBRARY_PATH, alias)) as f:
                try:
                    data = json.load(f)
                except JSONDecodeError:
                    return await self.entity.emit_msg("Library file {}.json decode error".format(alias))
        except FileNotFoundError:
            return await self.entity.emit_msg("Library file {}.json not found".format(alias))
        try:
            data = ValidateLibraryFile(data)
        except:
            return await self.entity.emit_msg("Library file {}.json syntax not valid".format(alias))
