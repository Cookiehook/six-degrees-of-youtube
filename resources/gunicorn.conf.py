import multiprocessing
import os

bind = "0.0.0.0:5000"
# bind = "unix:/app/gunicorn.sock"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 80
wsgi_app = "src.app:app"

accesslog = "/logs/gunicorn_access.log"
errorlog = "~"  # "~" means stderr
loglevel = os.getenv("GUNIORN_LOG_LEVEL", "debug")