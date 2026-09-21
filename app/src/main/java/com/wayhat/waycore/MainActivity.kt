package com.wayhat.waycore

import android.Manifest
import android.content.*
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.*
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import org.json.JSONObject
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    private var ready by mutableStateOf(false)
    private var paused by mutableStateOf(false)
    private var wayHatConnected by mutableStateOf(false)
    private var wayHatMessage by mutableStateOf("Buscando WayHat…")
    private var right by mutableStateOf(-1)
    private var left by mutableStateOf(-1)
    private var rear by mutableStateOf(-1)
    private var tf by mutableStateOf(-1)
    private var closest by mutableStateOf(-1)
    private var threshold by mutableStateOf(50)
    private var mode by mutableStateOf("SAFE")
    private var buzzer by mutableStateOf(true)
    private var battery by mutableStateOf(0)
    private var locationText by mutableStateOf("Ubicación no disponible")

    // IA local
    private var aiEngine by mutableStateOf(KarbysRouter.ENGINE_LOCAL_FIRST)
    private var modelStatus by mutableStateOf("Sin modelo local instalado")
    private var modelProgress by mutableStateOf(-1)
    private var modelBusy by mutableStateOf(false)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private val permissions = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        val mic = result[Manifest.permission.RECORD_AUDIO] == true || has(Manifest.permission.RECORD_AUDIO)
        if (mic) startKarbys() else paused = true
        startWayHat()
        updateDeviceInfo()
    }

    private val pickModel = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            modelStatus = "Copiando el modelo a WayCore…"
            modelBusy = true
            scope.launch(Dispatchers.IO) { ModelManager.importFromUri(applicationContext, uri) }
        }
    }

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent == null) return
            when (intent.action) {
                WayHatService.ACTION_STATUS -> {
                    intent.getStringExtra("message")?.let { wayHatMessage = it }
                    if (intent.hasExtra("connected")) wayHatConnected = intent.getBooleanExtra("connected", false)
                    intent.getStringExtra("telemetry")?.let { parseTelemetry(it) }
                }
                ModelManager.ACTION_MODEL_STATUS -> {
                    val state = intent.getStringExtra(ModelManager.EXTRA_STATE).orEmpty()
                    val message = intent.getStringExtra(ModelManager.EXTRA_MESSAGE).orEmpty()
                    modelProgress = intent.getIntExtra(ModelManager.EXTRA_PROGRESS, -1)
                    modelBusy = state == "downloading" || state == "importing"
                    when (state) {
                        "ready", "deleted" -> {
                            modelProgress = -1
                            LocalLlmClient.invalidate()
                            modelStatus = ModelManager.statusText(this@MainActivity)
                        }
                        "error" -> {
                            modelProgress = -1
                            modelStatus = if (message.isBlank()) "No pude instalar el modelo." else message
                        }
                        else -> modelStatus = message.ifBlank { ModelManager.statusText(this@MainActivity) }
                    }
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val filter = IntentFilter().apply {
            addAction(WayHatService.ACTION_STATUS)
            addAction(ModelManager.ACTION_MODEL_STATUS)
        }
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
        else registerReceiver(receiver, filter)

        aiEngine = KarbysRouter.engine(this)
        modelStatus = ModelManager.statusText(this)

        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    var prompt by remember { mutableStateOf("") }
                    var modelUrl by remember { mutableStateOf(ModelManager.savedUrl(this@MainActivity)) }
                    var hfToken by remember { mutableStateOf(ModelManager.savedToken(this@MainActivity)) }
                    Column(
                        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text("WAYCORE", style = MaterialTheme.typography.headlineMedium)
                        Text(if (wayHatConnected) "WayHat conectado" else wayHatMessage)
                        Spacer(Modifier.height(14.dp))
                        Button(
                            onClick = { if (!ready) requestPermissionsIfNeeded() else send(KarbysService.ACTION_LISTEN) },
                            modifier = Modifier.size(230.dp).semantics { contentDescription = "Hablar con Karbys" }
                        ) { Text(if (ready) "HABLAR" else "KARBYS") }

                        OutlinedTextField(
                            value = prompt, onValueChange = { prompt = it },
                            modifier = Modifier.fillMaxWidth().padding(top = 18.dp),
                            label = { Text("Escribe una pregunta para Karbys") }
                        )
                        Button(onClick = { if (prompt.isNotBlank()) { sendText(prompt.trim()); prompt = "" } }, modifier = Modifier.padding(top = 8.dp)) {
                            Text("ENVIAR")
                        }

                        HorizontalDivider(Modifier.padding(vertical = 18.dp))
                        Text("MOTOR DE IA DE KARBYS", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "La IA local piensa en tu teléfono: responde más rápido y sin Internet, y conserva el control de WayHat.",
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(vertical = 6.dp)
                        )
                        listOf(
                            KarbysRouter.ENGINE_LOCAL_FIRST to "Primero IA local (recomendado)",
                            KarbysRouter.ENGINE_LOCAL_ONLY to "Solo IA local, sin Internet",
                            KarbysRouter.ENGINE_GEMINI_FIRST to "Primero Gemini, IA local de respaldo",
                            KarbysRouter.ENGINE_GEMINI_ONLY to "Solo Gemini"
                        ).forEach { (value, label) ->
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Motor de IA: $label" }
                            ) {
                                RadioButton(selected = aiEngine == value, onClick = { chooseEngine(value) })
                                Text(label)
                            }
                        }

                        HorizontalDivider(Modifier.padding(vertical = 14.dp))
                        Text("MODELO DE IA LOCAL", style = MaterialTheme.typography.titleLarge)
                        Text(modelStatus, modifier = Modifier.padding(top = 6.dp))
                        if (modelProgress in 0..100 && modelBusy) {
                            LinearProgressIndicator(
                                progress = { modelProgress / 100f },
                                modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                            )
                        }
                        Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { pickModel.launch(arrayOf("*/*")) }, enabled = !modelBusy, modifier = Modifier.weight(1f)) {
                                Text("ELEGIR ARCHIVO")
                            }
                            OutlinedButton(
                                onClick = { ModelManager.deleteModel(applicationContext); LocalLlmClient.invalidate() },
                                enabled = !modelBusy && ModelManager.isModelReady(applicationContext),
                                modifier = Modifier.weight(1f)
                            ) { Text("BORRAR MODELO") }
                        }
                        OutlinedTextField(
                            value = modelUrl,
                            onValueChange = { modelUrl = it },
                            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                            label = { Text("URL directa del modelo (.task)") },
                            singleLine = true,
                            enabled = !modelBusy
                        )
                        OutlinedTextField(
                            value = hfToken,
                            onValueChange = { hfToken = it },
                            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                            label = { Text("Token de Hugging Face (opcional)") },
                            singleLine = true,
                            visualTransformation = PasswordVisualTransformation(),
                            enabled = !modelBusy
                        )
                        Button(
                            onClick = {
                                ModelManager.saveUrl(applicationContext, modelUrl)
                                ModelManager.saveToken(applicationContext, hfToken)
                                modelBusy = true
                                modelStatus = "Preparando descarga…"
                                scope.launch(Dispatchers.IO) { ModelManager.download(applicationContext, modelUrl, hfToken) }
                            },
                            enabled = !modelBusy && modelUrl.isNotBlank(),
                            modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                        ) { Text("DESCARGAR MODELO") }
                        Text(
                            "El modelo Gemma 3 (1B) pesa unos 560 MB. Para descargarlo desde Hugging Face acepta antes su licencia en huggingface.co/litert-community/Gemma3-1B-IT con tu cuenta y crea un token en Settings, Access Tokens. También puedes descargar el archivo con tu navegador y usar ELEGIR ARCHIVO. Sin modelo local ni clave de Gemini, Karbys igual responde sus comandos básicos: hora, batería, ubicación, recordatorios y controles directos de WayHat.",
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(top = 8.dp)
                        )

                        HorizontalDivider(Modifier.padding(vertical = 18.dp))
                        Text("WAYHAT", style = MaterialTheme.typography.titleLarge)
                        Text("Modo: ${if (mode == "SAFE") "Seguro" else "Charla"}")
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { mode = "SAFE"; sendConfig() }, Modifier.weight(1f)) { Text("SEGURO") }
                            Button(onClick = { mode = "CHAT"; sendConfig() }, Modifier.weight(1f)) { Text("CHARLA") }
                        }
                        Text("Sensibilidad: $threshold cm")
                        Slider(value = threshold.toFloat(), onValueChange = { threshold = (it / 5).roundToInt() * 5 }, valueRange = 20f..100f, onValueChangeFinished = { sendConfig() })
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Avisos sonoros")
                            Spacer(Modifier.width(12.dp))
                            Switch(checked = buzzer, onCheckedChange = { buzzer = it; sendConfig() })
                        }

                        Text("Derecha: ${cm(right)}   Izquierda: ${cm(left)}   Atrás: ${cm(rear)}")
                        Text("TF-Luna: ${cm(tf)}   Más cercano: ${cm(closest)}")
                        Text("Batería: $battery%")
                        Text("GPS: $locationText")
                        Spacer(Modifier.height(12.dp))
                        Button(onClick = { startWayHat() }) { Text("RECONECTAR WAYHAT") }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { sendHardware("BUZZER_TEST") }) { Text("PROBAR BUZZER") }
                            Button(onClick = { sendHardware("SENSORS") }) { Text("ACTUALIZAR") }
                        }
                        if (paused) Button(onClick = { requestPermissionsIfNeeded() }) { Text("ACTIVAR KARBYS") }
                    }
                }
            }
        }
        requestPermissionsIfNeeded()
    }

    override fun onDestroy() {
        unregisterReceiver(receiver)
        scope.cancel()
        super.onDestroy()
    }

    private fun chooseEngine(value: String) {
        aiEngine = value
        KarbysRouter.setEngine(this, value)
    }

    private fun requestPermissionsIfNeeded() {
        val needed = mutableListOf<String>()
        if (!has(Manifest.permission.RECORD_AUDIO)) needed += Manifest.permission.RECORD_AUDIO
        if (!has(Manifest.permission.ACCESS_FINE_LOCATION) && !has(Manifest.permission.ACCESS_COARSE_LOCATION)) needed += Manifest.permission.ACCESS_COARSE_LOCATION
        if (Build.VERSION.SDK_INT >= 31 && !has(Manifest.permission.BLUETOOTH_CONNECT)) needed += Manifest.permission.BLUETOOTH_CONNECT
        if (Build.VERSION.SDK_INT >= 31 && !has(Manifest.permission.BLUETOOTH_SCAN)) needed += Manifest.permission.BLUETOOTH_SCAN
        if (Build.VERSION.SDK_INT >= 33 && !has(Manifest.permission.POST_NOTIFICATIONS)) needed += Manifest.permission.POST_NOTIFICATIONS
        if (needed.isEmpty()) { startKarbys(); startWayHat(); updateDeviceInfo() } else permissions.launch(needed.toTypedArray())
    }

    private fun startKarbys() {
        ready = true; paused = false
        ContextCompat.startForegroundService(this, Intent(this, KarbysService::class.java).setAction(KarbysService.ACTION_GREETING))
    }

    private fun startWayHat() {
        ContextCompat.startForegroundService(this, Intent(this, WayHatService::class.java).setAction(WayHatService.ACTION_START))
    }

    private fun send(action: String) = ContextCompat.startForegroundService(this, Intent(this, KarbysService::class.java).setAction(action))
    private fun sendText(text: String) = ContextCompat.startForegroundService(this, Intent(this, KarbysService::class.java).setAction(KarbysService.ACTION_TEXT).putExtra("text", text))

    private fun sendConfig() {
        sendWayHat(JSONObject().put("type", "config").put("threshold", threshold).put("mode", mode).put("buzzer", buzzer).toString())
    }
    private fun sendHardware(name: String) {
        sendWayHat(JSONObject().put("type", "command").put("name", name).toString())
    }
    private fun sendWayHat(json: String) {
        ContextCompat.startForegroundService(this, Intent(this, WayHatService::class.java).setAction(WayHatService.ACTION_COMMAND).putExtra(WayHatService.EXTRA_JSON, json))
    }

    private fun parseTelemetry(line: String) {
        try {
            val o = JSONObject(line)
            right = o.optInt("right", right); left = o.optInt("left", left); rear = o.optInt("rear", rear)
            tf = o.optInt("tf", tf); closest = o.optInt("closest", closest)
            threshold = o.optInt("threshold", threshold)
            mode = o.optString("mode", mode)
            buzzer = o.optBoolean("buzzer", buzzer)
        } catch (_: Exception) { }
    }

    private fun updateDeviceInfo() {
        val intent = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = intent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = intent?.getIntExtra(BatteryManager.EXTRA_SCALE, 100) ?: 100
        battery = if (level >= 0) level * 100 / scale else 0
        val lm = getSystemService(LOCATION_SERVICE) as LocationManager
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
        val loc = providers.mapNotNull { try { lm.getLastKnownLocation(it) } catch (_: Exception) { null } }.maxByOrNull { it.time }
        if (loc != null) locationText = "%.5f, %.5f".format(loc.latitude, loc.longitude)
    }

    private fun cm(v: Int) = if (v > 0) "$v cm" else "—"
    private fun has(permission: String) = ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
}
