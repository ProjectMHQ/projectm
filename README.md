Project M
---

**ENVIRONMENT**:

It's necessary to declare an environment variable (for development, it must be set to `development`).

You can either specify at every command (like in the code snippets below) or set it in your `~/.bashrc`:

```
export PROJECTM_ENV=development
```
at the end of the file.

**SETUP**: 
```bash
# first install redis via your package manager,
# then do the following:
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

# type each of these lines in a different terminal
redis-server # if not running as a service
PROJECTM_ENV=development python -m core.src.auth.app
PROJECTM_ENV=development python -m core.src.world.run_websocket
PROJECTM_ENV=development python -m core.src.world.run_worker
```

**CLIENT (API test)**:

```bash
cd projectm
. venv/bin/activate
python -m manage --help 
```

**FIRST USER SIGNUP**
```bash
python -m manage user signup
```

**POPULATE TEST MAP**:
```bash
 PROJECTM_ENV=development python -m tools.txt_map_to_redis
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

