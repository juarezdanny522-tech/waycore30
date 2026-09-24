# WayCore + WayHat v0.6.0 — Telemetría real y control por Gemini

Esta versión usa la versión Bluetooth SPP estable anterior como base.

## Novedades de la app v0.6.0

- **"¿Dime?" en lugar del pitido**: cuando Karbys te va a escuchar (por palabra
  clave, por el botón HABLAR o después de responderte), lo anuncia con su voz
  diciendo "¿Dime?" en vez del antiguo sonidito.
- **Palabra clave más confiable**: ahora acepta variantes de pronunciación
  ("Oye Karbys", "Hey Karbis", "Her karbys", e incluso solo "Karbys"), usa
  coincidencia difusa para errores del reconocedor y se reinicia sola si el
  reconocedor se queda colgado.
- **Comando en una sola frase**: puedes decir "Oye Karbys, ¿qué hora es?" y
  Karbys atiende la pregunta de inmediato.
- **Pausa por voz corregida**: "Pausa Karbys" ahora pausa de verdad, y decir
  "Oye Karbys" la reactiva.

## Descargar el APK

El APK se compila automáticamente con GitHub Actions en cada cambio y se
publica en [Releases](https://github.com/juarezdanny522-tech/waycore30/releases).
Descarga el archivo `WayCore-vX.Y.Z.apk` en tu teléfono Android e instálalo.

## Nuevas funciones

- Karbys recibe en cada consulta un contexto fresco con:
  - HC-SR04 derecho, izquierdo y trasero.
  - TF-Luna.
  - Distancia más cercana.
  - Temperatura y humedad DHT11.
  - Estado de cada sensor.
  - Sensibilidad actual.
  - Modo SAFE/CHAT.
  - Estado de avisos sonoros.
  - Estado de conexión de WayHat.
  - Batería del teléfono.
  - Ubicación y antigüedad de la lectura GPS.
  - Hora local.
- Los datos de sensores son tratados como fuente de verdad: Karbys no debe inventar valores.
- Gemini puede usar Function Calling para controlar, de forma limitada y validada:
  - sensibilidad de WayHat (20–150 cm),
  - modo SAFE/CHAT,
  - avisos sonoros,
  - prueba del buzzer,
  - actualización inmediata de telemetría.
- Todos los comandos de hardware tienen una lista blanca y confirmación desde el ESP32.
- El enlace Bluetooth continúa siendo independiente de reconocimiento de voz y TTS.
- WayHat mantiene su seguridad local aunque Gemini o Internet no estén disponibles.

## API key

No hay ninguna clave API incluida. Configúrala en `local.properties`:

`GEMINI_API_KEY=TU_CLAVE`

## Bluetooth

El teléfono debe tener `WayHat-Karbys` vinculado. WayCore abre la conexión SPP automáticamente usando el UUID estándar de Bluetooth Classic.
