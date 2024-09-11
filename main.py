import discord
from discord.ext import commands, tasks
import datetime
import json
import aiohttp
import os 
import webserver
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Intenciones para el bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Necesario para obtener la lista de miembros

# Inicialización del bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Diccionario para almacenar los cumpleaños, mensajes y enlaces de imágenes
birthdays = {}
channel_map = {}
birthday_messages = {}
birthday_images = {}  # Diccionario para almacenar las URLs de las imágenes

# Función para guardar los datos en un archivo JSON
def save_data():
    with open('data.json', 'w') as f:
        json.dump({'birthdays': birthdays, 'channel_map': channel_map, 'birthday_messages': birthday_messages, 'birthday_images': birthday_images}, f)

# Función para cargar los datos desde un archivo JSON
def load_data():
    global birthdays, channel_map, birthday_messages, birthday_images
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            birthdays = data.get('birthdays', {})
            channel_map = data.get('channel_map', {})
            birthday_messages = data.get('birthday_messages', {})
            birthday_images = data.get('birthday_images', {})
    except FileNotFoundError:
        birthdays = {}
        channel_map = {}
        birthday_messages = {}
        birthday_images = {}

# Comando para enviar un mensaje privado al usuario
@bot.command(name='saludo', help='Envía un mensaje privado con un saludo. Uso: !saludo')
async def saludo(ctx):
    try:
        await ctx.author.send('¡Hola! 👋')  # Envía un mensaje privado al autor del comando
        await ctx.send('Te he enviado un saludo por mensaje privado.')
    except discord.Forbidden:
        await ctx.send('No pude enviarte un mensaje privado. Asegúrate de tener habilitados los mensajes directos.')

# Evento que se ejecuta cuando el bot se conecta
@bot.event
async def on_ready():
    load_data()
    check_birthdays.start()
    print(f'{bot.user} se ha conectado a Discord!')

# Comando para que los usuarios ingresen su cumpleaños
@bot.command(name='cumple', help='Guarda tu cumpleaños. Uso: !cumple DD/MM')
async def cumple(ctx, date):
    try:
        # Intentar convertir la fecha ingresada en un objeto datetime
        birthday = datetime.datetime.strptime(date, '%d/%m')
        # Guardar la fecha de cumpleaños del usuario
        birthdays[str(ctx.author.id)] = date
        channel_map[str(ctx.author.id)] = str(ctx.channel.id)  # Guardar el canal donde se guarda el cumpleaños
        save_data()
        await ctx.send(f'Tu cumpleaños ha sido guardado: {date}')
    except ValueError:
        await ctx.send('Por favor ingresa la fecha en formato DD/MM.')

# Comando para subir la URL de una imagen para otro usuario
@bot.command(name='subirimagen', help='Asocia una imagen al cumpleaños de un usuario. Uso: !subirimagen @usuario URL')
async def subirimagen(ctx, amigo: discord.Member, url):
    amigo_id = str(amigo.id)

    # Verificar que el amigo haya registrado su cumpleaños
    if amigo_id not in birthdays:
        await ctx.send(f'{amigo.name} no ha registrado su cumpleaños.')
        return
    
    try:
        # Verificar si el enlace apunta a una imagen válida
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200 and resp.headers['Content-Type'].startswith('image/'):
                    # Guardar la imagen asociada al amigo
                    birthday_images[amigo_id] = url
                    save_data()
                    await ctx.send(f'La imagen ha sido guardada correctamente para {amigo.name}.')
                else:
                    await ctx.send('El enlace no es una imagen válida.')
    except Exception as e:
        await ctx.send(f'Error al verificar la imagen: {str(e)}')

@bot.command(name='borrartodo', help='Borra todos los mensajes enviados por el bot en el canal actual')
async def borrartodo(ctx):
    def is_bot_message(message):
        return message.author == bot.user  # Verifica si el mensaje fue enviado por el bot

    deleted = await ctx.channel.purge(limit=100, check=is_bot_message)
    await ctx.send(f'Se han borrado {len(deleted)} mensajes enviados por el bot.', delete_after=5)

# Comando para mostrar la lista de usuarios registrados con su cumpleaños
@bot.command(name='listacumples', help='Uso: !listacumples')
async def listacumples(ctx):
    if not birthdays:
        await ctx.send('No hay cumpleaños registrados.')
    else:
        message = 'Lista de cumpleaños registrados:\n'
        for user_id, date in birthdays.items():
            user = await bot.fetch_user(user_id)
            message += f'{user.name}: {date}\n'
        await ctx.send(message)

# Comando para agregar un mensaje oculto de cumpleaños para un amigo
@bot.command(name='mensajecumple', help='Uso: !mensajecumple amigo mensaje')
async def mensajecumple(ctx, amigo: discord.Member, *, mensaje):
    amigo_id = str(amigo.id)
    autor_id = str(ctx.author.id)

    # Verificar si el amigo ha registrado su cumpleaños
    if amigo_id not in birthdays:
        await ctx.send(f'{amigo.name} no ha registrado su cumpleaños.')
    else:
        # Si el usuario no tiene mensajes almacenados, creamos una lista para ellos
        if amigo_id not in birthday_messages:
            birthday_messages[amigo_id] = []

        # Añadir el mensaje oculto
        birthday_messages[amigo_id].append({'from': autor_id, 'message': mensaje})
        save_data()
        await ctx.send(f'Tu mensaje para {amigo.name} ha sido guardado.')

# Tarea que se ejecuta diariamente para verificar los cumpleaños
@tasks.loop(hours=24)
async def check_birthdays():
    today = datetime.datetime.now().strftime('%d/%m')
    in_one_week = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%d/%m')

    for user_id, birthday in birthdays.items():
        channel_id = 751637993655238729
        
        # Verifica si hoy es el cumpleaños
        if birthday == today:
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    # Verificar si el usuario tiene una imagen asociada
                    if user_id in birthday_images:
                        await channel.send(f'¡Feliz cumpleaños, <@{user_id}>! 🎉🎂', embed=discord.Embed().set_image(url=birthday_images[user_id]))
                    else:
                        await channel.send(f'¡Feliz cumpleaños, <@{user_id}>! 🎉🎂')

            # Enviar mensajes ocultos al usuario que está de cumpleaños
            if user_id in birthday_messages:
                user = await bot.fetch_user(user_id)
                for message in birthday_messages[user_id]:
                    friend = await bot.fetch_user(message['from'])
                    await user.send(f'Mensaje de cumpleaños de {friend.name}: {message["message"]}')
        
        # Verifica si el cumpleaños es en una semana
        elif birthday == in_one_week:
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(f'¡Recordatorio! El cumpleaños de <@{user_id}> es en una semana. 🎉')

# Iniciar el bot
webserver.keep_alive() 
bot.run(DISCORD_TOKEN)
