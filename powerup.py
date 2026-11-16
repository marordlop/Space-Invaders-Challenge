"""Reto 11: clase PowerUp en un archivo independiente."""
import random
import pygame

# tipo -> (color, letra que se dibuja dentro)
TIPOS = {
    "velocidad": ((0, 200, 255), "V"),   # más velocidad durante unos segundos
    "vida": ((255, 80, 120), "+"),       # recupera una vida
    "escudo": ((255, 215, 0), "E"),      # invulnerable durante unos segundos
}


class PowerUp:
    def __init__(self, ancho_ventana, tipo=None):
        self.tipo = tipo or random.choice(list(TIPOS))
        self.color, self.letra = TIPOS[self.tipo]
        tam = 30
        x = random.randint(0, ancho_ventana - tam)
        self.rect = pygame.Rect(x, -tam, tam, tam)
        self.velocidad = 3

    def update(self):
        self.rect.y += self.velocidad

    def fuera_de_pantalla(self, alto_ventana):
        return self.rect.top > alto_ventana

    def draw(self, pantalla, fuente):
        pygame.draw.ellipse(pantalla, self.color, self.rect)
        pygame.draw.ellipse(pantalla, (255, 255, 255), self.rect, 2)
        texto = fuente.render(self.letra, True, (0, 0, 0))
        pantalla.blit(texto, texto.get_rect(center=self.rect.center))
