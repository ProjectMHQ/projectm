PROJECTM_ENV=development RUNNING_TESTS=1 venv/bin/coverage run --source=core -m unittest discover tests.unit
venv/bin/coverage html
