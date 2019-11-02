Project M
---

E' necessario settare una variabile d'ambiente PROJECTM_ENV.
In sviluppo dev'essere "development".


##### Only the brave:

SETUP: 
```bash
$ git pull projectm_url
$ cd projectm
$ virtualenv -p python3.6 venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ PROJECTM_ENV=development python -m alembic_script upgrade head
```

RUN:

```bash
$ cd projectm
$ . venv/bin/activate
$ PROJECTM_ENV=development python -m core.app
```


CLIENT (API test):

```bash
$ cd projectm
$ . venv/bin/activate
$ python -m manage --help 
```


CUSTOMIZING APP SETTINGS VIA `local-settings.conf`:
```bash
$ cd projectm
$ cd etc/<your_env_name, i.e. development>
$ cp settings.conf local-settings.conf

Then use your favorite editor to customize local-settings.conf file and fit your needs.

Notes: 
- The filename is into `.gitignore`.
- Keys with typos are ignored and the default settings is used.

```