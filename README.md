# Práctica 3: Calculadora Basada en Gestos
**Asignatura:** Sistemas Interactivos Inteligentes  
**Unidad IV:** Interacción Natural y Visión por Computador  

---

## 1. Descripción del Proyecto

Aplicación interactiva de calculadora controlada en tiempo real mediante visión artificial y reconocimiento gestual de manos a través de la webcam.

El sistema procesa la entrada de vídeo mediante **MediaPipe Hands** y **OpenCV**, permitiendo al usuario interactuar con una interfaz virtual para realizar operaciones aritméticas básicas, borrado, reset y visualización de resultados.

---

## 2. Requisitos y Entorno de Ejecución

### 2.1 En Windows y macOS (con `uv`)

1. **Crear el entorno virtual** (requiere Python 3.12 fijado en `.python-version`):
   ```bash
   uv venv
   ```

2. **Instalar dependencias**:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Comprobar la cámara**:
   ```bash
   uv run python src/gest-calc/webcam_test.py
   ```

4. **Ejecutar la calculadora**:
   ```bash
   uv run python src/gest-calc/main.py
   ```
   *(O alternativamente: `uv run python src/gest-calc/sample_main.py`)*

   Si se dispone de múltiples cámaras, puede especificarse el índice:
   ```bash
   uv run python src/gest-calc/main.py --cam 1
   ```

   > **Nota de ejecución:** En mi caso particular, debido a problemas/fallos al intentar lanzarlo mediante `uv run`, ejecuté la aplicación directamente con Python en el sistema sin necesidad de activar el entorno virtual:
   > ```bash
   > python src/gest-calc/main.py
   > ```

### 2.2 En Linux (con Docker)

1. **Construir la imagen**:
   ```bash
   make build
   ```

2. **Probar la cámara**:
   ```bash
   make camtest
   ```

3. **Ejecutar la calculadora**:
   ```bash
   make run
   ```

---

## 3. Arquitectura del Software

El código se organiza de forma modular y desacoplada en `src/gest-calc/`:

- `hand_detector.py`: Encapsula la detección de puntos de referencia con MediaPipe. Implementa suavizado de coordenadas (Exponential Moving Average) y cálculo de distancias normalizadas por escala anatómica de la palma.
- `calculator.py`: Lógica aritmética estricta y segura (manejo de operadores, prevención de entradas consecutivas inválidas, gestión de división por cero y formateo de resultados sin ejecución arbitraria).
- `gui.py`: Componentes visuales (`Button`, `CalculatorGUI`), gestión de layout adaptativo según resolución, efectos de transparencia alfa, estados interactivos (*normal, hover, pressed*) y barra de progreso.
- `sound_manager.py`: Feedback auditivo asíncrono y no bloqueante mediante hilos (*threads*), adaptado para Windows y con fallback transparente en Linux.
- `main.py`: Bucle principal de eventos, gestión de modos de interacción, temporizadores, captura de cámara y cálculo de FPS.

---

## 4. Diseño de la Interacción y Justificación Teórica

### 4.1 Mapeo Espacial Natural (Efecto Espejo)
La imagen capturada por la cámara se invierte horizontalmente (`cv2.flip(frame, 1)`). Esto alinea el movimiento propioceptivo del usuario con el movimiento visual en pantalla, reduciendo la carga cognitiva.

### 4.2 Apuntado y Suavizado
El cursor de interacción se fija en la punta del dedo índice (Landmark 8). Para mitigar el temblor involuntario (*jitter*) y mejorar la precisión según la Ley de Fitts, se aplica un filtro de suavizado exponencial:
$$X_{suavizado} = \alpha \cdot X_{actual} + (1 - \alpha) \cdot X_{previo}$$

### 4.3 Modos de Activación y Accesibilidad
El sistema incorpora dos modalidades intercambiables mediante la tecla `M`:

1. **Modo Pinza ("Pinch-to-Click")**:
   - Se calcula la distancia euclídea entre la punta del índice (Landmark 8) y la del pulgar (Landmark 4).
   - **Invarianza a la distancia:** La distancia se normaliza dividiéndola por la escala anatómica de la mano (distancia entre muñeca y nudillo medio). Esto asegura que el gesto funcione igual tanto cerca como lejos de la cámara.
   - **Histéresis y Antirrebote:** Se define un umbral de activación estricto ($d_{norm} < 0.28$) y un umbral de liberación más amplio ($d_{norm} > 0.40$), junto a un período de enfriamiento (*cooldown* de 350 ms). Esto evita pulsaciones dobles involuntarias.

2. **Modo Permanencia ("Dwell-Time")**:
   - Orientado a accesibilidad motriz para usuarios que no puedan realizar el gesto de pinza.
   - Al posicionar el cursor sobre una tecla durante 800 ms continuados, se confirma la pulsación.
   - Incluye feedback visual dinámico (barra de carga proporcional sobre el botón) para informar del progreso de activación.

### 4.4 Prevención de Falsos Positivos
- **Zona de pausa / descanso:** La interacción puede congelarse en cualquier momento con la tecla `Espacio` o al retirar la mano del encuadre, permitiendo gesticular o hablar con terceros sin accionar botones involuntariamente.
- **Filtro de confianza:** Se exigen umbrales de detección y seguimiento de 0.75 en MediaPipe para descartar falsas detecciones en fondos complejos.

### 4.5 Feedback Multimodal
- **Visual:** Cambio de color y contraste en estado *hover*, iluminación de acento en pulsación, borde de advertencia en caso de error y visualización clara de la operación activa junto al último resultado.
- **Auditivo:** Señales sonoras diferenciadas para pulsación estándar, borrado/reset y cálculo de resultado.

---

## 5. Controles Rápidos

| Tecla | Acción |
|---|---|
| `M` / `m` | Alternar entre modo Pinza y modo Permanencia (Dwell-Time) |
| `Espacio` | Pausar / Reactivar la interacción gestual |
| `C` / `c` | Activar / Desactivar feedback sonoro |
| `Q` / `ESC` | Cerrar la aplicación |

