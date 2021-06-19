FROM python:3.9.5

WORKDIR /app/
ENV LANG en_US.UTF-8
ENV PYTHONPATH .
ENV PYTHONUNBUFFERED 1

RUN pip install pipenv==2021.5.29
COPY Pipfile* /app/
RUN pipenv install --dev --ignore-pipfile

COPY stub_youtube /app/stub_youtube/

EXPOSE 5000
RUN find /app
CMD ["pipenv", "run", "python", "stub_youtube/app.py"]