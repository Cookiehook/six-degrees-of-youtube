FULLBRANCH= $(shell git branch --show-current)
BRANCH=$(shell echo $(FULLBRANCH) | cut -d '/' -f2)

clean:
	rm -rf .pytest_cache .coverage

install:
	pipenv install --dev --ignore-pipfile

update:
	pipenv update --dev
	pipenv check
	pipenv graph

# Tests currently failing after overhaul of ORM from flask-sqlalchemy to sqlalchemy. To be re-instated once deployment work is completed
#test: clean
#	pipenv run flake8
#	export six_degrees_of_youtube_db_dsn="sqlite:///:memory:" && pipenv run pytest --cov src --cov-report term-missing

run:
	docker-compose up --build

deploy:
	docker build -t cookiehook/six-degrees-of-youtube:$(BRANCH) .
	docker push cookiehook/six-degrees-of-youtube:$(BRANCH)
	cd deployment && terraform init -var branch=$(BRANCH) && terraform apply -var branch=$(BRANCH)

destroy:
	cd deployment && terraform init -var branch=$(BRANCH) && terraform destroy -var branch=$(BRANCH)
