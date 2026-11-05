from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
import sqlite3, os

# Configuramos Flask para servir archivos directamente desde la carpeta del proyecto
app = Flask(__name__, static_folder='.')
DB_NAME = "cet_kiosco.db"

# ==========================================
# 1. BASE DE DATOS
# ==========================================
def inicializar_bd():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL 
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            icono TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            producto TEXT NOT NULL,
            recreo TEXT NOT NULL,
            estado TEXT DEFAULT '⏳ Pendiente',
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    conexion.commit()
    conexion.close()

def cargar_menu_kiosco():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        menu = [
            ('Pizetas', 'Comida', 1200, '🍕'),
            ('Tostados', 'Comida', 1800, '🥪'),
            ('Variedad de Bebidas', 'Bebidas', 1400, '🥤'),
            ('Variedad de Caramelos', 'Snacks', 300, '🍬'),
            ('Alfajores', 'Snacks', 900, '🍫'),
            ('Barra de Cereal', 'Snacks', 700, '🌾'),
            ('Galletitas', 'Snacks', 800, '🍪'),
            ('Snacks Salados', 'Snacks', 1000, '🍟'),
            ('Constancia Alumno Regular', 'Preceptoría', 0, '📄'),
            ('Certificado de Examen', 'Preceptoría', 0, '📋')
        ]
        cursor.executemany("INSERT INTO productos (nombre, categoria, precio, icono) VALUES (?, ?, ?, ?)", menu)
        conexion.commit()
    conexion.close()

# ==========================================
# 2. DISEÑO IDÉNTICO AL TÓTEM DEL KIOSKO
# ==========================================
CSS_STYLE = """
<style>
    :root {
        --kiosk-orange: #f97316;
        --kiosk-bg: #e2e8f0;
        --card-white: #ffffff;
        --btn-green: #10b981;
        --btn-green-hover: #059669;
        --text-dark: #1e293b;
    }
    * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; margin: 0; padding: 0; }
    body { background-color: #cbd5e1; color: var(--text-dark); display: flex; justify-content: center; min-height: 100vh; padding: 10px; }
    .kiosk-frame {
        width: 100%;
        max-width: 500px;
        background: #ffffff;
        border-radius: 28px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.25);
        overflow: hidden;
        border: 8px solid #f97316;
        display: flex;
        flex-direction: column;
    }
    
    /* Header Naranja Estilo Totem */
    .kiosk-header {
        background: linear-gradient(180deg, #ea580c, #f97316);
        color: white;
        text-align: center;
        padding: 18px 15px 12px 15px;
        position: relative;
    }
    .kiosk-header h4 { font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; opacity: 0.9; }
    .kiosk-header h1 { font-size: 1.5rem; font-weight: 900; letter-spacing: 1px; margin-top: 2px; }
    
    .school-logo-img {
        width: 75px;
        height: 75px;
        object-fit: contain;
        margin: 8px auto 4px auto;
        display: block;
        background: white;
        padding: 5px;
        border-radius: 50%;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    .kiosk-body { padding: 16px; background-color: #f1f5f9; flex: 1; }

    /* Tarjeta Login */
    .login-card {
        background: white;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .form-group { margin-bottom: 14px; }
    .form-group label { font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; display: block; margin-bottom: 5px; }
    .form-control {
        width: 100%;
        padding: 12px;
        border-radius: 12px;
        border: 2px solid #cbd5e1;
        font-size: 0.95rem;
        outline: none;
        background: #f8fafc;
    }
    .form-control:focus { border-color: var(--kiosk-orange); background: white; }

    /* Grilla de Productos estilo Tótem */
    .section-title { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
    .product-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    .product-card {
        background: white;
        border-radius: 14px;
        padding: 10px 6px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 1px solid #e2e8f0;
    }
    .product-icon { font-size: 2.2rem; margin-bottom: 4px; }
    .product-name { font-size: 0.75rem; font-weight: 700; color: #1e293b; height: 32px; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
    .product-price { font-size: 0.85rem; font-weight: 800; color: #0f172a; margin: 4px 0; }
    
    .btn-add {
        background: var(--btn-green);
        color: white;
        border: none;
        padding: 6px 0;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 800;
        cursor: pointer;
        width: 100%;
        text-transform: uppercase;
        transition: 0.2s;
    }
    .btn-add:hover { background: var(--btn-green-hover); }

    .btn-kiosk-submit {
        background: var(--kiosk-orange);
        color: white;
        border: none;
        width: 100%;
        padding: 14px;
        border-radius: 14px;
        font-weight: 800;
        font-size: 1rem;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
        margin-top: 10px;
    }
    
    .btn-logout {
        background: #fee2e2;
        color: #ef4444;
        border: none;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        cursor: pointer;
    }

    /* Mis Pedidos */
    .order-list { list-style: none; display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
    .order-item { background: white; padding: 10px 12px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
    
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: 800; }
    .badge.pendiente { background: #fef3c7; color: #d97706; }
    .badge.proceso { background: #dbeafe; color: #2563eb; }
    .badge.listo { background: #dcfce7; color: #16a34a; }

    .admin-table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }
    .admin-table th, .admin-table td { padding: 8px 10px; font-size: 0.8rem; text-align: left; border-bottom: 1px solid #f1f5f9; }
    .admin-table th { background: #f8fafc; color: #64748b; font-weight: 700; }
</style>
"""

HTML_LOGIN = CSS_STYLE + """
<div class="kiosk-frame">
    <div class="kiosk-header">
        <h4>- Kiosko Escolar -</h4>
        <h1>¡PIDE Y RECOGE TU SNACK!</h1>
        <img src="/logo.png" alt="CET N1" class="school-logo-img" onerror="this.onerror=null; this.src='/log.png';">
    </div>
    <div class="kiosk-body">
        <div class="login-card">
            <h3 style="margin-bottom: 15px; font-size: 1rem; text-align: center;">👋 ¡Bienvenido al CET N° 1!</h3>
            <form action="/login" method="POST">
                <div class="form-group">
                    <label>Nombre y Apellido</label>
                    <input type="text" name="nombre" class="form-control" placeholder="Ej. Yanela Toledo" required>
                </div>
                <div class="form-group">
                    <label>Rol en el Sistema</label>
                    <select name="rol" class="form-control">
                        <option value="alumno">🎒 Estudiante / Docente</option>
                        <option value="admin">👨‍🍳 Encargado de Kiosco / Preceptoría</option>
                    </select>
                </div>
                <button type="submit" class="btn-kiosk-submit">INGRESAR AL KIOSKO 🚀</button>
            </form>
        </div>
    </div>
</div>
"""

HTML_CLIENTE = CSS_STYLE + """
<div class="kiosk-frame">
    <div class="kiosk-header" style="padding-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-weight: 800; font-size: 0.85rem;">👋 {{ usuario[1] }}</span>
            <a href="/"><button class="btn-logout">SALIR</button></a>
        </div>
        <h1>¡BIENVENIDO AL KIOSKO!</h1>
    </div>
    
    <div class="kiosk-body">
        <form action="/crear_pedido/{{ usuario[0] }}" method="POST">
            <h2 class="section-title">SELECCIONÁ TU SNACK</h2>
            
            <div class="product-grid">
                {% for p in productos %}
                <div class="product-card">
                    <div class="product-icon">{{ p[4] }}</div>
                    <div class="product-name">{{ p[1] }}</div>
                    <div class="product-price">{% if p[3] > 0 %}${{ p[3] }}{% else %}GRATIS{% endif %}</div>
                    <input type="radio" name="producto" value="{{ p[1] }}" id="prod_{{ p[0] }}" style="display:none;" required>
                    <label for="prod_{{ p[0] }}" class="btn-add" onclick="selectCard(this)">AÑADIR</label>
                </div>
                {% endfor %}
            </div>

            <div class="login-card" style="margin-bottom: 15px; padding: 14px;">
                <label style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Horario de Retiro (Recreo):</label>
                <select name="recreo" class="form-control" style="margin-top: 5px;">
                    <optgroup label="Turno Mañana">
                        <option value="Mañana - 08:50 hs">☀️ 08:50 hs (1° Recreo)</option>
                        <option value="Mañana - 10:30 hs">☀️ 10:30 hs (2° Recreo)</option>
                    </optgroup>
                    <optgroup label="Turno Tarde">
                        <option value="Tarde - 14:40 hs">🌙 14:40 hs (1° Recreo)</option>
                        <option value="Tarde - 16:40 hs">🌙 16:40 hs (2° Recreo)</option>
                    </optgroup>
                </select>
                <button type="submit" class="btn-kiosk-submit">CONFIRMAR PEDIDO 🛒</button>
            </div>
        </form>

        <h2 class="section-title" style="font-size: 0.95rem;">MIS PEDIDOS REALIZADOS</h2>
        {% if mis_pedidos %}
        <ul class="order-list">
            {% for ped in mis_pedidos %}
            <li class="order-item">
                <div>
                    <strong style="font-size: 0.85rem;">{{ ped[1] }}</strong><br>
                    <small style="color: #64748b;">🕒 {{ ped[2] }}</small>
                </div>
                <span class="badge {% if 'Listo' in ped[3] %}listo{% elif 'Proceso' in ped[3] %}proceso{% else %}pendiente{% endif %}">{{ ped[3] }}</span>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p style="color: #94a3b8; font-size: 0.8rem; text-align: center; padding: 10px;">Aún no realizaste ningún pedido.</p>
        {% endif %}
    </div>
</div>

<script>
function selectCard(element) {
    document.querySelectorAll('.btn-add').forEach(btn => {
        btn.style.background = '#10b981';
        btn.innerText = 'AÑADIR';
    });
    element.style.background = '#f97316';
    element.innerText = '¡ELEGIDO!';
}
</script>
"""

