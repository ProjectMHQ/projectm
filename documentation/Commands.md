# Project M


***

#### World commands and events for private namespaces

Almost any event may come asynchronously, at any time, on the same topic, if it is requred to update the client status.

##### - look

- request topic: `cmd`
- request payload: `look [id]`
- response topic: `msg`
- response body: 
```
{
    "event": "look",
    "title": str,
    "description": str,
    "content": [
        {"id": integer, "descr": str}, ...
    ]
}
```


##### - getmap

- request topic: `cmd`
- request payload: `getmap`
- response topic: `map`
- response body: 
```
{
    "event": "map", 
    "base": [] # 81 entries fixed size array, uint8 (9x9 row-major),
    "data": [
        {
            "type": int, # entity type
            "pos": int # relative pos, min 0, max 81
        }
    ]
}
```

##### - movement

- request topic: `cmd`
- request payload: `n, s, w, e, u, d  (north, south, west, east, up, down)`
- response topic: `msg`
- response error:
```
{
    "event": "move",
    "status": "error",
    "message": "You cannot go there"
}
```
- response:

```
** Afther checking the movement can be done, the first event is fired. 
   In this state the movement can be interrupted:

{
    "event": "move",
    "status": "begin",
    "message": "You begin to move to <direction>"
}

** Right before moving this other event is fired. 
   In this state the movement cannot be interrupted anymore:

{
    "event": "move",
    "status": "done",
    "message": "You move to <direction>"
}
```
Once a movement is completed and the entity position changes, `getmap` and `look` events are fired as well.