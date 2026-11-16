

https://github.com/user-attachments/assets/f2e34656-bf61-4bb1-8e73-5819458abbd0

# Esquiva los obstáculos (Pygame)

Juego de dos jugadores en el que hay que esquivar obstáculos que caen.

- **Jugador 1 (izquierda, azul):** teclas W A S D
- **Jugador 2 (derecha, verde):** flechas del teclado
- **ESC:** pausa · **+ / -:** velocidad del jugador 1 · **R:** reiniciar tras el Game Over

## Archivos

| Archivo | Contenido |
|---|---|
| `main.py` | Juego completo: clases `Player`, `Obstacle` y `Juego` (bucle principal) |
| `powerup.py` | Clase `PowerUp` (reto 11), en un archivo independiente |
| `scores.txt` | Se crea solo al guardar la primera puntuación (reto 12) |

Ejecutar: `pip install pygame` y después `python main.py`.

## Idea general del código

- `Juego.run()` repite en cada fotograma: leer eventos → `actualizar(dt)` → `dibujar()`.
- El juego tiene un **estado**: `menu`, `jugando` o `fin`.
- Todos los temporizadores (aparición de obstáculos, invulnerabilidad, power-ups, cronómetro) usan `self.tiempo`, un contador en milisegundos que **solo avanza mientras se juega y no hay pausa**. Gracias a eso la pausa y el Game Over congelan todo automáticamente, sin código extra en cada reto.
- La constante `USAR_VIDAS` permite elegir: `False` = comportamiento de los retos 1-9 (un golpe y se acaba), `True` = reto 10 (vidas).

---

## Parte 1 — Retos obligatorios

### 1. Límites de pantalla
En `Player.mover()`, tras modificar `self.rect.x` / `self.rect.y`, se llama a `self.rect.clamp_ip(PANTALLA_RECT)`. `clamp_ip` mueve el rectángulo para que quede dentro de otro (la ventana), así ningún jugador puede salir por arriba, abajo, izquierda o derecha. Se aplica a los dos jugadores porque ambos usan la misma clase.

### 2. Tamaños aleatorios
En `Obstacle.__init__` se genera `self.tam = random.randint(20, 70)` y la posición horizontal con `random.randint(0, ANCHO - self.tam)`. Al restar el tamaño, el obstáculo siempre cabe completo dentro del ancho. Nace justo encima de la pantalla (`y = -tam`).

### 3. Colisión del segundo jugador
En `actualizar()`, para cada obstáculo se recorre la lista `self.jugadores` (jugador 1 y jugador 2) y se comprueba `p.rect.colliderect(o.rect)`. Con `USAR_VIDAS = False`, el choque de cualquiera de los dos llama a `terminar_partida()`.

### 4. Pausa
En `manejar_evento()`, al pulsar ESC se invierte `self.pausa`. En `actualizar()`, si `self.pausa` es `True` se hace `return` al principio: no se mueven jugadores ni obstáculos, no aparecen nuevos y el tiempo no avanza. En `dibujar()` se muestra el texto **PAUSE** encima.

### 5. Reiniciar partida
Al llegar al Game Over, pulsar R llama a `nueva_partida()`, que pone la puntuación y el tiempo a cero, vacía la lista de obstáculos y de power-ups, y llama a `Player.reset()` para devolver a los jugadores a su posición inicial. El récord no se toca porque vive fuera de `nueva_partida()`.

### 6. Tiempo de supervivencia
`self.tiempo` suma los milisegundos de cada fotograma (`dt = reloj.tick(FPS)`) **solo** cuando el estado es `jugando` y no hay pausa. Se muestra como `tiempo / 1000` segundos. Al ser Game Over o pausa, `actualizar()` no lo suma, así que se queda parado. (Es equivalente a usar `pygame.time.get_ticks()` restando las pausas, pero más sencillo.)

### 7. Dificultad progresiva
`intervalo_aparicion()` calcula `1000 - 50 * (puntuacion // 10)` y lo limita con `max(150, ...)`. Cada 10 puntos el intervalo baja 50 ms y nunca baja de 150 ms. Un obstáculo nuevo aparece cuando `self.tiempo - self.ultimo_obstaculo` alcanza ese intervalo.

### 8. Cambiar velocidad
Se usa el evento `KEYDOWN` (se dispara **una vez por pulsación**, no mientras se mantiene la tecla). `+` suma 1 y `-` resta 1 a `velocidad_base` del jugador 1, limitada con `max(2, min(12, ...))`. Se aceptan `K_PLUS`, `K_KP_PLUS` y el carácter `"+"` (por si el teclado lo genera con otra combinación); igual con `-`.

### 9. Récord de puntuación
`self.record` se inicializa a 0 al abrir el programa y se actualiza con `max(self.record, self.puntuacion)` cada vez que sube la puntuación. Se muestra junto a la puntuación actual. `nueva_partida()` no lo reinicia, así que se conserva entre partidas (pero no entre ejecuciones; para eso está el reto 12).

---

## Parte 2 — Retos opcionales

### 10. Sistema de vidas
Cada `Player` tiene `vidas = 3` y `invulnerable_hasta`. Al colisionar con un obstáculo:
- Si `self.tiempo >= p.invulnerable_hasta`, pierde una vida, se elimina el obstáculo y se fija `invulnerable_hasta = tiempo + 2000` (2 segundos).
- Si aún es invulnerable, el obstáculo lo atraviesa sin hacer daño.

Un jugador sin vidas deja de dibujarse, moverse y recibir golpes. La partida termina cuando **ninguno** de los dos tiene vidas. Durante la invulnerabilidad el jugador parpadea y tiene borde dorado.

### 11. Power-ups
`PowerUp` está en `powerup.py`. Cada 8 segundos de juego aparece uno de tipo aleatorio, que cae desde arriba. Si un jugador lo toca se llama a `aplicar_powerup()`:
- **Velocidad (V, azul):** `turbo_hasta = tiempo + 5000`; mientras `tiempo < turbo_hasta`, `Player.velocidad()` suma +4.
- **Vida (+, rosa):** suma una vida (máximo 3).
- **Escudo (E, dorado):** invulnerable 5 segundos, reutilizando `invulnerable_hasta`.

Los efectos temporales caducan solos: no hay que "quitarlos", simplemente la comparación con `self.tiempo` deja de cumplirse.

### 12. Guardar récords en fichero
- `guardar_puntuacion()` añade una línea `nombre,puntuacion` a `scores.txt`.
- `cargar_puntuaciones()` lee el fichero, ignora líneas mal formadas, ordena de mayor a menor y devuelve la lista; se usan las 5 primeras (`[:5]`).
- Al arrancar, la pantalla de inicio muestra el **TOP 5**.
- Al terminar una partida se pide el nombre con una entrada de texto hecha con eventos de Pygame (`e.unicode` para escribir, `BACKSPACE` para borrar, `ENTER` para guardar, máximo 12 caracteres). Tras guardar, se muestra el TOP 5 actualizado y se puede pulsar R para reiniciar.