HTML_ADMIN = CSS_STYLE + """
<div class="kiosk-frame" style="max-width: 600px;">
    <div class="kiosk-header">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-weight: 800; font-size: 0.85rem;">👨‍🍳 PANEL DE CONTROL KIOSKO</span>
            <a href="/"><button class="btn-logout">SALIR</button></a>
        </div>
        <h1>CONTROL DE PEDIDOS</h1>
    </div>
    
    <div class="kiosk-body">
        {% if pedidos %}
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Alumno</th>
                    <th>Producto</th>
                    <th>Recreo</th>
                    <th>Estado</th>
                    <th>Cambiar</th>
                </tr>
            </thead>
            <tbody>
                {% for p in pedidos %}
                <tr>
                    <td><strong>{{ p[1] }}</strong></td>
                    <td>{{ p[2] }}</td>
                    <td><small>{{ p[3] }}</small></td>
                    <td><span class="badge {% if 'Listo' in p[4] %}listo{% elif 'Proceso' in p[4] %}proceso{% else %}pendiente{% endif %}">{{ p[4] }}</span></td>
                    <td>
                        <form action="/actualizar_estado/{{ p[0] }}" method="POST" style="margin:0;">
                            <select name="estado" style="padding: 4px; font-size: 0.7rem; border-radius: 6px;" onchange="this.form.submit()">
                                <option value="⏳ Pendiente" {% if p[4]=='⏳ Pendiente' %}selected{% endif %}>⏳ Pendiente</option>
                                <option value="🔥 En Proceso" {% if p[4]=='🔥 En Proceso' %}selected{% endif %}>🔥 En Proceso</option>
                                <option value="✅ Listo" {% if p[4]=='✅ Listo' %}selected{% endif %}>✅ Listo</option>
                            </select>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p style="color: #64748b; font-size: 0.85rem; text-align: center; padding: 20px;">No hay pedidos pendientes en este momento.</p>
        {% endif %}
    </div>
</div>
"""

# Servidor estático directo por si la imagen está guardada en la raíz
@app.route('/<filename>')
def serve_root_file(filename):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
        return send_from_directory('.', filename)
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template_string(HTML_LOGIN)

@app.route('/login', methods=['POST'])
def login():
    nombre = request.form['nombre']
    rol = request.form['rol']
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO usuarios (nombre, rol) VALUES (?, ?)", (nombre, rol))
    conexion.commit()
    usuario_id = cursor.lastrowid
    conexion.close()
    
    if rol == 'alumno':
        return redirect(url_for('vista_cliente', usuario_id=usuario_id))
    else:
        return redirect(url_for('vista_admin'))

@app.route('/cliente/<int:usuario_id>')
def vista_cliente(usuario_id):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    
    if not usuario:
        conexion.close()
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    
    cursor.execute("SELECT id, producto, recreo, estado FROM pedidos WHERE usuario_id = ? ORDER BY id DESC", (usuario_id,))
    mis_pedidos = cursor.fetchall()
    conexion.close()
    
    return render_template_string(HTML_CLIENTE, usuario=usuario, productos=productos, mis_pedidos=mis_pedidos)

@app.route('/crear_pedido/<int:usuario_id>', methods=['POST'])
def crear_pedido(usuario_id):
    producto = request.form.get('producto', 'Pizetas')
    recreo = request.form['recreo']
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO pedidos (usuario_id, producto, recreo, estado) VALUES (?, ?, ?, '⏳ Pendiente')", 
                   (usuario_id, producto, recreo))
    conexion.commit()
    conexion.close()
    
    return redirect(url_for('vista_cliente', usuario_id=usuario_id))

@app.route('/admin')
def vista_admin():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT pedidos.id, usuarios.nombre, pedidos.producto, pedidos.recreo, pedidos.estado 
        FROM pedidos 
        JOIN usuarios ON pedidos.usuario_id = usuarios.id
        ORDER BY pedidos.id DESC
    """)
    pedidos = cursor.fetchall()
    conexion.close()
    
    return render_template_string(HTML_ADMIN, pedidos=pedidos)

@app.route('/actualizar_estado/<int:pedido_id>', methods=['POST'])
def actualizar_estado(pedido_id):
    nuevo_estado = request.form['estado']
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))
    conexion.commit()
    conexion.close()
    
    return redirect(url_for('vista_admin'))

if __name__ == '__main__':
    inicializar_bd()
    cargar_menu_kiosco()
    app.run(host='0.0.0.0', port=5000, debug=True)