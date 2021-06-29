install:
	pipenv install --dev --ignore-pipfile


update:
	pipenv update --dev
	pipenv check
	pipenv graph

