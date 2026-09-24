package com.wayhat.waycore

import android.content.Context

/**
 * Guarda la clave de la API de Gemini en el almacenamiento privado de la app.
 * La primera vez que se abre WayCore, la pantalla de configuración pide la
 * clave y la deja lista para que Karbys funcione sola.
 */
object ApiKeyStore {
    private const val PREFS = "waycore"
    private const val KEY = "gemini_api_key"

    private fun clean(value: String): String = value.trim()
        .removeSurrounding("\"")
        .replace("\r", "")
        .replace("\n", "")
        .trim()

    /** Devuelve la clave guardada por el usuario o, en su defecto, la incluida en el build. */
    fun get(context: Context): String {
        val stored = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY, "").orEmpty()
        val cleaned = clean(stored)
        if (cleaned.isNotEmpty()) return cleaned
        return clean(BuildConfig.GEMINI_API_KEY)
    }

    fun save(context: Context, apiKey: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY, clean(apiKey))
            .apply()
    }

    fun isConfigured(context: Context): Boolean = get(context).isNotEmpty()
}
