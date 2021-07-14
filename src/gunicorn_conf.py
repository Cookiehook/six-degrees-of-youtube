import os

bind = "0.0.0.0:5000"
workers = 1
threads = 40
wsgi_app = "src.app:app"

accesslog = "/logs/gunicorn_access.log"
errorlog = "~"  # "~" means stderr
loglevel = os.getenv("GUNIORN_LOG_LEVEL", "debug")
