FROM python:3.8

WORKDIR /app/
ENV LANG "en_US.UTF-8"
ENV PYTHONPATH .
ENV PYTHONUNBUFFERED 1
RUN mkdir /logs

# Install dependencies
RUN pip install pipenv==2020.11.15
COPY Pipfile* /app/
RUN pipenv install --ignore-pipfile

# Copy in application code
COPY src /app/src/

CMD ["pipenv", "run", "gunicorn", "--preload", "-c", "/app/src/gunicorn_conf.py"]
