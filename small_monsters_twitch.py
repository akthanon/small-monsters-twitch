import pygame
import random
import os
import time
import threading
import imageio
from PIL import Image, ImageSequence

# Inicialización de Pygame
pygame.init()

# Nuevas dimensiones estándar con la misma relación de aspecto 16:9
# Nuevas dimensiones estándar con la misma relación de aspecto 16:9
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NPC Chat")

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)

# Colores claros aleatorios para los nombres de los personajes
BRIGHT_COLORS = [(255, 0, 0), (128, 128, 128), (0, 0, 255), (255, 128, 0), (255, 0, 255), (0, 128, 128), (123, 200, 123), (128, 0, 128), (255, 128, 0), (0, 100, 255)]


# Fuente para los nombres y los mensajes
pygame.font.init()
font_name = pygame.font.SysFont('Arial', 20)
font_message = pygame.font.SysFont('Arial', 16)

# Cargar imágenes de la carpeta "sprites"
sprite_images = []
sprite_folder = "sprites"
for filename in os.listdir(sprite_folder):
    if filename.endswith(".png"):  # Puedes ajustar esto si tienes otros formatos
        sprite_images.append(os.path.join(sprite_folder, filename))

# Estados de los personajes
STATE_LEFT = -1
STATE_STOP = 0
STATE_RIGHT = 1
STATE_FOLLOW = 2

# Velocidad constante para todos los personajes
SPEED = 4

# Parámetros de salto
JUMP_HEIGHT = 5
JUMP_DURATION = 0.1  # Duración de cada salto en segundos

# Grosor del contorno
OUTLINE_THICKNESS = 3

# Obtener valor numérico para cada letra del abecedario
def get_numeric_value(letter):
    return ord(letter.lower()) - ord('a')

# Función para dibujar texto con contorno
def draw_text_with_outline(surface, text, font, text_color, outline_color, pos):
    text_surface = font.render(text, True, text_color)
    outline_surface = font.render(text, True, outline_color)
    x, y = pos
    for dx in range(-OUTLINE_THICKNESS, OUTLINE_THICKNESS + 1):
        for dy in range(-OUTLINE_THICKNESS, OUTLINE_THICKNESS + 1):
            if dx != 0 or dy != 0:
                surface.blit(outline_surface, (x + dx, y + dy))
    surface.blit(text_surface, pos)

# Verificar si la carpeta "sprites" existe
if not os.path.exists("sprites"):
    raise FileNotFoundError("La carpeta 'sprites' no existe. Asegúrate de que la carpeta 'sprites' esté presente y contenga las imágenes de los sprites.")

