Project M
---

E' necessario settare una variabile d'ambiente PROJECTM_ENV.
In sviluppo dev'essere "development".


**SETUP**: 
```bash
git pull projectm_url
cd projectm
virtualenv -p python3.6 venv
. venv/bin/activate
pip install -r requirements.txt
PROJECTM_ENV=development python -m alembic_script upgrade head
```

**RUN TESTS WITH COVERAGE**:
```
$ cd projectm
$ bash coverage.sh

then open with browser projectm/htmlcov/index.html
```
**RUN**:

```bash
cd projectm
. venv/bin/activate
PROJECTM_ENV=development python -m core.app
PROJECTM_ENV=development python -m core.src.world.run_websocket

(in two separated terminals, obv)
```

**CLIENT (API test)**:

```bash
cd projectm
. venv/bin/activate
python -m manage --help 
```


**IN THE NEED OF CUSTOMIZED SETTINGS**:
```bash
cd projectm
cd etc/<your_env_name, i.e. development>
cp settings.conf local-settings.conf
```
Then use your favorite editor to customize local-settings.conf file and fit your needs.
Notes: 

- The filename is into `.gitignore`.
- Keys with typos are ignored and the default settings is used.



**TO AVOID DECLARE PROJECTM_ENV EVERYTIME**:

edit ~/.bashrc and add
```
export PROJECTM_ENV=development
```
at the end of the file, to avoid explicitly declare the variable at every execution.


**CUSTOMIZING APP SETTINGS VIA `local-settings.conf`:**

```bash

$ cd projectm
$ cd etc/<your_env_name, i.e. development>
$ cp settings.conf local-settings.conf
```
Then use your favorite editor to customize local-settings.conf file and fit your needs.

Notes: 
- The filename is into `.gitignore`.
- Keys with typos are ignored and the default settings is used.

