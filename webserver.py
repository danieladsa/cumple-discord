from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def index():
    return "Your bot is alive!"

def run():
    # Asegúrate de que Flask escuche en 0.0.0.0
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()
