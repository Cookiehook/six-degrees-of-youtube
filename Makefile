.PHONY: deploy

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

deploy:
	(cd ./deploy && terraform init && terraform apply)

re-deploy:
	(cd ./deploy && terraform init && terraform apply -replace="null_resource.prepare_archive")

destroy:
	(cd ./deploy && terraform init && terraform destroy)
