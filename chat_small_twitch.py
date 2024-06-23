import os
import time
import argparse
from datetime import datetime
from twitchchatreader import TwitchChatReader
from twitchchatreaderevents import CommentEvent, ConnectEvent
import re

# Eliminar el contenido del archivo messages.txt al iniciar el programa
def initialize_file():
    with open("historial.txt", "w", encoding="cp1252") as file:
        file.write("")

def read_messages_from_file():
    with open("historial.txt", "r", encoding="cp1252") as file:
        return file.readlines()

def save_messages_to_file(messages):
    with open("historial.txt", "w", encoding="cp1252") as file:
        file.writelines(messages)


def limpiar_texto(texto):
    # Expresión regular para mantener letras, números, espacios, acentos, ñ y signos de puntuación
    patron = r'[^a-zA-Z0-9\sáéíóúüñÁÉÍÓÚÜÑ._:\[\].,!?¿¡]'
    texto_limpio = re.sub(patron, '', texto)
    return texto_limpio

def on_comment_handler(event: CommentEvent):
    user = event.user.name
    comment = event.comment
    current_time = datetime.now().strftime("[%H:%M:%S]")
    new_message = f"{user}: {comment}\n"

    new_message=limpiar_texto(new_message)
    if comment:
        messages = read_messages_from_file()
        #if len(messages) >= 10:
            # Eliminar el mensaje más antiguo (el primer elemento de la lista)
            #messages.pop(0)
        # Añadir el nuevo mensaje
        messages.append(new_message)
        # Imprimir el mensaje para debug
        #print(new_message.encode('utf-8').decode('utf-8'))
        # Guardar los mensajes actualizados en el archivo
        save_messages_to_file(messages)

if __name__ == "__main__":
    # Configurar argparse para manejar los argumentos de la línea de comandos
    parser = argparse.ArgumentParser(description="Twitch Chat Reader")
    parser.add_argument("--channel", type=str, help="Nombre del canal de Twitch")
    args = parser.parse_args()

    # Inicializar el archivo
    initialize_file()

    # Utilizar el nombre del canal proporcionado como argumento
    twitch_reader = TwitchChatReader(args.channel)

    @twitch_reader.on("comment")
    def on_comment(event: CommentEvent):
        on_comment_handler(event)

    @twitch_reader.on("connect")
    def on_connect(event: ConnectEvent):
        print("Connection established!")

    while True:
        time.sleep(1)  # Mantener el bucle principal funcionando para escuchar el chat de Twitch
