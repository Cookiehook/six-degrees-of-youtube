clean:
	rm -r .pytest_cache .coverage

install:
	pipenv install --dev --ignore-pipfile

update:
	pipenv update --dev
	pipenv check
	pipenv graph

test: clean
	pipenv run pytest --cov src --cov-report term-missing
