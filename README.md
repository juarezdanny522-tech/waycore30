# WayCore + WayHat v0.6.0 — IA local en el teléfono + control total de WayHat

WayCore es la app Android de Karbys: un asistente de voz pensado para personas con
discapacidad visual que controla el dispositivo WayHat (ESP32) por Bluetooth.

## Lo nuevo en esta versión

- **IA local en el teléfono** con MediaPipe LLM Inference (modelo Gemma 3 1B, int4):
  - Karbys piensa y responde **sin Internet**, mucho más rápido que llamando a la nube.
  - **Conserva el mismo poder de control que tiene con Gemini**: la IA local puede
    ajustar la sensibilidad (20–150 cm), cambiar el modo SAFE/CHAT, activar o
    desactivar los avisos sonoros, probar el buzzer y pedir lecturas nuevas de
    sensores. Todo pasa por la misma lista blanca y la confirmación del ESP32.
  - Recibe el mismo contexto real en cada consulta: telemetría de WayHat,
    batería, ubicación y hora. Si un dato no existe, lo dice sin inventarlo.
- **Selector de motor de IA** en la pantalla principal:
  1. Primero IA local (recomendado)
  2. Solo IA local, sin Internet
  3. Primero Gemini, IA local de respaldo
  4. Solo Gemini
- **Gestor del modelo dentro de la app**: descarga por URL (con token de
  Hugging Face opcional), importar archivo ya descargado, progreso de descarga
  y borrado del modelo.
- **Compilación automática del APK en GitHub Actions**: cada `push` genera el APK
  instalable como artefacto, y cada tag `v*` crea un Release con el APK adjunto.

## Cómo instalar el modelo de IA local (una sola vez)

El modelo nunca se incluye en el APK porque pesa ~560 MB. Se instala en el
teléfono desde la propia app, pantalla principal, sección **MODELO DE IA LOCAL**:

**Opción A — descarga directa en la app (recomendada)**
1. Crea una cuenta en [huggingface.co](https://huggingface.co) y acepta la
   licencia de Gemma en [litert-community/Gemma3-1B-IT](https://huggingface.co/litert-community/Gemma3-1B-IT).
2. En tu perfil de Hugging Face: **Settings → Access Tokens → Create new token**
   (basta uno de solo lectura, "Read").
3. En WayCore pega el token y toca **DESCARGAR MODELO** (la URL ya viene lista:
   `gemma3-1b-it-int4.task`). Se guarda solo; con Wi-Fi tarda unos minutos.

**Opción B — archivo ya descargado**
1. Desde el navegador del teléfono o una computadora, descarga
   `gemma3-1b-it-int4.task` del mismo repositorio.
2. En WayCore toca **ELEGIR ARCHIVO** y selecciónalo; la app lo copia sola.

También sirven otros modelos compatibles con MediaPipe (`gemma-2-2b-it-int4.task`,
`gemma-2b-it-int4.task`, etc.); se eligen igual, cambiando la URL o el archivo.

Cuando el modelo está instalado aparece "Modelo instalado (XXX MB)". La primera
pregunta tarda unos segundos más mientras el modelo se carga en memoria; Karbys
te avisa con voz que lo está encendiendo.

## Compilar el APK desde GitHub (sin instalar nada)

El repositorio incluye `.github/workflows/android.yml`:

- **Cada push** compila el APK. Se descarga en la pestaña **Actions** → ejecución →
  artefacto `waycore-apk` (archivo `WayCore-v0.6.0.apk`, firmado con la clave de
  depuración: listo para instalar en tu teléfono).
- **Releases**: crea un tag y súbelo para publicar el APK en la sección Releases:
  ```bash
  git tag v0.6.0 && git push origin v0.6.0
  ```
- **Clave de Gemini opcional**: para compilar el APK ya con la clave, guarda
  `GEMINI_API_KEY` en **Settings → Secrets and variables → Actions → New
  repository secret**. Sin el secreto el APK compila igual y Karbys funciona con
  la IA local y sus comandos básicos; en local puedes seguir usando
  `local.properties` como antes.

## Qué puede controlar la IA (local y Gemini)

- Sensibilidad de WayHat (20–150 cm de zona de aviso).
- Modo SAFE (avisos de proximidad) o CHAT (silenciados, telemetría activa).
- Avisos sonoros de proximidad (buzzer de seguridad).
- Pitido de prueba del buzzer, solo si el usuario lo pide.
- Lectura inmediata de sensores antes de responder.

La IA **no** puede enviar comandos arbitrarios al ESP32: todo pasa por la lista
blanca de `WayHatService.executeTool` y cada comando necesita la confirmación
(ack) del WayHat. Los comandos críticos (hora, batería, ubicación, recordatorios,
modo, sensibilidad, buzzer) además tienen atajos locales instantáneos que no
usan IA.

## Telemetría y seguridad (sin cambios)

- Karbys recibe contexto fresco en cada consulta: HC-SR04 derecho/izquierdo/
  trasero, TF-Luna, distancia más cercana, DHT11, sensibilidad, modo, avisos,
  conexión de WayHat, batería del teléfono, GPS y hora.
- WayHat mantiene su seguridad local aunque no haya IA ni Internet.
- El enlace Bluetooth SPP sigue siendo independiente de voz y TTS.

## Notas sobre la IA local

- Requiere un teléfono con **4 GB de RAM libres aprox.** y Android 8 o superior.
  En gama media funciona mejor con el modo "Primero IA local" y respuestas cortas.
- Si algo falla con el modelo (archivo dañado, poca memoria), Karbys cae
  automáticamente al respaldo configurado y lo explica con voz.
- El audio, la palabra de activación "oye Karbys" y los controles directos del
  WayHat siguen funcionando igual, con o sin modelo.
