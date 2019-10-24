Project M
---



##### Only the brave:

SETUP: 
```bash
$ git pull projectm_url
$ cd projectm
$ virtualenv -p python3.6 venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ python -m alembic_script upgrade_head
```

RUN:

```bash
$ cd projectm
$ . venv/bin/activate
$ python -m core.app
```


CLIENT (API test)

```bash
$ cd pojectm
$ . venv/bin/activate
$ python -m manage --help 
```
