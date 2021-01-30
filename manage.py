import hashlib
import json
import os
import typing
from getpass import getpass
from json import JSONDecodeError
from typing import Dict

import click
import requests
from requests import HTTPError


class Client:
    def __init__(self, url):
        self.url = url
        self.token_file = '/tmp/____client_token'
        self._token = None
        self._user_id = None

    @property
    def is_logged_in(self):
        return self.has_token

    @property
    def user_id(self):
        if not self._user_id:
            self._get_credentials()
        return self._user_id

    def _clean_localstorage(self):
        try:
            os.remove(self.token_file)
        except FileNotFoundError:
            pass

    @property
    def has_token(self):
        if not self._token:
            self._get_credentials()
        return bool(self._token)

    def _get_credentials(self):
        try:
            if not self._token:
                with open(self.token_file, 'r') as f:
                    d = json.load(f)
                    self._user_id = d['user_id']
                    self._token = d['token']
        except FileNotFoundError:
            pass
        except JSONDecodeError:
            self._clean_localstorage()
        return self._token

    @staticmethod
    def _parse_token_from_cookies(cookies):
        cookie = cookies.get('Authorization')
        return cookie.replace('"', '').replace('Bearer ', '')

    def _get_cookie_from_token(self):
        return {'Authorization': 'Bearer {}'.format(self._get_credentials())}

    def _store_credentials(self, token: str):
        self._token = token
        with open(self.token_file, 'w') as f:
            return json.dump(
                {
                    'user_id': self._user_id,
                    'token': self._token
                },
                f
            )

    def signup(self, payload: Dict):
        res = requests.post(self.url + '/auth/signup', data=json.dumps(payload))
        res.raise_for_status()
        return res.content

    def login(self, payload: Dict) -> typing.Tuple[str, str]:
        res = requests.post(self.url + '/auth/login', data=json.dumps(payload))
        res.raise_for_status()
        self._user_id = res.json()['user_id']
        self._store_credentials(self._parse_token_from_cookies(res.cookies))
        return self._user_id, res.cookies

    def logout(self):
        try:
            res = requests.post(self.url + '/auth/logout', cookies=self._get_cookie_from_token())
        except:
            pass
        self._clean_localstorage()
        return True

    def get_details(self):
        res = requests.get(
            self.url + '/user',
            cookies=self._get_cookie_from_token()
        )
        res.raise_for_status()
        return res.json()

    def get_characters(self):
        res = requests.get(
            self.url + '/user/character',
            cookies=self._get_cookie_from_token()
        )
        res.raise_for_status()
        return res.json()

    def create_character(self, payload: Dict):
        res = requests.post(
            self.url + '/user/character',
            cookies=self._get_cookie_from_token(),
            data=json.dumps(payload)
        )
        res.raise_for_status()
        return res.json()

    def authenticate_character(self, character_id: str) -> typing.Tuple[str, str]:
        payload = {
            'entity_type': 'character',
            'entity_id': character_id
        }
        res = requests.post(
            self.url + '/auth/token',
            data=json.dumps(payload),
            cookies=self._get_cookie_from_token()
        )
        res.raise_for_status()
        return res.json(), res.cookies


def _get_login_data():
    email = input('Enter email: ')
    password = getpass('Enter Password: ')
    payload = {
        'email': email,
        'password': hashlib.sha256(password.encode()).hexdigest()
    }
    return payload


def get_client() -> Client:
    def get_client_url():
        try:
            with open('/tmp/__pm_client_url', 'r') as f:
                d = f.read()
                click.echo('using url %s' % d)
        except FileNotFoundError:
            d = input('Enter projectm base URL (default http://localhost:60161) : ')
            d = d or 'http://localhost:60161'
            check_res = requests.get(d + '/auth/login')
            try:
                check_res.raise_for_status()
            except HTTPError as e:
                if e.response.status_code == 405:
                    pass
                else:
                    print('Error checking Client URL: ', str(e))
                    exit(1)

            with open('/tmp/__pm_client_url', 'w') as f:
                f.write(d)
        return d
    url = get_client_url()
    return Client(url)


@click.group(name='client')
def main():
    pass


@main.group(name='user')
def user():
    pass


@user.command()
def signup():
    client = get_client()
    if client.is_logged_in:
        click.echo('Logged in. Logout first')
        return
    payload = _get_login_data()
    response = client.signup(payload)
    click.echo('Signup response: %s' % response)


@user.command()
def login():
    client = get_client()
    if client.is_logged_in:
        click.echo('Already logged in. Logout first')
        return
    payload = _get_login_data()
    response = client.login(payload)
    click.echo('Login response: %s - Cookies: %s' % response)


@user.command()
def logout():
    client = get_client()
    if not client.is_logged_in:
        click.echo('Not logged in')
        return
    response = client.logout()
    click.echo('Logout response: %s' % response)


@user.command()
def details():
    client = get_client()
    if not client.is_logged_in:
        click.echo('Not logged in')
        return
    response = client.get_details()
    click.echo('Response:\n%s' % json.dumps(response, indent=2))


@main.group()
def character():
    pass


@character.command()
def ls():
    client = get_client()
    if not client.is_logged_in:
        click.echo('Not logged in')
        return
    response = client.get_characters()
    click.echo('Response:\n%s' % json.dumps(response, indent=2))


@character.command()
def authenticate():
    client = get_client()

    if not client.is_logged_in:
        click.echo('Not logged in')
        return

    by_name = {ch['name']: ch for ch in client.get_characters()['data']}
    if not by_name:
        click.echo('No characters created')
        return

    character_name = input('Enter your chacter name: ')
    try:
        character_id = by_name[character_name]['character_id']
    except KeyError:
        click.echo('No character with that name, available: [%s]' % ', '.join(list(by_name.keys())))
        return
    response = client.authenticate_character(character_id)

    click.echo('Authenticate Character response:\n%s - Cookies: %s' % response)


if __name__ == '__main__':
    main()
