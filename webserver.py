from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def index():
    return "Your bot is alive!"

def keep_alive():
    server = Thread(target=app.run)
    server.start()