class Character(pygame.sprite.Sprite):
    def __init__(self, name, image_path, x, y):
        super().__init__()
        self.name = name
        self.creation_time = time.time()
        self.numeric_value = sum(get_numeric_value(char) for char in name)
        
        # Color aleatorio claro para el nombre del personaje
        self.name_color = random.choice(BRIGHT_COLORS)
        
        # Cargar imagen y ajustar tamaño basado en el valor numérico
        self.original_image = pygame.image.load(sprite_images[self.numeric_value % len(sprite_images)]).convert_alpha()
        self.image = self.resize_image(self.original_image, 64)
        
        self.rect = self.image.get_rect()
        #self.rect = pygame.Rect(0, 0, 64, 96)
        self.rect.x = x
        self.base_y = y  # Posición base en y (parte inferior)
        self.rect.bottom = self.base_y
        self.speed = SPEED
        self.state = random.choice([STATE_LEFT, STATE_STOP, STATE_RIGHT])
        self.next_state_time = time.time() + random.randint(2, 10)
        self.last_jump_time = time.time()
        self.message = None
        self.message_start_time = None  # Agregado para rastrear el tiempo del mensaje
        self.dialog_rect = pygame.Rect(0, 0, 0, 0)  # Rectángulo para el área ocupada por el diálogo
        self.text_y = self.base_y - 96  # Posición Y original del texto

        # Superficie adicional para la imagen sobre el personaje
        self.extra_images = None
        self.current_frame_index = 0
        self.last_frame_update = pygame.time.get_ticks()
        self.old_skin = None
        self.gif_start_time = None  # Inicializar el tiempo de inicio del GIF
        self.target_name = None
        
        # Definir los comandos disponibles con sus descripciones
        self.commands = "!gif <nombre> !mover <direccion|nombre> !skinrandom !skin <nombre> !help"

        # Estado para saber si está mirando a la derecha
        self.facing_right = True

    def resize_image(self, image, new_width):
        width, height = image.get_size()
        aspect_ratio = height / width
        new_height = int(new_width * aspect_ratio)
        return pygame.transform.scale(image, (new_width, new_height))

    def update(self):
        # Cambiar de estado si ha pasado el tiempo

        if self.extra_images is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_frame_update > 60:
                self.current_frame_index = (self.current_frame_index + 1) % len(self.extra_images)
                self.last_frame_update = current_time

            # Verificar si han pasado 2 segundos desde que el GIF comenzó a mostrarse
            if current_time - self.gif_start_time > 7000:  # 2000 milisegundos = 2 segundos
                self.extra_images = None  # Dejar de mostrar el GIF
                self.gif_start_time = None  # Reiniciar el tiempo de inicio del GIF

        if time.time() >= self.next_state_time:
            self.state = random.choice([STATE_LEFT, STATE_STOP, STATE_RIGHT])
            self.next_state_time = time.time() + random.randint(2, 10)
            self.target_name = None

        # Actualizar posición basada en el estado actual
        if self.state == STATE_LEFT or self.state == STATE_RIGHT:
            if time.time() - self.last_jump_time >= JUMP_DURATION:
                self.rect.bottom = self.base_y - JUMP_HEIGHT if self.rect.bottom == self.base_y else self.base_y
                self.last_jump_time = time.time()

            if self.state == STATE_LEFT:
                self.rect.x -= self.speed
                if self.rect.left <= 0:
                    self.rect.left = 0
                    self.state = STATE_RIGHT
                self.facing_right = True
            elif self.state == STATE_RIGHT:
                self.rect.x += self.speed
                if self.rect.right >= SCREEN_WIDTH:
                    self.rect.right = SCREEN_WIDTH
                    self.state = STATE_LEFT
                self.facing_right = False

        if self.target_name in npc_dict:
            target_character = npc_dict[self.target_name]
            if target_character.rect.x < self.rect.x - 32:
                self.state = STATE_LEFT
            elif target_character.rect.x > self.rect.x + 32:
                self.state = STATE_RIGHT
            else:
                self.state = STATE_STOP

        # Eliminar el mensaje después de 5 segundos
        if self.message_start_time and time.time() - self.message_start_time > 60:
            self.message = None
            self.message_start_time = None
            self.dialog_rect = pygame.Rect(0, 0, 0, 0)


    def draw(self, screen):
        # Dibujar la imagen extra sobre el personaje si está disponible
        if self.extra_images:
            try:
                extra_image = self.extra_images[self.current_frame_index]
            except:
                self.current_frame_index = 0
                extra_image = self.extra_images[self.current_frame_index]
            extra_rect = extra_image.get_rect(center=(self.rect.centerx, self.rect.top - 64))
            screen.blit(extra_image, extra_rect)

        # Espejear la imagen si el personaje se está moviendo hacia la izquierda
        if not self.facing_right:
            flipped_image = pygame.transform.flip(self.image, True, False)
            screen.blit(flipped_image, self.rect)
        else:
            screen.blit(self.image, self.rect)
        
        # Renderizar el nombre y dibujarlo sobre la cabeza con el color aleatorio
        text_surface = font_name.render(self.name, True, self.name_color)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.text_y))
        draw_text_with_outline(screen, self.name, font_name, self.name_color, WHITE, (text_rect.x, text_rect.y))

        # Mostrar los comandos disponibles si hay un mensaje "help" activo
        if self.message == "!help":
            self.message = self.commands

        # Renderizar el mensaje y dibujarlo sobre el personaje
        if self.message and self.message != "!help":
            message_surface = font_message.render(self.message, True, BLACK)
            message_rect = message_surface.get_rect(midbottom=(self.rect.centerx, self.text_y - 20))
            
            # Ajustar la posición vertical para evitar la superposición con el nombre
            if message_rect.bottom > text_rect.top:  
                message_rect.bottom = text_rect.top - 5
            
            # Manejar la colisión de diálogos entre personajes
            for other_character in characters:
                if other_character != self and message_rect.colliderect(other_character.dialog_rect):
                    message_rect.top = other_character.dialog_rect.top - message_rect.height - 10

            pygame.draw.rect(screen, BLACK, (message_rect.left - 6, message_rect.top - 6, message_rect.width + 12, message_rect.height + 12))
            pygame.draw.rect(screen, WHITE, (message_rect.left - 5, message_rect.top - 5, message_rect.width + 10, message_rect.height + 10))

            draw_text_with_outline(screen, self.message, font_message, BLACK, WHITE, (message_rect.x, message_rect.y))
            
            # Actualizar el rectángulo del diálogo para la detección de colisiones
            self.dialog_rect = message_rect

    def execute_command(self, command):
        #command = command.lower()
        if command.startswith("!gif "):
            if "random" in command:
                gif_files = [f for f in os.listdir("sprites_objetos") if f.endswith(".gif")]
                if gif_files:
                    random_gif_name = random.choice(gif_files)
                    self.show_gif(random_gif_name)
            else:
                gif_name = command.split(" ")[1] + ".gif"
                self.show_gif(gif_name)
        elif command.startswith("!mover "):
            direction_or_target = command.split(" ")[1]
            if direction_or_target == "izquierda":
                self.move_left_for_duration()
            elif direction_or_target == "derecha":
                self.move_right_for_duration()
            elif direction_or_target == "parado":
                self.stop_for_duration()
            else:
                self.target_name=direction_or_target
                self.move_towards()
        elif command.startswith("!skin"):
            if "random" in command:
                self.change_to_random_skin()
            elif len(command.split(" ")) > 1:
                skin_name = command.split(" ")[1]
                self.change_to_skin("sprite_" + skin_name + ".png")
        elif command == "!help":
            self.message = "!help"

    def show_gif(self, gif_name):
        gif_path = os.path.join("sprites_objetos", gif_name)
        gif_images = []
        try:
            gif = Image.open(gif_path)
            for frame in ImageSequence.Iterator(gif):
                # Convertir el fotograma al modo RGB
                frame = frame.convert("RGBA")
                frame_surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                gif_images.append(frame_surface)
        except Exception as e:
            return
        self.extra_images = gif_images
        self.gif_start_time = pygame.time.get_ticks()  # Registrar el tiempo de inicio del GIF


    def move_left_for_duration(self):
        self.state = STATE_LEFT
        self.next_state_time = time.time() + 10

    def move_right_for_duration(self):
        self.state = STATE_RIGHT
        self.next_state_time = time.time() + 10

    def move_towards(self):
        self.state = STATE_FOLLOW
        self.next_state_time = time.time() + 20

    def stop_for_duration(self):
        self.state = STATE_STOP
        self.next_state_time = time.time() + 10

    def change_to_random_skin(self):
        random_skin_path = random.choice(sprite_images)
        if random_skin_path!=self.old_skin:
            self.image = pygame.image.load(random_skin_path).convert_alpha()
            self.image = self.resize_image(self.image, 64)
            oldx=self.rect.x
            self.rect = self.image.get_rect()
            self.rect.x = oldx
            self.rect.bottom = self.base_y
            self.old_skin=random_skin_path

    def change_to_skin(self, skin_name):
        skin_path = os.path.join("sprites", skin_name)
        if os.path.exists(skin_path) and skin_path!=self.old_skin:
            self.image = pygame.image.load(skin_path).convert_alpha()
            self.image = self.resize_image(self.image, 64)
            oldx=self.rect.x
            self.rect = self.image.get_rect()
            self.rect.x = oldx
            self.rect.bottom = self.base_y
            self.old_skin=skin_path

    def change_skin(self, skin_path):
        skin_image = pygame.image.load(skin_path).convert_alpha()
        self.image = self.resize_image(skin_image, 64)

