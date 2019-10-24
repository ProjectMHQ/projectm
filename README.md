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
$ PROJECTM_ENV=development python -m alembic_script upgrade_head
```

RUN:

```bash
$ cd projectm
$ . venv/bin/activate
$ PROJECTM_ENV=development python -m core.app
```


CLIENT (API test)

```bash
$ cd projectm
$ . venv/bin/activate
$ python -m manage --help 
```
