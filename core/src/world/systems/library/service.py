import json
from json import JSONDecodeError

from pycomb.exceptions import PyCombValidationError

from core.src.world.systems.library.validator import LibraryJSONFileValidator


class LibrarySystemService:
    def __init__(self, entity, repository=None):
        from core.src.world.builder import library_repository
        self.repository = repository or library_repository
        self.entity = entity

    async def load(self, location: str, alias: str, overwrite=False):
        if not overwrite:
            if await self.repository.exists(alias):
                await self.entity.emit_msg('Alias {} already exists, do you mean "reload"?'.format(alias))
                return
        else:
            if not await self.repository.exists(alias):
                await self.entity.emit_msg('Alias {} does not exists, do you mean "load"?'.format(alias))
                return

        if location == 'json':
            data = await self._import_json_library(alias)
            if not overwrite:
                await self.repository.save_library_item(data)
            else:
                await self.repository.update_library_item(data)
            await self.entity.emit_msg(('Library {} {}'.format(alias, 'reloaded' if overwrite else 'loaded')))

    async def ls(self, pattern: str, offset: int = 0, limit: int = 20):
        data = await self.repository.get_libraries(pattern, offset=offset, limit=limit)
        data and await self.entity.emit_msg(data)

    async def _import_json_library(self, alias):
        try:
            from core.src.world.builder import WORLD_SYSTEM_PATH
            filepath = '{}/core/src/world/library/json/{}.json'.format(WORLD_SYSTEM_PATH, alias)
            with open(filepath, 'r') as f:
                try:
                    data = json.load(f)
                    LibraryJSONFileValidator(data)
                    return data
                except JSONDecodeError:
                    return await self.entity.emit_msg("Library file {}.json decode error".format(alias))
        except FileNotFoundError:
            return await self.entity.emit_msg("Library file {}.json not found".format(alias))
        except PyCombValidationError as e:
            return await self.entity.emit_msg("Library file {}.json syntax error: \n{}".format(alias, e))
