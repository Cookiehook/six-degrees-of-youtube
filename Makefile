clean:
	rm -rf .pytest_cache .coverage build

install:
	pipenv install --dev --ignore-pipfile

update:
	pipenv update --dev
	pipenv check
	pipenv graph

test: clean
	pipenv run flake8
	pipenv run pytest --cov src --cov-report term-missing

deploy-prod:
	TF_WORKSPACE="prod" TF_S3_BUCKET="terraform-workspaces-shaunharrison" deploy/scripts/deploy.sh

destroy-prod:
	TF_WORKSPACE="prod" TF_S3_BUCKET="terraform-workspaces-shaunharrison" deploy/scripts/destroy.sh
