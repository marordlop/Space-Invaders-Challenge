import os
import random
import sys

import pygame

from powerup import PowerUp

# ------------------------------------------------------------------
# Configuración
# ------------------------------------------------------------------
ANCHO, ALTO = 800, 600
FPS = 60
PANTALLA_RECT = pygame.Rect(0, 0, ANCHO, ALTO)

USAR_VIDAS = True            # True = reto 10 (vidas). False = retos 1-9 (un golpe y se acaba)
VIDAS_INICIALES = 3
INVULNERABLE_MS = 2000       # reto 10: 2 segundos tras un impacto

INTERVALO_INICIAL = 1000     # reto 7: ms entre obstáculos al empezar
INTERVALO_MINIMO = 150
REDUCCION_INTERVALO = 50     # cada 10 puntos

VEL_MIN, VEL_MAX = 2, 12     # reto 8
VEL_INICIAL = 5

POWERUP_CADA_MS = 8000       # reto 11
EFECTO_MS = 5000
BONUS_VELOCIDAD = 4

FICHERO_SCORES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.txt")

NEGRO = (20, 20, 30)
BLANCO = (240, 240, 240)
ROJO = (220, 60, 60)
AZUL = (70, 130, 255)
VERDE = (80, 200, 120)


# ------------------------------------------------------------------
# Clases
# ------------------------------------------------------------------
class Player:
    def __init__(self, x, y, color, teclas, velocidad):
        self.inicio = (x, y)
        self.color = color
        self.teclas = teclas  # (izquierda, derecha, arriba, abajo)
        self.velocidad_inicial = velocidad
        self.rect = pygame.Rect(x, y, 40, 40)
        self.reset()

    def reset(self):
        """Vuelve a la posición inicial y recupera vidas/velocidad."""
        self.rect.topleft = self.inicio
        self.velocidad_base = self.velocidad_inicial
        self.vidas = VIDAS_INICIALES
        self.invulnerable_hasta = 0
        self.turbo_hasta = 0

    @property
    def vivo(self):
        return self.vidas > 0

    def velocidad(self, tiempo):
        extra = BONUS_VELOCIDAD if tiempo < self.turbo_hasta else 0
        return self.velocidad_base + extra

    def mover(self, teclas_pulsadas, tiempo):
        izq, der, arr, abj = self.teclas
        v = self.velocidad(tiempo)
        if teclas_pulsadas[izq]:
            self.rect.x -= v
        if teclas_pulsadas[der]:
            self.rect.x += v
        if teclas_pulsadas[arr]:
            self.rect.y -= v
        if teclas_pulsadas[abj]:
            self.rect.y += v
        # Reto 1: no salir de la ventana por ningún lado
        self.rect.clamp_ip(PANTALLA_RECT)

    def draw(self, pantalla, tiempo):
        if not self.vivo:
            return
        invulnerable = tiempo < self.invulnerable_hasta
        # Parpadeo mientras es invulnerable
        if invulnerable and (tiempo // 100) % 2 == 0:
            return
        pygame.draw.rect(pantalla, self.color, self.rect)
        if invulnerable:
            pygame.draw.rect(pantalla, (255, 215, 0), self.rect, 3)


class Obstacle:
    def __init__(self):
        # Reto 2: tamaño aleatorio entre 20 y 70 y siempre dentro del ancho
        self.tam = random.randint(20, 70)
        x = random.randint(0, ANCHO - self.tam)
        self.rect = pygame.Rect(x, -self.tam, self.tam, self.tam)
        self.velocidad = random.randint(3, 6)

    def update(self):
        self.rect.y += self.velocidad

    def draw(self, pantalla):
        pygame.draw.rect(pantalla, ROJO, self.rect)


# ------------------------------------------------------------------
# Récords en fichero (reto 12)
# ------------------------------------------------------------------
def cargar_puntuaciones():
    puntuaciones = []
    if os.path.exists(FICHERO_SCORES):
        with open(FICHERO_SCORES, "r", encoding="utf-8") as f:
            for linea in f:
                try:
                    nombre, punt = linea.strip().rsplit(",", 1)
                    puntuaciones.append((nombre, int(punt)))
                except ValueError:
                    continue  # línea mal formada: se ignora
    puntuaciones.sort(key=lambda x: x[1], reverse=True)
    return puntuaciones


def guardar_puntuacion(nombre, puntuacion):
    with open(FICHERO_SCORES, "a", encoding="utf-8") as f:
        f.write(f"{nombre},{puntuacion}\n")


# ------------------------------------------------------------------
# Juego
# ------------------------------------------------------------------
class Juego:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Space Invaders Challenge")
        self.reloj = pygame.time.Clock()
        self.f_peq = pygame.font.SysFont(None, 26)
        self.f_med = pygame.font.SysFont(None, 40)
        self.f_gra = pygame.font.SysFont(None, 90)

        self.record = 0                      # reto 9: solo vive mientras corre el programa
        self.top5 = cargar_puntuaciones()[:5]
        self.estado = "menu"                 # menu | jugando | fin
        self.salir = False

        self.jugadores = [
            Player(200, ALTO - 60, AZUL, (pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s), VEL_INICIAL),
            Player(560, ALTO - 60, VERDE, (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN), VEL_INICIAL),
        ]
        self.nueva_partida()

    # ---------------- estado de la partida ----------------
    def nueva_partida(self):
        """Reto 5: deja todo como al principio (menos el récord)."""
        for p in self.jugadores:
            p.reset()
        self.obstaculos = []
        self.powerups = []
        self.puntuacion = 0
        self.tiempo = 0                      # ms de juego (no avanza en pausa ni en Game Over)
        self.ultimo_obstaculo = 0
        self.ultimo_powerup = 0
        self.pausa = False
        self.nombre = ""
        self.guardado = False

    def intervalo_aparicion(self):
        """Reto 7: -50 ms cada 10 puntos, nunca por debajo de 150 ms."""
        reduccion = (self.puntuacion // 10) * REDUCCION_INTERVALO
        return max(INTERVALO_MINIMO, INTERVALO_INICIAL - reduccion)

    def cambiar_velocidad(self, delta):
        """Reto 8: solo jugador 1, entre 2 y 12."""
        p1 = self.jugadores[0]
        p1.velocidad_base = max(VEL_MIN, min(VEL_MAX, p1.velocidad_base + delta))

    def terminar_partida(self):
        self.estado = "fin"
        self.record = max(self.record, self.puntuacion)

    # ---------------- eventos ----------------
    def manejar_evento(self, e):
        if e.type == pygame.QUIT:
            self.salir = True
            return
        if e.type != pygame.KEYDOWN:
            return

        if self.estado == "menu":
            self.estado = "jugando"

        elif self.estado == "jugando":
            if e.key == pygame.K_ESCAPE:                      # reto 4
                self.pausa = not self.pausa
            elif not self.pausa:
                # KEYDOWN salta una vez por pulsación -> cambia la velocidad una sola vez
                if e.key in (pygame.K_PLUS, pygame.K_KP_PLUS) or e.unicode == "+":
                    self.cambiar_velocidad(1)
                elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS) or e.unicode == "-":
                    self.cambiar_velocidad(-1)

        elif self.estado == "fin":
            if not self.guardado:
                self.escribir_nombre(e)
            elif e.key == pygame.K_r:                         # reto 5
                self.nueva_partida()
                self.estado = "jugando"

    def escribir_nombre(self, e):
        """Reto 12: entrada de texto hecha con eventos de Pygame."""
        if e.key == pygame.K_RETURN:
            nombre = self.nombre.strip() or "ANON"
            guardar_puntuacion(nombre, self.puntuacion)
            self.top5 = cargar_puntuaciones()[:5]
            self.guardado = True
        elif e.key == pygame.K_BACKSPACE:
            self.nombre = self.nombre[:-1]
        elif e.unicode and e.unicode.isprintable() and e.unicode != "," and len(self.nombre) < 12:
            self.nombre += e.unicode

    # ---------------- lógica ----------------
    def actualizar(self, dt):
        if self.estado != "jugando" or self.pausa:
            return  # reto 4 y 6: nada se mueve ni el tiempo avanza

        self.tiempo += dt                                     # reto 6
        teclas = pygame.key.get_pressed()
        for p in self.jugadores:
            if p.vivo:
                p.mover(teclas, self.tiempo)

        # Aparición de obstáculos
        if self.tiempo - self.ultimo_obstaculo >= self.intervalo_aparicion():
            self.obstaculos.append(Obstacle())
            self.ultimo_obstaculo = self.tiempo

        # Aparición de power-ups
        if self.tiempo - self.ultimo_powerup >= POWERUP_CADA_MS:
            self.powerups.append(PowerUp(ANCHO))
            self.ultimo_powerup = self.tiempo

        # Mover obstáculos y puntuar los que se esquivan
        for o in self.obstaculos[:]:
            o.update()
            if o.rect.top > ALTO:
                self.obstaculos.remove(o)
                self.puntuacion += 1
                self.record = max(self.record, self.puntuacion)   # reto 9

        # Colisiones (retos 3 y 10)
        for o in self.obstaculos[:]:
            for p in self.jugadores:
                if p.vivo and p.rect.colliderect(o.rect):
                    if not USAR_VIDAS:
                        self.terminar_partida()
                        return
                    if self.tiempo >= p.invulnerable_hasta:
                        p.vidas -= 1
                        p.invulnerable_hasta = self.tiempo + INVULNERABLE_MS
                        if o in self.obstaculos:
                            self.obstaculos.remove(o)
                        break

        if USAR_VIDAS and not any(p.vivo for p in self.jugadores):
            self.terminar_partida()
            return

        # Power-ups: mover, recoger, caducar
        for pu in self.powerups[:]:
            pu.update()
            if pu.fuera_de_pantalla(ALTO):
                self.powerups.remove(pu)
                continue
            for p in self.jugadores:
                if p.vivo and p.rect.colliderect(pu.rect):
                    self.aplicar_powerup(p, pu)
                    self.powerups.remove(pu)
                    break

    def aplicar_powerup(self, jugador, pu):
        if pu.tipo == "velocidad":
            jugador.turbo_hasta = self.tiempo + EFECTO_MS      # caduca solo al pasar ese instante
        elif pu.tipo == "vida":
            jugador.vidas = min(VIDAS_INICIALES, jugador.vidas + 1)
        elif pu.tipo == "escudo":
            jugador.invulnerable_hasta = max(jugador.invulnerable_hasta, self.tiempo + EFECTO_MS)

    # ---------------- dibujo ----------------
    def texto(self, txt, fuente, color, **pos):
        surf = fuente.render(txt, True, color)
        self.pantalla.blit(surf, surf.get_rect(**pos))

    def dibujar_top5(self, y_inicial):
        self.texto("TOP 5", self.f_med, ROJO, midtop=(ANCHO // 2, y_inicial))
        if not self.top5:
            self.texto("Todavía no hay puntuaciones", self.f_peq, BLANCO, midtop=(ANCHO // 2, y_inicial + 40))
        for i, (nombre, punt) in enumerate(self.top5):
            self.texto(f"{i + 1}. {nombre} - {punt}", self.f_peq, BLANCO, midtop=(ANCHO // 2, y_inicial + 40 + i * 26))
    
    def dibujar(self):
        self.pantalla.fill(NEGRO)

        if self.estado == "menu":
            self.texto("SPACE INVADERS CHALLENGE", self.f_med, BLANCO, center=(ANCHO // 2, 90))
            self.texto("J1 (izquierda): WASD  |  J2 (derecha): flechas  |  +/-: velocidad J1  |  ESC: pausa", self.f_peq, BLANCO, center=(ANCHO // 2, 140))
            self.dibujar_top5(200)
            self.texto("Pulsa cualquier tecla para empezar", self.f_med, VERDE, center=(ANCHO // 2, 500))
            pygame.display.flip()
            return

        for o in self.obstaculos:
            o.draw(self.pantalla)
        for pu in self.powerups:
            pu.draw(self.pantalla, self.f_peq)
        for p in self.jugadores:
            p.draw(self.pantalla, self.tiempo)

        # HUD
        p1, p2 = self.jugadores
        self.texto(f"Puntos: {self.puntuacion}", self.f_peq, BLANCO, topleft=(10, 10))
        self.texto(f"Récord: {self.record}", self.f_peq, BLANCO, topleft=(10, 34))
        self.texto(f"Tiempo: {self.tiempo / 1000:.1f} s", self.f_peq, BLANCO, topleft=(10, 58))
        self.texto(f"Vel J1: {p1.velocidad_base}", self.f_peq, BLANCO, topleft=(10, 82))
        if USAR_VIDAS:
            self.texto(f"J1 vidas: {p1.vidas}", self.f_peq, AZUL, topright=(ANCHO - 10, 10))
            self.texto(f"J2 vidas: {p2.vidas}", self.f_peq, VERDE, topright=(ANCHO - 10, 34))
        y = 58
        for nombre, p in (("J1", p1), ("J2", p2)):
            if self.tiempo < p.turbo_hasta:
                seg = (p.turbo_hasta - self.tiempo) / 1000
                self.texto(f"{nombre} turbo {seg:.1f}s", self.f_peq, (0, 200, 255), topright=(ANCHO - 10, y))
                y += 24

        if self.pausa:
            self.texto("PAUSE", self.f_gra, BLANCO, center=(ANCHO // 2, ALTO // 2))

        if self.estado == "fin":
            capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            capa.fill((0, 0, 0, 170))
            self.pantalla.blit(capa, (0, 0))
            self.texto("GAME OVER", self.f_gra, ROJO, center=(ANCHO // 2, 110))
            self.texto(f"Puntos: {self.puntuacion}   Récord: {self.record}   Tiempo: {self.tiempo / 1000:.1f} s",
                       self.f_peq, BLANCO, center=(ANCHO // 2, 170))
            if not self.guardado:
                self.texto("Escribe tu nombre y pulsa ENTER:", self.f_med, BLANCO, center=(ANCHO // 2, 240))
                caja = pygame.Rect(0, 0, 300, 44)
                caja.center = (ANCHO // 2, 295)
                pygame.draw.rect(self.pantalla, BLANCO, caja, 2)
                self.texto(self.nombre, self.f_med, BLANCO, center=caja.center)
            else:
                self.dibujar_top5(230)
                self.texto("Pulsa R para jugar otra vez", self.f_med, VERDE, center=(ANCHO // 2, 500))

        pygame.display.flip()

    # ---------------- bucle principal ----------------
    def run(self):
        while not self.salir:
            dt = self.reloj.tick(FPS)
            for e in pygame.event.get():
                self.manejar_evento(e)
            self.actualizar(dt)
            self.dibujar()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Juego().run()
