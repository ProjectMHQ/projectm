# Project M


***

### World commands and events for private namespaces

Almost any event may come asynchronously, at any time, on the same topic, if it is required to update the client status.

#### - look

- request topic: `cmd`
- request payload: `look <abbrev>` [ TODO - WIP ]
- request payload: `look <abbrev> <abbrev>` [ TODO - WIP]
- request payload: `look <dir: n\s\w\e\u\d>`
- response topic: `system`
- response body: 
```
{
    "event": "look",
    "title": str,
    "description": str,
    "content": [
        {
        "e_id": int,
        "excerpt": str,
        "name": optional[str],
        "status": int,
        "type": int
        },
        ...
    ]
}
```


#### - getmap

- request topic: `cmd`
- request payload: `getmap`
- response topic: `system`
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

#### - movement

- request topic: `cmd`
- request payload: `n, s, w, e, u, d  (north, south, west, east, up, down)`
- response topic: `msg`

Flow:

1) The server receives the command and checks about the movement. 
   This first step may lead to an error (see below, response errors).

2) Once a movement is authorized, an event of type `begin` is fired. 
   In this state the movement can be interrupted.

3) Another movement check is done to ensure the movement can still be done.
   The check may lead to an error.
   If the movement is authorized again, it cannot be interrupted anymore and it is
   immediately executed. An event with of type `success` is emitted and the entity is 
   finally moved into another location.
   
4) Once a movement is completed and the entity position change, `map` and `look` events are fired as well.
 
Events:
 
* Movement begin:
```
* Textual output on MSG channel about movement begin * 
```
* Movement success:
```
* Textual output on MSG channel about movement begin * 
```
* Movement interrupted:
```
* Textual output on MSG channel about movement begin * 
```
* Terrain error:
```
* Textual output on MSG channel about movement begin * 
```
