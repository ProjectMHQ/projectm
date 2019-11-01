# Project M


***

## Websocket Flow Documentation

Endpoints:
 - development: `localhost:60160` (or check `local-settings.conf`)
 - staging: `staging.pm.chatsubo.it`


#### Character Creation & Authentication on '/' namespace

##### Create Character
- Requires Bearer Token: YES
- Namespace: `/`
- Topic: `create`
- Payload: ` {token: String, name: String}`
- OnSuccess: ` {character_id: String[UUID], success: true} `

##### Authenticate Character
- Requires Bearer Token: YES
- Namespace: `/`
- Topic: `auth`
- Payload: ` {token: String, character_id: String[UUID]}`
- OnSuccess: ` {channel_id: String[256bit hex], timeout: int} `



##### Character Impersonation on the private namespace

Flow:
- Once authenticated, quit the main namespace
- Join the private namespace returned by the authentication process before `timeout`.
- From this point, messages must be sent on the private namespace.
- The namespace is ephemeral and changes at every authentication.
- Client disconnected by legacy network disconnections may rejoin a previous channel before timeout without re-authenticating. 
- To keep the namespace alive client must answer `PING` messages with `PONG` responses on the `presence` channel.

