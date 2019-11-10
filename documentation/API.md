# Project M

***

## API Flow Documentation

Endpoints:

development: localhost:60161 (or check local-settings.conf)
staging: staging.pm.chatsubo.it

Flow:
- Create account with credentials (email, password):  ```POST /auth/signup => SIGNUP_OK```
- Login in to the platform with credentials (email, password): ```POST /auth/login => LOGIN_OK (auth cookie set)```
- From now on every request must be authenticated (authorization headers) until logout.
- Ask world:create and world:auth tokens in order to fill actions on the websocket 
- Ask characters of a user: ```GET /user/character => {data: Array}```
- Logout from the platform with: ```POST /auth/logout => LOGOUT_CONFIRMED  (auth cookie removed)```

### Authentication

##### Signup
- Requires Bearer Token: NO
- URL: ```/auth/signup```
- Method: ```POST```
- Payload: ```{"email": String, "password": String}```
- Response: ```200 SIGNUP_OK```
- Set-Cookie: NO

Note: _Password MUST be hashed_

##### Confirm Email
- Requires Bearer Token: YES
- URL: ```/auth/confirm_email/<email_token>```
- Method: ```GET```
- Payload: EMPTY
- Response: ```200 EMAIL_CONFIRMED```
- Set-Cookie: NO

Note: _Confirmation links are sent to the email address via Twilio' SendGrid_

##### Login
- Requires Bearer Token: NO
- URL: ```/auth/login```
- Method: ```POST```
- Payload: ```{"email": String, "password": String}```
- Response: ```200 LOGIN_OK```
- Set-Cookie ```Authentication: Bearer <token>```


##### Logout
- Requires Bearer Token: YES
- URL: ```/auth/logout```
- Method: ```POST```
- Payload: EMPTY
- Response: ```200 LOGOUT_OK```
- Set-Cookie: ```Authentication: ```

##### Token
- Requires Bearer Token: YES
- URL: ```/auth/token```
- Method: ```POST```
- Payload: ```{"context": String, "id": String}```
- Response: ```{"expires_at": Integer, "token": String}```
- Params:
  - ```context: ```
     - ```world:create``` To create a new character
     - ```world:auth``` To authorize an existing character

##### User's characters
- Requires Bearer Token: YES
- URL: ```/user/character```
- Method: ```GET```
- Payload: EMPTY
- Response: ```{"data": Array}```