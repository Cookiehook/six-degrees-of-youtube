.PHONY: test lint

clean:
	rm -rf .pytest_cach .coverage

lint:
	pipenv run flake8

test: Pipfile.lock lint
	pipenv run pytest --cov=src

Pipfile.lock: Pipfile
	pipenv update --dev
