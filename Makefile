.PHONY: deploy

clean:
	rm -rf .pytest_cache .coverage

install:
	pipenv install --dev --ignore-pipfile

update:
	pipenv update --dev
	pipenv check
	pipenv graph

run:
	docker-compose up --build

test: clean
	pipenv run flake8
	pipenv run pytest --cov src --cov-report term-missing
