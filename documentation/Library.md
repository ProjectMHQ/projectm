# Project M


***

### Usage of the static Library

The library is the implementation of almost anything in Projectm. From a weapon to an NPC,
everything must came out from the library.

The current library implementation is JSON-files based. 
The files must be located into a library path and manually loaded into redis.

The library is actually "not-so-static" since contents can be hotloaded and unloaded dinamically.

A Library example file is `world/library/json/coltello.json`

```json
{
  "alias": "coltello",
  "components": {
    "attributes": {
      "keyword": "coltello",
      "name": "il coltello del potere",
      "description": "Con questo coltello potresti skillare, ma non c'è"
    },
    "weapon": "knife"
  }
}
```

To load `coltello` into the library (alias is a unique constraint) just do, as an admin:

```
@lib load coltello
```

A reload command is available as well:
```
@lib reload coltello
```

And the library content can be seen with
```
@library ls colte*
```

Quite straightforward.

### Instancing library elements into the words, as entities

Once an element is load into the library, it can be instantiated into the world with `@inst` command, 
which works as follows:

```
@inst create coltello @here
```

create an instance of the coltello Entity in the current room (@here) and saves it on the db.

More maintenance sub-commands for `@inst` are available:

```
@inst destroy coltello <entity_id> 
@inst destroy <whatever> <entity_id> [--force] 
```

The command destroy the entity (destroying a character is not allowed) in the current location, 
the instance type must match to do a double check. 
This can be bypassed using --force and a dummy placeholder for the instance type.

Playing with entities and components, may happen often to screw everything up.
The --force option try to make the things right, but it can fail to obtain the Position component.

In that case, zombies entities can be left by the system on the map.
At this very moment no cleanup system tasks are implemented, but the 'cleanup' command can be
used to remove zombie entities from the map.

```
@inst cleanup <entity_id> @here
``` 

This command deletes the entity reference on the rooms DB, cleaning up the zombie from the map.
