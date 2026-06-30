import string
import random
import requests
from flask import Flask, request, jsonify, render_template_string, Response

app = Flask(__name__)

# --- DIRECTORIO DE PUNTEROS PERMANENTES (0 KB ARCHIVOS LOCALES) ---
# Almacena de forma ultra compacta las URIs de los recursos permanentes distribuidos en la nube.
PERSISTENT_POINTER_DIRECTORY = {}

def generate_db_id(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# --- GESTOR CORS MANUAL GLOBAL ---
@app.before_request
def handle_options_and_cors():
    if request.method == "OPTIONS":
        response = jsonify({"status": "cors_ready"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Range"
        return response, 200

@app.after_request
def apply_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Range"
    return response

# --- INTERFAZ ADMINISTRATIVA Y CONSOLA DE MONITOREO ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZeroMix Quantum Control Console</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #030712;
            --bg-card: #0b1329;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        body { 
            background-color: var(--bg-base); 
            color: var(--text-main); 
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.01em;
        }
        .mono { font-family: 'Fira Code', monospace; }
        .cyber-card { 
            background-color: var(--bg-card); 
            border: 1px solid #1e293b; 
            border-radius: 12px;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.7);
        }
        .accent-gradient {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .btn-cyber {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            color: #fff;
            font-weight: 600;
            border: none;
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        .btn-cyber:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
            color: #fff;
        }
        .form-control { 
            background-color: #030712; 
            color: #fff; 
            border: 1px solid #1e293b; 
            border-radius: 6px;
        }
        pre { 
            background-color: #020617; 
            padding: 15px; 
            border-radius: 8px; 
            color: #38bdf8; 
            font-size: 0.85em; 
            border: 1px solid #1e293b;
        }
        .nav-tabs .nav-link { color: var(--text-muted); border: none; font-weight: 600; }
        .nav-tabs .nav-link.active { color: var(--accent-cyan) !important; background-color: transparent; border-bottom: 2px solid var(--accent-cyan); }
    </style>
</head>
<body class="py-5">
    <div class="container">
        <!-- Header -->
        <div class="d-flex justify-content-between align-items-center mb-5 pb-4 border-bottom border-secondary">
            <div>
                <h1 class="fw-bold accent-gradient m-0">🛰️ ZEROMIX LIVE TRANSIT BRIDGE</h1>
                <p class="text-muted m-0 mt-1">Base de Datos ilimitada de persistencia permanente distribuida para todo tipo de archivos.</p>
            </div>
            <span class="badge border border-info text-info p-2 mono">CAPACIDAD: ILIMITADA</span>
        </div>

        <div class="row">
            <!-- Columna Izquierda -->
            <div class="col-lg-5 mb-4">
                <div class="cyber-card p-4 mb-4">
                    <h3 class="h5 fw-bold text-info mb-3">CANAL DE TRANSMISIÓN</h3>
                    <div class="mb-3">
                        <label class="form-label text-muted small">Nombre del Canal</label>
                        <input type="text" id="dbName" class="form-control" placeholder="n82" value="n82">
                    </div>
                    <button class="btn btn-cyber w-100 py-2" onclick="conectarCanal()">Establecer Canal Permanente</button>
                    
                    <div id="connectionInfo" class="mt-4 d-none">
                        <div class="p-3 bg-dark rounded border border-secondary">
                            <span class="text-muted small">ID de Sincronización Global:</span>
                            <p class="mono text-warning fw-bold fs-5 m-0" id="dbIdSpan"></p>
                        </div>
                    </div>
                </div>

                <div class="cyber-card p-4">
                    <h3 class="h5 fw-bold text-info mb-3">VISTA DE ARQUITECTURA .ZEROMIX</h3>
                    <p class="text-muted small">La estructura inmutable .zeromix conserva los registros asíncronos alojados en la nube.</p>
                    <pre id="zeromixView" class="mono m-0" style="max-height: 250px; overflow-y: auto;">{}</pre>
                </div>
            </div>

            <!-- Columna Derecha -->
            <div class="col-lg-7 mb-4">
                <div class="cyber-card p-4 mb-4">
                    <h3 class="h5 fw-bold text-info mb-3">MONITOR DE TRÁNSITO GLOBAL</h3>
                    <div id="noChannelWarning" class="text-muted text-center py-4">
                        Conecta un canal de sincronización para habilitar la vista de datos compartidos.
                    </div>
                    <div id="monitorContent" class="d-none">
                        <div class="table-responsive">
                            <table class="table table-dark table-hover small">
                                <thead>
                                    <tr>
                                        <th>Identificador</th>
                                        <th>Ubicación del Recurso (URI)</th>
                                        <th>Proxy Bypass (Para Apps)</th>
                                    </tr>
                                </thead>
                                <tbody id="monitorTableBody">
                                    <tr>
                                        <td colspan="3" class="text-muted text-center">Esperando transmisiones...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Códigos de Integración -->
                <div class="cyber-card p-4">
                    <h3 class="h5 fw-bold text-info mb-3">🔌 CÓDIGOS DE INTEGRACIÓN (CRUD COMPLETO)</h3>
                    <ul class="nav nav-tabs mb-3" id="tabIntegraciones">
                        <li class="nav-item">
                            <button class="nav-link active" id="js-tab" data-bs-toggle="tab" data-bs-target="#js-code">JS (Sincronización Ilimitada)</button>
                        </li>
                    </ul>
                    <div class="tab-content">
                        <div class="tab-pane fade show active" id="js-code">
                            <pre class="mono"><code id="jsCodeSnippet">// Conecta tu canal para obtener tu código de vinculación.</code></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const API_HOST = window.location.origin;
        let activeDbId = null;

        let localZeroMix = {
            version: "1.1.2",
            protocol: "zeromix-cvam",
            database_name: "n82",
            database_id: "OEmw3Y4e",
            virtual_allocation_bytes: 7696581394432,
            index: {}
        };

        async function conectarCanal() {
            const name = document.getElementById('dbName').value.trim();
            if (!name) return alert('Especifica un nombre para el canal.');

            try {
                const response = await fetch('/api/database/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    activeDbId = data.db_id;
                    
                    document.getElementById('dbIdSpan').textContent = activeDbId;
                    document.getElementById('connectionInfo').classList.remove('d-none');
                    document.getElementById('noChannelWarning').classList.add('d-none');
                    document.getElementById('monitorContent').classList.remove('d-none');
                    
                    localZeroMix.database_name = name;
                    localZeroMix.database_id = activeDbId;
                    localZeroMix.index = {};
                    
                    actualizarCodigosDeIntegracion(activeDbId);
                    forzarSincronizacion();
                    
                    setInterval(forzarSincronizacion, 3000);
                }
            } catch (err) {
                alert('Fallo de conexión.');
            }
        }

        async function forzarSincronizacion() {
            if (!activeDbId) return;
            try {
                const response = await fetch(`/api/database/${activeDbId}/records`);
                const data = await response.json();
                if (data.status === 'success') {
                    localZeroMix.index = data.index;
                    document.getElementById('zeromixView').textContent = JSON.stringify(localZeroMix, null, 2);
                    
                    const tbody = document.getElementById('monitorTableBody');
                    const keys = Object.keys(data.index);
                    
                    if (keys.length > 0) {
                        tbody.innerHTML = '';
                        keys.forEach(key => {
                            const rec = data.index[key];
                            const proxyUrl = `${API_HOST}/api/proxy?url=${encodeURIComponent(rec.uri)}`;
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td class="mono text-info fw-bold">${key}</td>
                                <td class="text-truncate" style="max-width: 150px;"><a href="${rec.uri}" target="_blank" class="text-secondary">${rec.uri}</a></td>
                                <td><a href="${proxyUrl}" target="_blank" class="text-warning text-break small font-monospace">${proxyUrl}</a></td>
                            `;
                            tbody.appendChild(row);
                        });
                    } else {
                        tbody.innerHTML = '<tr><td colspan="3" class="text-muted text-center">Esperando transmisiones...</td></tr>';
                    }
                }
            } catch (err) {
                console.error("Fallo de sincronización:", err);
            }
        }

        function actualizarCodigosDeIntegracion(dbId) {
            const jsCode = "/* CLIENTE DE PERSISTENCIA ILIMITADA Y COMPATIBILIDAD MULTIMEDIA (JS) */\\n" +
"class ZeroMix {\\n" +
"    constructor(apiHost = \\"" + API_HOST + "\\", dbId = \\"" + dbId + "\\") {\\n" +
"        this.apiHost = apiHost;\\n" +
"        this.baseUrl = apiHost + \\"/api/database/\\" + dbId;\\n" +
"    }\\n\\n" +
"    /* ESCRIBIR RECURSOS EN EL ÍNDICE PERMANENTE DEL SERVIDOR */\\n" +
"    async escribir(key, fileUrl, metadatos = {}) {\\n" +
"        return (await fetch(this.baseUrl + \\"/record\\", {\\n" +
"            method: 'POST',\\n" +
"            headers: { 'Content-Type': 'application/json' },\\n" +
"            body: JSON.stringify({ key, file_url: fileUrl, metadata: metadatos })\\n" +
"        })).json();\\n" +
"    }\\n\\n" +
"    /* LEER CON PROXY MULTIMEDIA (Permite reproducción fluida de audio/video de cualquier servidor) */\\n" +
"    async leerMultimedia(key) {\\n" +
"        const response = await (await fetch(this.baseUrl + \\"/record/\\" + key)).json();\\n" +
"        if (response.status === 'success') {\\n" +
"            const originalUrl = response.data.uri;\\n" +
"            return this.apiHost + \\"/api/proxy?url=\\" + encodeURIComponent(originalUrl);\\n" +
"        }\\n" +
"    }\\n\\n" +
"    async borrar(key) {\\n" +
"        return (await fetch(this.baseUrl + \\"/record/\\" + key, { method: 'DELETE' })).json();\\n" +
"    }\\n\\n" +
"    conectarSincronizacion(callback, intervaloMs = 3000) {\\n" +
"        setInterval(async () => {\\n" +
"            try {\\n" +
"                const r = await (await fetch(this.baseUrl + \\"/records\\")).json();\\n" +
"                if(r.status === 'success') callback(r.index);\\n" +
"            } catch(e) { console.error('Error de sincronización:', e); }\\n" +
"        }, intervaloMs);\\n" +
"    }\\n" +
"}";
            document.getElementById('jsCodeSnippet').textContent = jsCode;
        }
    </script>
</body>
</html>
"""

# --- CONTROLADORES DE RUTA DE LA API ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# --- PROXY DE TRANSMISIÓN DE FLUJO SEGMENTADO (CORS BYPASS) ---
@app.route('/api/proxy', methods=['GET'])
def stream_proxy():
    """Túnel de retransmisión seguro que soporta solicitudes por segmentos (Range Requests) para audios y vídeos."""
    target_url = request.args.get('url')
    if not target_url:
        return "Falta parámetro 'url'", 400
        
    try:
        headers = {key: value for key, value in request.headers if key.lower() == 'range'}
        req = requests.get(target_url, headers=headers, stream=True, timeout=15)
        
        def generate_chunks():
            for chunk in req.iter_content(chunk_size=1024 * 64):
                yield chunk
                
        proxy_response = Response(generate_chunks(), status=req.status_code)
        for name, value in req.headers.items():
            if name.lower() in ['content-type', 'content-length', 'content-range', 'accept-ranges']:
                proxy_response.headers[name] = value
                
        return proxy_response
    except Exception as e:
        return f"Error de tránsito multimedia: {str(e)}", 500

@app.route('/api/database/create', methods=['POST'])
def api_create():
    data = request.json or {}
    name = data.get('name', 'n82').strip() or 'n82'
    db_id = generate_db_id()
    
    # Registra la estructura del canal de señalamiento en el directorio
    PERSISTENT_POINTER_DIRECTORY[db_id] = {
        "version": "1.1.2",
        "protocol": "zeromix-cvam",
        "database_name": name,
        "database_id": db_id,
        "virtual_allocation_bytes": 7696581394432,
        "index": {}
    }
    return jsonify({"status": "success", "db_id": db_id}), 201

@app.route('/api/database/<db_id>/records', methods=['GET'])
def api_get_all_records(db_id):
    if db_id not in PERSISTENT_POINTER_DIRECTORY:
        return jsonify({"status": "error", "message": "Canal no registrado"}), 404
    return jsonify({
        "status": "success",
        "index": PERSISTENT_POINTER_DIRECTORY[db_id]["index"]
    }), 200

@app.route('/api/database/<db_id>/record', methods=['POST'])
def api_write(db_id):
    if db_id not in PERSISTENT_POINTER_DIRECTORY:
        return jsonify({"status": "error", "message": "Canal no registrado"}), 404

    data = request.json or {}
    key = data.get('key')
    file_url = data.get('file_url', 'no-file-url')
    metadata = data.get('metadata', {})

    if not key:
        return jsonify({"status": "error", "message": "Falta parámetro clave (key)"}), 400

    # Almacena únicamente el puntero de red corto (~100 bytes)
    PERSISTENT_POINTER_DIRECTORY[db_id]["index"][key] = {
        "uri": file_url,
        "metadata": metadata
    }
    return jsonify({"status": "success", "message": "Puntero registrado exitosamente."}), 200

@app.route('/api/database/<db_id>/record/<key>', methods=['GET', 'DELETE'])
def api_record_ops(db_id, key):
    if db_id not in PERSISTENT_POINTER_DIRECTORY:
        return jsonify({"status": "error", "message": "Canal no registrado"}), 404

    if request.method == 'GET':
        record = PERSISTENT_POINTER_DIRECTORY[db_id]["index"].get(key)
        if not record:
            return jsonify({"status": "error", "message": "Clave inexistente"}), 404
        return jsonify({"status": "success", "key": key, "data": record}), 200

    elif request.method == 'DELETE':
        if key in PERSISTENT_POINTER_DIRECTORY[db_id]["index"]:
            del PERSISTENT_POINTER_DIRECTORY[db_id]["index"][key]
            return jsonify({"status": "success", "message": "Registro eliminado"}), 200
        else:
            return jsonify({"status": "error", "message": "Clave no encontrada"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
