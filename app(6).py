from flask import Flask, request, render_template_string, redirect, session
import requests
import os
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

# 🔗 Datos de Supabase
SUPABASE_URL = "https://zdbwnxnikspdexfpuhad.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY environment variable is not set")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}
# 🟢 Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        contrasena = request.form.get("contrasena")
        if not usuario or not contrasena:
            return render_template_string(LOGIN_TEMPLATE, error="Usuario y contraseña requeridos")
        query = f"?nombre_usuario=eq.{usuario}"
        response = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios{query}", headers=HEADERS)

        if response.status_code == 200 and len(response.json()) == 1:
            user = response.json()[0]
            if check_password_hash(user.get("contrasena", ""), contrasena):
                session["usuario"] = usuario
                return redirect("/home")
        return render_template_string(LOGIN_TEMPLATE, error="Usuario o contraseña incorrectos")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# 🟢 Home
@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect("/")
    return render_template_string(HOME_TEMPLATE, usuario=session["usuario"])

# 🟢 Alta de Lead
@app.route("/formulario_lead", methods=["GET", "POST"])
def formulario_lead():
    if "usuario" not in session:
        return redirect("/")
    if request.method == "POST":
        data = {
            "tipo_cliente": request.form.get("tipo_lead"),
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead"),
            "codigo_postal": request.form.get("codigo_postal"),
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona"),
            "persona_contacto": request.form.get("persona_contacto"),
            "telefono": request.form.get("telefono"),
            "email": request.form.get("email"),
            "observaciones": request.form.get("observaciones")
        }

        required = [data["tipo_cliente"], data["direccion"], data["nombre_cliente"], data["localidad"]]
        if any(not field for field in required):
            return "Datos del lead inválidos", 400

        response = requests.post(f"{SUPABASE_URL}/rest/v1/clientes?select=id", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            cliente_id = response.json()[0]["id"]
            return redirect(f"/nuevo_equipo?cliente_id={cliente_id}")
        else:
            return f"<h3 style='color:red;'>❌ Error al registrar lead</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(FORM_TEMPLATE)

# 🟢 Alta de Equipo
@app.route("/nuevo_equipo", methods=["GET", "POST"])
def nuevo_equipo():
    if "usuario" not in session:
        return redirect("/")
    cliente_id = request.args.get("cliente_id")

    cliente_data = None
    if cliente_id:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}", headers=HEADERS)
        if r.status_code == 200 and r.json():
            cliente_data = r.json()[0]

    if request.method == "POST":
        equipo_data = {
            "cliente_id": request.form.get("cliente_id"),
            "tipo_equipo": request.form.get("tipo_equipo"),
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "ubicacion": request.form.get("ubicacion"),
            "descripcion": request.form.get("descripcion"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato"),
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima")
        }

        required = [equipo_data["cliente_id"], equipo_data["tipo_equipo"]]
        if any(not field for field in required):
            return "Datos del equipo inválidos", 400

        res = requests.post(f"{SUPABASE_URL}/rest/v1/equipos", json=equipo_data, headers=HEADERS)
        if res.status_code in [200, 201]:
            return f"""
            <h3>✅ Equipo registrado correctamente</h3>
            <a href='/nuevo_equipo?cliente_id={cliente_id}' class='button'>➕ Añadir otro equipo</a><br><br>
            <a href='/home' class='button'>🏠 Finalizar y volver al inicio</a>
            """
        else:
            return f"<h3 style='color:red;'>❌ Error al registrar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(EQUIPO_TEMPLATE, cliente=cliente_data)

# 🟢 Plantillas

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Login</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Bienvenido, {{ usuario }}</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Usuario:</label><br>
                <input type="text" name="usuario" required><br><br>
                <label>Contraseña:</label><br>
                <input type="password" name="contrasena" required><br><br>
                <button type="submit" class="button">Iniciar Sesión</button>
            </form>
            {% if error %}
            <p style="color: red;">{{ error }}</p>
            {% endif %}
        </div>
    </main>
</body>
</html>
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Bienvenido</title>
    <link rel='stylesheet' href='/static/styles.css'>
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Bienvenido, {{ usuario }}</h1>
        </div>
    </div>
</header>
    <main>
        <div class='menu'>
            <a href="/formulario_lead" class='button'>➕ Añadir Lead</a>
            <a href="/leads_dashboard" class='button'>📊 Visualizar Datos</a>
            <a href="/logout" class='button'>🚪 Cerrar Sesión</a>
        </div>
    </main>
</body>
</html>
"""

FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Formulario Lead</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Introducir datos</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Tipo de Lead:</label><br>
                <select name="tipo_lead" required>
                    <option value="">-- Selecciona un tipo --</option>
                    <option value="Comunidad">Comunidad</option>
                    <option value="Hotel/Apartamentos">Hotel/Apartamentos</option>
                    <option value="Empresa">Empresa</option>
                    <option value="Otro">Otro</option>
                </select><br><br>

                <label>Dirección:</label><br>
                <input type="text" name="direccion" required><br><br>

                <label>Nombre de la Instalación:</label><br>
                <input type="text" name="nombre_lead" required><br><br>

                <label>Código Postal:</label><br>
                <input type="text" name="codigo_postal"><br><br>

                <label>Localidad:</label><br>
                <select name="localidad" required>
                    <option value="">-- Selecciona una localidad --</option>
                    <option value="Agaete">Agaete</option>
                    <option value="Agüimes">Agüimes</option>
                    <option value="Arguineguín">Arguineguín</option>
                    <option value="Arinaga">Arinaga</option>
                    <option value="Artenara">Artenara</option>
                    <option value="Arucas">Arucas</option>
                    <option value="Carrizal">Carrizal</option>
                    <option value="Cruce de Arinaga">Cruce de Arinaga</option>
                    <option value="El Burrero">El Burrero</option>
                    <option value="El Tablero">El Tablero</option>
                    <option value="Gáldar">Gáldar</option>
                    <option value="Ingenio">Ingenio</option>
                    <option value="Jinámar">Jinámar</option>
                    <option value="La Aldea de San Nicolás">La Aldea de San Nicolás</option>
                    <option value="La Pardilla">La Pardilla</option>
                    <option value="Las Palmas de Gran Canaria">Las Palmas de Gran Canaria</option>
                    <option value="Maspalomas">Maspalomas</option>
                    <option value="Mogán">Mogán</option>
                    <option value="Moya">Moya</option>
                    <option value="Playa de Mogán">Playa de Mogán</option>
                    <option value="Playa del Inglés">Playa del Inglés</option>
                    <option value="Puerto Rico">Puerto Rico</option>
                    <option value="San Bartolomé de Tirajana">San Bartolomé de Tirajana</option>
                    <option value="San Fernando">San Fernando</option>
                    <option value="San Mateo">San Mateo</option>
                    <option value="Santa Brígida">Santa Brígida</option>
                    <option value="Santa Lucía de Tirajana">Santa Lucía de Tirajana</option>
                    <option value="Santa María de Guía">Santa María de Guía</option>
                    <option value="Tafira">Tafira</option>
                    <option value="Tejeda">Tejeda</option>
                    <option value="Teror">Teror</option>
                    <option value="Valleseco">Valleseco</option>
                    <option value="Valsequillo">Valsequillo</option>
                    <option value="Vecindario">Vecindario</option>
                </select><br><br>

                <label>Zona:</label><br>
                <input type="text" name="zona"><br><br>

                <label>Persona de Contacto:</label><br>
                <input type="text" name="persona_contacto"><br><br>

                <label>Teléfono:</label><br>
                <input type="text" name="telefono"><br><br>

                <label>Email:</label><br>
                <input type="email" name="email"><br><br>

                <label>Observaciones:</label><br>
                <textarea name="observaciones"></textarea><br><br>

                <button type="submit" class="button">Registrar Lead</button>
            </form>
        </div>
    </main>
</body>
</html>
"""

EQUIPO_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Formulario Equipo</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
<header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Introducir datos</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <input type="hidden" name="cliente_id" value="{{ cliente['id'] }}">

                <label>Tipo de Equipo:</label><br>
                <select name="tipo_equipo" required>
                    <option value="">-- Selecciona un tipo --</option>
                    <option value="Ascensor">Ascensor</option>
                    <option value="Elevador">Elevador</option>
                    <option value="Montaplatos">Montaplatos</option>
                    <option value="Montacargas">Montacargas</option>
                    <option value="Plataforma Salvaescaleras">Plataforma Salvaescaleras</option>
                    <option value="Otro">Otro</option>
                </select><br><br>

                <label>Empresa Mantenedora:</label><br>
                <select name="empresa_mantenedora">
                    <option value="">-- Selecciona una empresa --</option>
                    <option value="FAIN Ascensores">FAIN Ascensores</option>
                    <option value="KONE">KONE</option>
                    <option value="Otis">Otis</option>
                    <option value="Schindler">Schindler</option>
                    <option value="TKE">TKE</option>
                    <option value="Orona">Orona</option>
                    <option value="APlus Ascensores">APlus Ascensores</option>
                    <option value="Ascensores Canarias">Ascensores Canarias</option>
                    <option value="Ascensores Domingo">Ascensores Domingo</option>
                    <option value="Ascensores Vulcano Canarias">Ascensores Vulcano Canarias</option>
                    <option value="Elevadores Canarios">Elevadores Canarios</option>
                    <option value="Fedes Ascensores">Fedes Ascensores</option>
                    <option value="Gratecsa">Gratecsa</option>
                    <option value="Lift Technology">Lift Technology</option>
                    <option value="Omega Elevadores">Omega Elevadores</option>
                    <option value="Q Ascensores">Q Ascensores</option>
                </select><br><br>

                <label>Ubicación:</label><br>
                <input type="text" name="ubicacion"><br><br>

                <label>Descripción:</label><br>
                <input type="text" name="descripcion"><br><br>

                <label>Fecha Vencimiento Contrato:</label><br>
                <input type="date" name="fecha_vencimiento_contrato"><br><br>

                <label>RAE (solo para ascensores):</label><br>
                <input type="text" name="rae"><br><br>

                <label>IPO Próxima:</label><br>
                <input type="date" name="ipo_proxima"><br><br>

                <button type="submit" class="button">Registrar Equipo</button>
            </form>
        </div>
    </main>
</body>
</html>
"""
# 🟢 Listado de Leads y Equipos
@app.route("/leads")
def leads():
    if "usuario" not in session:
        return redirect("/")
    response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=*", headers=HEADERS)
    if response.status_code == 200:
        leads_data = response.json()
        # Para cada lead, traer sus equipos asociados
        for lead in leads_data:
            lead_id = lead["id"]
            equipos_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
            if equipos_response.status_code == 200:
                lead["equipos"] = equipos_response.json()
            else:
                lead["equipos"] = []
        return render_template_string(LEADS_TEMPLATE, leads=leads_data)
    else:
        return f"<h3 style='color:red;'>❌ Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

# 📝 Plantilla de listado de Leads y Equipos
LEADS_TEMPLATE = """
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Leads y Equipos</title>
    <link rel='stylesheet' href='/static/styles.css'>
</head>
<body>
 <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Leads y Equipos</h1>
        </div>
    </div>
</header>
    <h1>Leads y Equipos</h1>
    </header>
    <main>
        <div class='menu'>
            {% for lead in leads %}
                <div class='lead-box'>
                    <h3>{{ lead.nombre_cliente }} ({{ lead.tipo_cliente }})</h3>
                    <p>Dirección: {{ lead.direccion }}</p>
                    <p>Localidad: {{ lead.localidad }}</p>
                    <p>Contacto: {{ lead.persona_contacto }} - {{ lead.telefono }}</p>
                    <p>Email: {{ lead.email }}</p>
                    <p>Observaciones: {{ lead.observaciones }}</p>
                    <h4>Equipos Asociados:</h4>
                    <ul>
                        {% for equipo in lead.equipos %}
                            <li>{{ equipo.tipo_equipo }} - {{ equipo.empresa_mantenedora }} - {{ equipo.descripcion }}</li>
                        {% else %}
                            <li>No hay equipos registrados.</li>
                        {% endfor %}
                    </ul>
                </div>
                <hr>
            {% endfor %}
            <a href='/home' class='button'>🏠 Volver al inicio</a>
        </div>
    </main>
</body>
</html>
"""
@app.route("/leads_dashboard")
def leads_dashboard():
    if "usuario" not in session:
        return redirect("/")

    # Consultar todos los Leads
    response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=*", headers=HEADERS)
    if response.status_code != 200:
        return f"<h3 style='color:red;'>❌ Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    leads_data = response.json()
    rows = []

    # Recorrer leads y traer sus equipos
    for lead in leads_data:
        lead_id = lead["id"]
        equipos_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
        if equipos_response.status_code == 200:
            equipos = equipos_response.json()
            total_equipos = len(equipos)
            if equipos:
                for equipo in equipos:
                    rows.append({
                        "lead_id": lead_id,
                        "direccion": lead.get("direccion", "-"),
                        "localidad": lead.get("localidad", "-"),
                        "codigo_postal": lead.get("codigo_postal", "-"),
                        "total_equipos": total_equipos,
                        "empresa_mantenedora": equipo.get("empresa_mantenedora", "-"),
                        "fecha_vencimiento_contrato": equipo.get("fecha_vencimiento_contrato", "-"),
                        "ipo_proxima": equipo.get("ipo_proxima", "-")
                    })
            else:
                rows.append({
                    "lead_id": lead_id,
                    "direccion": lead.get("direccion", "-"),
                    "localidad": lead.get("localidad", "-"),
                    "codigo_postal": lead.get("codigo_postal", "-"),
                    "total_equipos": 0,
                    "empresa_mantenedora": "-",
                    "fecha_vencimiento_contrato": "-",
                    "ipo_proxima": "-"
                })
        else:
            rows.append({
                "lead_id": lead_id,
                "direccion": lead.get("direccion", "-"),
                "localidad": lead.get("localidad", "-"),
                "codigo_postal": lead.get("codigo_postal", "-"),
                "total_equipos": "-",
                "empresa_mantenedora": "-",
                "fecha_vencimiento_contrato": "-",
                "ipo_proxima": "-"
            })

    return render_template_string(DASHBOARD_TEMPLATE, rows=rows)
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Leads Dashboard</title>
    <link rel='stylesheet' href='/static/styles.css'>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:hover { background-color: #f5f5f5; }
        a { text-decoration: none; color: #0065a3; }
    </style>
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Bienvenido, {{ usuario }}</h1>
        </div>
    </div>
</header>
    <main>
        <div class='menu'>
            <table>
                <thead>
                    <tr>
                        <th>Dirección</th>
                        <th>Localidad</th>
                        <th>Código Postal</th>
                        <th>Total Equipos</th>
                        <th>Empresa Mantenedora</th>
                        <th>Vencimiento Contrato</th>
                        <th>IPO Próxima</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr>
                        <td><a href='/editar_lead/{{ row.lead_id }}'>{{ row.direccion }}</a></td>
                        <td>{{ row.localidad }}</td>
                        <td>{{ row.codigo_postal }}</td>
                        <td><a href='/nuevo_equipo?cliente_id={{ row.lead_id }}'>{{ row.total_equipos }}</a></td>
                        <td>{{ row.empresa_mantenedora }}</td>
                        <td>{{ row.fecha_vencimiento_contrato }}</td>
                        <td>{{ row.ipo_proxima }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href='/home' class='button'>🏠 Volver al inicio</a>
        </div>
    </main>
</body>
</html>
"""

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug)