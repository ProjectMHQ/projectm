set -e

PROJECTM_ENV=development RUNNING_TESTS=1 venv/bin/coverage run --source=core -m unittest discover tests.unit
mv .coverage .coverage.unit
PROJECTM_ENV=development RUNNING_TESTS=1 INTEGRATION_TESTS=1 venv/bin/coverage run --source=core -m unittest discover tests.integration
mv .coverage .coverage.integration
venv/bin/coverage combine
venv/bin/coverage html
