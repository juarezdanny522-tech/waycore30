package com.wayhat.waycore

import android.content.Context
import android.content.Intent
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/**
 * Gestiona el archivo del modelo de IA local (Gemma en formato .task/.bin/.litertlm)
 * que Karbys ejecuta directamente en el teléfono con MediaPipe.
 *
 * El modelo NO va dentro del APK (pesa cientos de MB): se descarga o se importa
 * una vez y queda guardado en el almacenamiento interno de la app.
 */
object ModelManager {
    const val ACTION_MODEL_STATUS = "com.wayhat.waycore.MODEL_STATUS"
    const val EXTRA_STATE = "state"            // idle | downloading | importing | ready | deleted | error
    const val EXTRA_PROGRESS = "progress"      // 0..100 o -1
    const val EXTRA_MESSAGE = "message"

    /** Gemma 3 1B (int4) preparada por el equipo LiteRT. Requiere aceptar la licencia en Hugging Face. */
    const val DEFAULT_MODEL_URL =
        "https://huggingface.co/litert-community/Gemma3-1B-IT/resolve/main/gemma3-1b-it-int4.task"

    private const val PREFS = "waycore"
    private const val KEY_MODEL_URL = "model_url"
    private const val KEY_HF_TOKEN = "hf_token"
    private const val MIN_MODEL_BYTES = 40L * 1024 * 1024 // ningún LLM real pesa menos que esto
    private const val BUFFER = 256 * 1024

    private fun modelsDir(context: Context): File = File(context.filesDir, "models").apply { mkdirs() }
    fun modelFile(context: Context): File = File(modelsDir(context), "karbys-local-model.task")
    private fun tempFile(context: Context): File = File(modelsDir(context), "download.part")

    fun isModelReady(context: Context): Boolean {
        val f = modelFile(context)
        return f.isFile && f.length() >= MIN_MODEL_BYTES
    }

    fun statusText(context: Context): String {
        val f = modelFile(context)
        if (!f.isFile) return "Sin modelo local instalado"
        val mb = f.length() / (1024 * 1024)
        return if (f.length() >= MIN_MODEL_BYTES) "Modelo instalado ($mb MB)"
        else "Archivo de modelo incompleto ($mb MB). Vuelve a instalarlo."
    }

    fun deleteModel(context: Context) {
        modelFile(context).delete()
        tempFile(context).delete()
        broadcast(context, "deleted", -1, "Modelo eliminado")
    }

    fun savedUrl(context: Context): String =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_MODEL_URL, DEFAULT_MODEL_URL) ?: DEFAULT_MODEL_URL

    fun saveUrl(context: Context, url: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_MODEL_URL, url.trim()).apply()
    }

    fun savedToken(context: Context): String =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_HF_TOKEN, "") ?: ""

    fun saveToken(context: Context, token: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_HF_TOKEN, token.trim()).apply()
    }

    /** Descarga el modelo desde una URL directa. Si el repo es privado/licenciado, acepta [token] de Hugging Face. */
    suspend fun download(context: Context, urlText: String, token: String) {
        withContext(Dispatchers.IO) {
            broadcast(context, "downloading", 0, "Iniciando descarga…")
            val tmp = tempFile(context)
            tmp.delete()
            try {
                val conn = (URL(urlText.trim()).openConnection() as HttpURLConnection).apply {
                    connectTimeout = 20_000
                    readTimeout = 60_000
                    instanceFollowRedirects = true
                    setRequestProperty("User-Agent", "WayCore")
                    if (token.isNotBlank()) setRequestProperty("Authorization", "Bearer ${token.trim()}")
                }
                val code = try { conn.responseCode } catch (e: Exception) { throw IllegalStateException("No pude conectar con el servidor de descarga: ${e.message}") }
                if (code !in 200..299) {
                    val reason = when (code) {
                        401, 403 -> "Acceso denegado ($code). Acepta la licencia del modelo en huggingface.co y pega tu token de acceso (Settings, Access Tokens)."
                        404 -> "No encontré el archivo (404). Revisa la URL del modelo."
                        else -> "El servidor respondió con error $code."
                    }
                    throw IllegalStateException(reason)
                }
                val total = conn.contentLengthLong
                conn.inputStream.use { input ->
                    tmp.outputStream().use { out ->
                        val buf = ByteArray(BUFFER)
                        var read = 0L
                        var lastPct = -1
                        while (true) {
                            val n = input.read(buf)
                            if (n < 0) break
                            out.write(buf, 0, n)
                            read += n
                            val pct = if (total > 0) ((read * 100) / total).toInt().coerceIn(0, 99) else 0
                            if (pct != lastPct) {
                                lastPct = pct
                                broadcast(context, "downloading", pct, "Descargando modelo… $pct%")
                            }
                        }
                    }
                }
                finishInstall(context, tmp)
            } catch (e: Exception) {
                tmp.delete()
                broadcast(context, "error", -1, e.message ?: "No pude descargar el modelo.")
            }
        }
    }

    /** Copia a la app un archivo de modelo elegido por el usuario (descargas, Drive, etc.). */
    suspend fun importFromUri(context: Context, uri: Uri) {
        withContext(Dispatchers.IO) {
            broadcast(context, "importing", -1, "Copiando modelo a WayCore…")
            val tmp = tempFile(context)
            tmp.delete()
            try {
                val input = context.contentResolver.openInputStream(uri)
                    ?: throw IllegalStateException("No pude abrir el archivo elegido.")
                input.use { source ->
                    tmp.outputStream().use { out -> source.copyTo(out, BUFFER) }
                }
                finishInstall(context, tmp)
            } catch (e: Exception) {
                tmp.delete()
                broadcast(context, "error", -1, e.message ?: "No pude importar el modelo.")
            }
        }
    }

    private fun finishInstall(context: Context, tmp: File) {
        if (!tmp.isFile || tmp.length() < MIN_MODEL_BYTES) {
            tmp.delete()
            throw IllegalStateException("El archivo quedó incompleto o no es un modelo válido (${tmp.length() / (1024 * 1024)} MB).")
        }
        val target = modelFile(context)
        target.delete()
        if (!tmp.renameTo(target)) {
            tmp.copyTo(target, overwrite = true)
            tmp.delete()
        }
        val mb = target.length() / (1024 * 1024)
        broadcast(context, "ready", 100, "Modelo listo ($mb MB). Karbys ya puede pensar sin Internet.")
    }

    private fun broadcast(context: Context, state: String, progress: Int, message: String) {
        context.sendBroadcast(
            Intent(ACTION_MODEL_STATUS).setPackage(context.packageName)
                .putExtra(EXTRA_STATE, state)
                .putExtra(EXTRA_PROGRESS, progress)
                .putExtra(EXTRA_MESSAGE, message)
        )
    }
}
