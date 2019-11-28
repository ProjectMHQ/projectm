# Project M


***

## Websocket Flow Documentation

Endpoints:
 - development: `localhost:60160` (or check `local-settings.conf`)
 - staging: `staging.pm.chatsubo.it`

Api Flow:
- Use main namespace `/` to create or authenticate a character. 
- Once a character is authenticated, quit the main namespace. 
- Join the private namespace `/<channel_id>` returned by the authentication process before `timeout`.
- From this point, world messages must be sent on the private namespace. The namespace is ephemeral and changes at every authentication.
- Clients disconnected by legacy network disconnections may rejoin a previous channel before timeout without re-authenticating. 
- To keep the namespace alive client must answers `PING` messages with `PONG` responses on the `presence` topic.

#### Character Creation & Authentication on '/' namespace

##### Create Character

Before proceeding request a token on the REST for the `world:create` topic.

- Requires Bearer Token: NO
- Namespace: `/`
- Topic: `create`
- Payload: ` {token: String, name: String}`
- OnSuccess: ` {character_id: String[UUID], success: true} `

##### Authenticate Character

Before proceeding request a token on the REST for the `world:auth` topic.

- Requires Bearer Token: NO
- Namespace: `/`
- Topic: `auth`
- Payload: ` {token: String, character_id: String[UUID]}`
- OnSuccess: ` {channel_id: String[256bit hex], timeout: int} `



#### Character Impersonation on the private namespace

