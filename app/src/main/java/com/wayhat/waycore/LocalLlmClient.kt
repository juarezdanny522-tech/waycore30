package com.wayhat.waycore

import android.content.Context
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runInterruptible
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withTimeout
import org.json.JSONObject

/** Error de la IA local que KarbysRouter puede convertir en mensaje para el usuario. */
class LocalModelException(message: String) : Exception(message)

private data class ToolCall(val name: String, val args: JSONObject)

/**
 * Karbys pensando 100% en el teléfono (sin Internet), usando MediaPipe LLM
 * Inference con un modelo Gemma en formato .task.
 *
 * Mantiene el MISMO poder de control que tiene Gemini: el modelo produce una
 * línea TOOL:{...} con la acción de WayHat, aquí se ejecuta contra la lista
 * blanca de WayHatService y luego el modelo confirma el resultado hablado.
 */
object LocalLlmClient {
    private const val MAX_TOKENS = 1408          // prompt + respuesta por turno
    private const val TOP_K = 32
    private const val TEMPERATURE = 0.3f         // baja para que TOOL salga exacto
    private const val INFER_TIMEOUT_MS = 170_000L

    @Volatile private var engine: LlmInference? = null
    @Volatile private var loadedSig: String? = null
    private val mutex = Mutex()

    fun modelInstalled(context: Context): Boolean = ModelManager.isModelReady(context)
    fun willNeedLoad(context: Context): Boolean = modelInstalled(context) && engine == null

    /** Llámalo cuando el modelo se borra o se reemplaza. */
    fun invalidate() {
        try { engine?.close() } catch (_: Throwable) {}
        engine = null
        loadedSig = null
    }

    private fun sigOf(context: Context): String {
        val f = ModelManager.modelFile(context)
        return "${f.absolutePath}:${f.length()}:${f.lastModified()}"
    }

    private suspend fun ensureLoaded(context: Context): LlmInference {
        if (!ModelManager.isModelReady(context)) {
            throw LocalModelException("no_model")
        }
        val sig = sigOf(context)
        val current = engine
        if (current != null && loadedSig == sig) return current

        return runInterruptible(Dispatchers.IO) {
            invalidate()
            val file = ModelManager.modelFile(context)
            val created = try {
                val opts = LlmInference.LlmInferenceOptions.builder()
                    .setModelPath(file.absolutePath)
                    .setMaxTokens(MAX_TOKENS)
                    .setMaxTopK(TOP_K)
                    .build()
                LlmInference.createFromOptions(context.applicationContext, opts)
            } catch (t: Throwable) {
                throw LocalModelException("No pude iniciar el modelo local. Instálalo de nuevo desde la pantalla principal.")
            }
            engine = created
            loadedSig = sig
            created
        }
    }

    suspend fun ask(context: Context, user: String, memory: List<ConversationTurn>, deviceContext: String): String =
        mutex.withLock {
            val llm = ensureLoaded(context)
            try {
                withTimeout(INFER_TIMEOUT_MS) { askInternal(llm, user, memory, deviceContext) }
            } catch (e: LocalModelException) {
                throw e
            } catch (_: Throwable) {
                throw LocalModelException("Mi IA local tardó demasiado o falló al responder.")
            }
        }

    private suspend fun askInternal(llm: LlmInference, user: String, memory: List<ConversationTurn>, deviceContext: String): String {
        // Primer intento con historial; si el prompt no cabe, reintenta sin historial.
        var raw = generate(llm, buildPrompt(user, memory, deviceContext, includeHistory = true))
        if (raw == null) raw = generate(llm, buildPrompt(user, emptyList(), deviceContext, includeHistory = false))
        if (raw == null) throw LocalModelException("Mi IA local no pudo responder.")

        val call = parseTool(raw)
        if (call == null) {
            val spoken = cleanSpeech(raw)
            if (spoken.isBlank()) throw LocalModelException("Mi IA local no dio una respuesta clara.")
            return spoken
        }

        // Control de WayHat: pasa por la misma lista blanca y confirmación del ESP32 que usa Gemini.
        val result = WayHatService.executeTool(call.name, call.args)

        var spoken2 = generate(llm, buildToolFollowup(user, call, result))?.let { cleanSpeech(it) }.orEmpty()
        if (spoken2.isBlank()) spoken2 = friendlyToolFallback(call.name, result)
        return spoken2
    }

    private suspend fun generate(llm: LlmInference, prompt: String): String? {
        return try {
            runInterruptible(Dispatchers.Default) {
                try {
                    // API de sesión: permite fijar topK y temperatura.
                    val sessionOptions = LlmInferenceSession.LlmInferenceSessionOptions.builder()
                        .setTopK(TOP_K)
                        .setTemperature(TEMPERATURE)
                        .build()
                    val session = LlmInferenceSession.createFromOptions(llm, sessionOptions)
                    try {
                        session.addQueryChunk(prompt)
                        session.generateResponse()
                    } finally {
                        try { session.close() } catch (_: Throwable) {}
                    }
                } catch (_: Throwable) {
                    // API simple de respaldo.
                    llm.generateResponse(prompt)
                }
            }
        } catch (_: Throwable) {
            null
        }
    }

