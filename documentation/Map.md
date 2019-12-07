# Project M

***

## Map events

#### Flow:

- User enters an area
- Fetch rooms from the DB
- Subscribe events for area
- Return to the user the area square and the entities that populates it
- Update the map with events related to entities


#### Events:

##### - map_event

The first event to render the map is the same as the `getmap` response.
This event is triggered everytime a user join a new room (on connect, after teleport \ movement, etc.)

```
{
    "event": "map", 
    "base": [uint8, uint8, uint8... ]
    "data": [],
    "shape": [int, int]
}
```

The `base` array contain the tiles id, is a 1d row-major array representing the entire area.  
The `data` array contains entities on the map in two forms: Local and Remote.
The `shape` array contains the map size and shape.

##### - map_event.data

The entities are indexed with a position relative to the last map the user got from the server:

With a 3x3 map the array would represent:

| | | | 
--- | --- | --- |
| 0 | 1 | 2 |
| 3 | 4 | 5 |
| 6 | 7 | 8 |

And an entity with value pos=4 would go in the center. 


If the entity is in the same room of the event receiver (as in this case with 4, since the character is always in the map center), data array is populated with:

```
{
    "e_id": int,
    "type": int,
    "pos": int, 
    "name" null \ string,
    "excerpt": string,
    "status": int
}
``` 

Otherwise, if the entity is in another room of the area:

```
{
    "e_id": int,
    "type": int, 
    "pos": int 
}
```

no details about it are returned.


---

##### - updates events 
  
Once the map is returned, updates events are triggered. As for the values of the data array, relative positions are used to push updates.

Three are the main events relative to entities and map, which are the following:

`entity_add`, which is triggered everytime an entity join the event receiver FOV. An entity may join the receiver FOV for many reasons: movement, teleport, connection, or because an item is dropped in the room from a character inventory, etc.

```json
{
  "event": "entity_add",
  "data": {
    "pos": 42,
    "e_id": 8,
    "type": 0
  }
}
```

The event, as the entries of `map_event.data`, could be enriched by name, status and excerpt, if happen in the same room of the character.

`entity_remove`, which is triggered everytime an entity left the event receiver FOV. An entity may left the receiver FOV for many reasons: movement, teleport, connection, or because an item that was in the room is picked up by a character.

```json
{
  "event": "entity_remove",
  "data": {
    "e_id": 8
  }
}
```

This event is slightly different from the others, as it lacks of some values, and carry only the entity_id, which is enough for a client to drop an entity from its storage and render.

`entity_change_pos` which is triggered everytime an entity change the position in the receiver FOV.
An entity may change position in the receiver FOV for less reasons than others events: movement, teleport. Any different behaviour should be handled by other events.

```json
{
  "event": "entity_change_pos",
  "data": {
    "e_id": 8,
    "pos": 42
  }
}
```
The position returned is the new position of the entity.


#### Notes

 - Since the relative position of the updates events is related to the current position of the user, is also related to the last map the user got, as it changes everytime the events receiver changes position. This behaviour should lead clients developers to cleanup any reference to the map and relative positions, as any relative position previously received become stale once the event receiver moves.
