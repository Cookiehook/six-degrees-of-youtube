.PHONY: deploy

clean:
	rm -rf .pytest_cache .coverage

install:
	pipenv install --dev --ignore-pipfile

update:
	pipenv update --dev
	pipenv check
	pipenv graph

test: clean
	pipenv run flake8
	export six_degrees_of_youtube_db_dsn="sqlite:///:memory:" && pipenv run pytest --cov src --cov-report term-missing

run:
	docker-compose up --build

deploy:
	cd deployment && terraform init && terraform apply

destroy:
	cd deployment && terraform init && terraform destroy
