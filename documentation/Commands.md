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
