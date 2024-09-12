from flask import Flask
from threading import Thread

app = Flask('')

# Ruta principal para verificar que el bot está vivo
@app.route('/')
def index():
    return "Your bot is alive!"

# Ruta de ping para mantener el bot despierto
@app.route('/ping')
def ping():
    return "Pong", 200

def run():
    # Asegúrate de que Flask escuche en 0.0.0.0
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    # Inicia un hilo separado para correr el servidor Flask
    server = Thread(target=run)
    server.start()