# Función para leer el historial de chat desde un archivo de texto
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='cp1252') as file:
        chat_lines = file.readlines()
    return chat_lines

# Función para procesar las líneas del historial de chat
def process_chat_lines(chat_lines):
    chat_data = []
    for line in chat_lines:
        parts = line.strip().split(': ')
        if len(parts) == 2:
            username, message = parts
            chat_data.append((username, message))
    return chat_data

# Función para actualizar el historial de chat cada cierto tiempo
def update_chat_data():
    global chat_data
    while True:
        chat_lines = read_chat_history("historial.txt")
        chat_data = process_chat_lines(chat_lines)
        time.sleep(2)  # Esperar 2 segundos antes de volver a leer el historial

# Crear un grupo de sprites para los personajes
characters = pygame.sprite.Group()

# Leer el historial de chat y procesarlo
chat_data = []
chat_thread = threading.Thread(target=update_chat_data)
chat_thread.daemon = True
chat_thread.start()

# Diccionario para mantener una referencia de NPC por nombre
npc_dict = {}

# Bucle principal
running = True
clock = pygame.time.Clock()

last_processed_index = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Leer el historial de chat y procesarlo
    chat_lines = read_chat_history("historial.txt")
    chat_data = process_chat_lines(chat_lines)

    # Procesar solo los nuevos mensajes
    new_messages = chat_data[last_processed_index:]
    last_processed_index += len(new_messages)

    # Actualizar los mensajes de los personajes y ejecutar comandos
    for username, message in new_messages:
        if len(npc_dict) > 50:
            oldest_npc = min(characters, key=lambda npc: npc.creation_time)
            characters.remove(oldest_npc)
            del npc_dict[oldest_npc.name]

        if username not in npc_dict:
            character = Character(username, sprite_images[0], random.randint(50, SCREEN_WIDTH - 50), SCREEN_HEIGHT // 2)
            characters.add(character)
            npc_dict[username] = character

        if message.startswith("!"):
            npc_dict[username].execute_command(message)
            if message != "!help":
                npc_dict[username].message = ""
        else:
            npc_dict[username].message = message
            npc_dict[username].message_start_time = time.time()

    # Actualizar la posición de los personajes
    characters.update()

    # Dibujar todo
    screen.fill(GREEN)
    for character in characters:
        character.draw(screen)

    # Actualizar la pantalla
    pygame.display.flip()

    # Configurar la velocidad de fotogramas
    clock.tick(30)

pygame.quit()
