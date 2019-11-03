PROJECTM_ENV=development RUNNING_TESTS=1 venv/bin/coverage run --source=core -m unittest discover tests.unit
PROJECTM_ENV=development RUNNING_TESTS=1 INTEGRATION_TESTS=1 venv/bin/coverage run --source=core -m unittest discover tests.integration
venv/bin/coverage html