    /**
     * Busca la línea TOOL: y extrae el JSON aunque venga partido en varias
     * líneas o con texto extra después.
     */
    private fun parseTool(raw: String): ToolCall? {
        val marker = Regex("TOOL\\s*:", RegexOption.IGNORE_CASE).find(raw) ?: return null
        val jsonStart = raw.indexOf('{', marker.range.last + 1)
        if (jsonStart < 0) return null

        var depth = 0
        var end = -1
        for (i in jsonStart until raw.length) {
            when (raw[i]) {
                '{' -> depth++
                '}' -> {
                    depth--
                    if (depth == 0) { end = i; break }
                }
            }
        }
        if (end < 0) return null

        val obj = runCatching { JSONObject(raw.substring(jsonStart, end + 1)) }.getOrNull() ?: return null
        val name = obj.optString("name").trim()
        if (name.isBlank()) return null
        return ToolCall(name, obj.optJSONObject("args") ?: JSONObject())
    }

    /** Quita restos de plantilla y deja solo lo hablable. */
    private fun cleanSpeech(raw: String): String {
        var t = raw.substringBefore("<end_of_turn>")
        t = t.lineSequence()
            .map { it.trim() }
            .filter { line ->
                line.isNotBlank() &&
                    !line.startsWith("<start_of_turn>", ignoreCase = true) &&
                    !line.startsWith("<end_of_turn>", ignoreCase = true) &&
                    !Regex("^TOOL\\s*:", RegexOption.IGNORE_CASE).containsMatchIn(line) &&
                    !line.equals("model", ignoreCase = true)
            }
            .joinToString(" ")
        t = t.replace(Regex("\\s+"), " ").trim()
        if (t.length > 420) {
            val cut = t.take(420)
            t = cut.substringBeforeLast('.').takeIf { it.length > 120 } ?: cut
        }
        return t.trim()
    }

    private fun wrap(body: String): String =
        "<start_of_turn>user\n$body<end_of_turn>\n<start_of_turn>model\n"

    private fun buildPrompt(user: String, memory: List<ConversationTurn>, deviceContext: String, includeHistory: Boolean): String {
        val history = if (!includeHistory || memory.isEmpty()) "" else {
            "\nCONVERSACIÓN RECIENTE:\n" + memory.takeLast(2).joinToString("\n") {
                "Usuario: ${it.user}\nKarbys: ${it.assistant}"
            }
        }
        return wrap(
            """Eres Karbys, el asistente de voz de WayCore creado por WayCorp, pensado para personas con discapacidad visual. Respondes en español latino, breve (maximo 50 palabras), claro y amable, para ser escuchado en voz alta. Nunca uses emojis, listas ni simbolos.
Los datos de ESTADO ACTUAL son lecturas reales del telefono y del dispositivo WayHat: son la verdad. Nunca inventes valores; -1, null o unavailable significan dato no disponible, dilo con honestidad.
Para controlar WayHat NO respondas con texto: escribe una sola linea que empiece con TOOL: y un JSON, por ejemplo TOOL:{"name":"set_wayhat_mode","args":{"mode":"CHAT"}}. Herramientas disponibles:
set_wayhat_sensitivity args={"centimeters":numero entre 20 y 150} ajusta a que distancia del obstaculo avisa.
set_wayhat_mode args={"mode":"SAFE" o "CHAT"} SAFE mantiene los avisos de proximidad, CHAT los silencia.
set_wayhat_alerts args={"enabled":true o false} enciende o apaga los avisos sonoros.
test_wayhat_alert args={} emite un pitido de prueba.
refresh_wayhat_telemetry args={} pide una lectura nueva de los sensores.
Usa una herramienta SOLO si el usuario la pide o es claramente necesaria para cumplir su peticion. Nunca desactives seguridad sin que te lo pidan. Si no necesitas herramienta, responde normal SIN escribir TOOL. Nunca digas que hiciste una accion si no usaste la herramienta.

ESTADO ACTUAL:
$deviceContext
$history

USUARIO: $user
KARBYS:"""
        )
    }

    private fun buildToolFollowup(user: String, call: ToolCall, toolResult: String): String = wrap(
        """Eres Karbys, el asistente de voz de WayCore. Hablas español latino, breve (maximo 40 palabras), claro, para escuchar en voz alta, sin emojis ni listas.
El usuario pidio: "$user"
Ejecutaste la accion ${call.name} con parametros ${call.args} y WayHat respondio exactamente: "$toolResult".
Dile al usuario que hiciste y confirma el resultado real recibido. Si fue un error, explicalo con honestidad y calma. No escribas TOOL ni JSON.
KARBYS:"""
    )

    private fun friendlyToolFallback(name: String, result: String): String {
        if (result.startsWith("No ejecutado") || result.startsWith("No pude confirmar") || result.startsWith("WayHat no está")) return result
        return when (name) {
            "set_wayhat_sensitivity" -> "Actualicé la sensibilidad de WayHat."
            "set_wayhat_mode" -> "Cambié el modo de WayHat."
            "set_wayhat_alerts" -> "Actualicé los avisos sonoros de WayHat."
            "test_wayhat_alert" -> "Envié la prueba de sonido a WayHat."
            "refresh_wayhat_telemetry" -> "Pedí una lectura nueva de los sensores de WayHat."
            else -> "Listo."
        }
    }
}
