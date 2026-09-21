package com.wayhat.waycore

import android.content.Context

/**
 * Decide quién piensa la respuesta de Karbys: la IA local (en el teléfono,
 * rápida y sin Internet) o Gemini (nube). Con respaldo cruzado según el modo
 * elegido en la pantalla principal.
 */
object KarbysRouter {
    private const val PREFS = "waycore"
    private const val KEY_ENGINE = "ai_engine"

    const val ENGINE_LOCAL_FIRST = "local_first"
    const val ENGINE_LOCAL_ONLY = "local_only"
    const val ENGINE_GEMINI_FIRST = "gemini_first"
    const val ENGINE_GEMINI_ONLY = "gemini_only"

    fun engine(context: Context): String =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY_ENGINE, ENGINE_LOCAL_FIRST) ?: ENGINE_LOCAL_FIRST

    fun setEngine(context: Context, value: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_ENGINE, value).apply()
    }

    suspend fun ask(
        context: Context,
        user: String,
        memory: List<ConversationTurn>,
        deviceContext: String,
        onFirstLocalLoad: (() -> Unit)? = null
    ): String = when (engine(context)) {
        ENGINE_LOCAL_ONLY ->
            askLocal(context, user, memory, deviceContext, onFirstLocalLoad)
                ?: "No pude usar mi IA local. Si aún no instalaste el modelo, hazlo desde la pantalla principal de WayCore. Si ya lo instalaste, intenta de nuevo."

        ENGINE_GEMINI_ONLY ->
            askGemini(user, memory, deviceContext)
                ?: "No pude usar Gemini. Revisa la clave y tu conexión a Internet."

        ENGINE_GEMINI_FIRST ->
            askGemini(user, memory, deviceContext)
                ?: askLocal(context, user, memory, deviceContext, onFirstLocalLoad)
                ?: "Gemini falló y la IA local tampoco está lista. Revisa tu conexión o instala el modelo local desde la pantalla principal."

        else ->
            askLocal(context, user, memory, deviceContext, onFirstLocalLoad)
                ?: askGemini(user, memory, deviceContext)
                ?: finalFallback(context)
    }

    private suspend fun askLocal(
        context: Context,
        user: String,
        memory: List<ConversationTurn>,
        deviceContext: String,
        onFirstLocalLoad: (() -> Unit)?
    ): String? {
        if (!LocalLlmClient.modelInstalled(context)) return null
        return try {
            if (LocalLlmClient.willNeedLoad(context)) onFirstLocalLoad?.invoke()
            LocalLlmClient.ask(context, user, memory, deviceContext)
        } catch (_: Throwable) {
            null
        }
    }

    private suspend fun askGemini(user: String, memory: List<ConversationTurn>, deviceContext: String): String? =
        try {
            GeminiClient.askOrNull(user, memory, deviceContext)
        } catch (_: Throwable) {
            null
        }

    private fun finalFallback(context: Context): String =
        if (!LocalLlmClient.modelInstalled(context) && !GeminiClient.hasApiKey()) {
            "Todavía no tengo un cerebro de respaldo disponible. Instala mi modelo local desde la pantalla principal o agrega la clave de Gemini. Mientras tanto puedo ayudarte con la hora, la batería, tu ubicación, recordatorios y los controles directos de WayHat."
        } else {
            "No pude generar una respuesta en este momento. Intenta preguntarme de nuevo."
        }
}
