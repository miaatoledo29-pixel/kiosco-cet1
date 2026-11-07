from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__, static_folder='.')
app.secret_key = 'clave_secreta_kiosco_cet1_2026'

DB_NAME = "kiosco_v2.db"

def inicializar_db():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL,
            password TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'encargado'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nombre, rol, password) VALUES (?, ?, ?)", ("admin", "encargado", "1234"))
    
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
            cantidad INTEGER DEFAULT 1,
            recreo TEXT NOT NULL,
            estado TEXT DEFAULT '⏳ Pendiente',
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    conexion.commit()
    conexion.close()

inicializar_db()

def cargar_menu_inicial():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_iniciales = [
            ("Chocotorta", "Dulces", 1000.0, "🍰"),
            ("Pancho", "Comidas", 1400.0, "🌭"),
            ("Jugo de Naranja", "Bebidas", 700.0, "🧃"),
            ("Barra de Cereal", "Snacks", 500.0, "🌾"),
            ("Tostado de Jamón y Queso", "Snacks", 1200.0, "🥪"),
            ("Pizeta individual", "Comidas", 1500.0, "🍕")
        ]
        cursor.executemany("INSERT INTO productos (nombre, categoria, precio, icono) VALUES (?, ?, ?, ?)", productos_iniciales)
        conexion.commit()
    conexion.close()

cargar_menu_inicial()

BASE_STYLE = '''
    <style>
        :root {
            --app-green: #059669;
            --app-green-dark: #047857;
            --app-bg: #f3f4f6;
            --card-bg: #ffffff;
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --border-color: #e5e7eb;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #e5e7eb;
            color: var(--text-main);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .phone-frame {
            width: 100%;
            max-width: 440px;
            background: var(--app-bg);
            min-height: 100vh;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
            position: relative;
        }
        @media (min-width: 441px) {
            .phone-frame {
                min-height: 90vh;
                border-radius: 35px;
                overflow: hidden;
                border: 10px solid #111;
            }
        }
        .app-header {
            background: var(--app-green);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .app-header img {
            width: 65px;
            height: 65px;
            object-fit: cover;
            border-radius: 50%;
            border: 2px solid white;
            background: white;
            margin-bottom: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .app-header h2 {
            margin: 0;
            font-size: 20px;
            font-weight: 600;
        }
        .app-header span {
            font-size: 12px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .logout-link {
            position: absolute;
            top: 20px;
            right: 20px;
            color: white;
            text-decoration: none;
            font-size: 13px;
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
        }
        .content-body {
            padding: 20px;
            flex: 1;
            overflow-y: auto;
            padding-bottom: 90px;
        }
        .products-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .product-card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            border: 1px solid var(--border-color);
        }
        .product-icon {
            font-size: 40px;
            margin-bottom: 8px;
        }
        .product-name {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-main);
            margin: 0 0 5px 0;
        }
        .product-price {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 10px;
        }
        .qty-input {
            width: 60px;
            padding: 6px;
            text-align: center;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            margin: 0 auto;
            background: #f9fafb;
        }
        .btn {
            background: var(--app-green);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            transition: background 0.2s;
        }
        .btn:hover { background: var(--app-green-dark); }
        .btn-danger { background: #ef4444; }
        .btn-danger:hover { background: #dc2626; }
        
        input[type="text"], input[type="password"], select {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            box-sizing: border-box;
            margin-top: 5px;
            margin-bottom: 15px;
            font-size: 14px;
            background: white;
        }
        label { font-size: 13px; font-weight: 600; color: var(--text-muted); }
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 15px;
            font-size: 13px;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            margin-top: 15px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
        }
        th { background: var(--app-green); color: white; }
    </style>
'''

@app.route('/')
def index():
    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Kiosco Escolar CET 1</title>
            {BASE_STYLE}
        </head>
        <body>
            <div class="phone-frame">
                <div class="app-header" style="padding-top: 40px;">
                    <img src="{{{{ url_for('static', filename='log.png') }}}}" alt="Logo CET 1">
                    <span>CET N° 1</span>
                    <h2>Kiosco Escolar</h2>
                </div>
                <div class="content-body" style="text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                    <p style="color: var(--text-muted); font-size: 15px; margin-bottom: 30px;">Sistema oficial de pedidos rápidos para recreos.</p>
                    <a href="/login" class="btn" style="max-width: 250px; width: 100%;">Comenzar</a>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        rol = request.form.get('rol')
        password = request.form.get('password', '')

        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()

        if rol == 'encargado':
            cursor.execute("SELECT * FROM usuarios WHERE nombre = ? AND rol = 'encargado' AND password = ?", (nombre, password))
            user = cursor.fetchone()
            if user:
                session['usuario_id'] = user[0]
                session['nombre'] = user[1]
                session['rol'] = 'encargado'
                conexion.close()
                return redirect(url_for('panel_encargado'))
            else:
                error = "Usuario o contraseña incorrectos."
        else:
            cursor.execute("SELECT * FROM usuarios WHERE nombre = ? AND rol = 'alumno'", (nombre,))
            user = cursor.fetchone()
            if not user:
                cursor.execute("INSERT INTO usuarios (nombre, rol, password) VALUES (?, 'alumno', '')", (nombre,))
                conexion.commit()
                cursor.execute("SELECT * FROM usuarios WHERE nombre = ? AND rol = 'alumno'", (nombre,))
                user = cursor.fetchone()
            
            session['usuario_id'] = user[0]
            session['nombre'] = user[1]
            session['rol'] = 'alumno'
            conexion.close()
            return redirect(url_for('menu'))

        conexion.close()

    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Iniciar Sesión - Kiosco CET 1</title>
            {BASE_STYLE}
            <script>
                function togglePassword() {{
                    var rol = document.getElementById('rol').value;
                    var passDiv = document.getElementById('password-group');
                    passDiv.style.display = (rol === 'encargado') ? 'block' : 'none';
                }}
            </script>
        </head>
        <body>
            <div class="phone-frame">
                <div class="app-header">
                    <img src="{{{{ url_for('static', filename='log.png') }}}}" alt="Logo CET 1">
                    <h2>Iniciar Sesión</h2>
                </div>
                <div class="content-body">
                    {{% if error %}}
                        <p style="color: #ef4444; text-align: center; font-weight: bold; font-size: 13px;">{{{{ error }}}}</p>
                    {{% endif %}}
                    <form method="POST">
                        <label>Tu Nombre y Apellido:</label>
                        <input type="text" name="nombre" required placeholder="Ej: María Gómez">
                        
                        <label>Seleccionar Rol:</label>
                        <select name="rol" id="rol" onchange="togglePassword()" required>
                            <option value="alumno">Alumno</option>
                            <option value="encargado">Encargado del Kiosco</option>
                        </select>

                        <div id="password-group" style="display:none;">
                            <label>Contraseña:</label>
                            <input type="password" name="password" placeholder="••••">
                        </div>

                        <button type="submit" class="btn" style="width: 100%; margin-top: 15px; border-radius: 10px;">Ingresar</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
    ''', error=error)

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if 'usuario_id' not in session or session.get('rol') != 'alumno':
        return redirect(url_for('login'))
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    mensaje = None
    if request.method == 'POST':
        recreo = request.form.get('recreo')
        usuario_id = session['usuario_id']
        
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        
        pedidos_guardados = 0
        for p in productos:
            prod_id = p[0]
            prod_nombre = p[1]
            cantidad_str = request.form.get(f'cant_{prod_id}')
            if cantidad_str and cantidad_str.isdigit():
                cantidad = int(cantidad_str)
                if cantidad > 0:
                    cursor.execute("INSERT INTO pedidos (usuario_id, producto, cantidad, recreo) VALUES (?, ?, ?, ?)", 
                                   (usuario_id, prod_nombre, cantidad, recreo))
                    pedidos_guardados += 1
        
        if pedidos_guardados > 0:
            conexion.commit()
            mensaje = "¡Pedido realizado con éxito!"
        else:
            mensaje = "Seleccioná al menos un producto indicando su cantidad."

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    cursor.execute("SELECT producto, cantidad, recreo, estado FROM pedidos WHERE usuario_id = ? ORDER BY id DESC", (session['usuario_id'],))
    mis_pedidos = cursor.fetchall()
    conexion.close()

    products_html = ""
    for p in productos:
        products_html += f'''
            <div class="product-card">
                <div class="product-icon">{p[4]}</div>
                <div>
                    <div class="product-name">{p[1]}</div>
                    <div class="product-price">${p[3]}</div>
                </div>
                <input type="number" name="cant_{p[0]}" min="0" value="0" class="qty-input">
            </div>
        '''

    historial_html = ""
    for mp in mis_pedidos:
        historial_html += f'''
            <tr>
                <td>{mp[0]}</td>
                <td style="text-align: center; font-weight: bold;">{mp[1]}</td>
                <td>{mp[2]}</td>
                <td><b>{mp[3]}</b></td>
            </tr>
        '''

    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Kiosco Escolar</title>
            {BASE_STYLE}
        </head>
        <body>
            <div class="phone-frame">
                <div class="app-header">
                    <a href="/logout" class="logout-link">Salir</a>
                    <img src="{{{{ url_for('static', filename='log.png') }}}}" alt="Logo CET 1">
                    <h2>Kiosco Escolar</h2>
                    <span style="font-size: 11px;">Hola, {{{{ session['nombre'] }}}}</span>
                </div>

                <div class="content-body">
                    {{% if mensaje %}}
                        <div class="alert-success">{{{{ mensaje }}}}</div>
                    {{% endif %}}

                    <form method="POST" id="order-form">
                        <p style="font-weight: 600; font-size: 14px; margin-top: 0; color: var(--text-main);">Menú Disponible:</p>
                        <div class="products-grid">
                            {products_html}
                        </div>

                        <div style="background: white; padding: 15px; border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 20px;">
                            <label>Recreo de Retiro:</label>
                            <select name="recreo" required style="margin-bottom: 0;">
                                <option value="10:00 hs">10:00 hs (Primer Recreo)</option>
                                <option value="11:30 hs">11:30 hs (Segundo Recreo)</option>
                            </select>
                        </div>

                        <button type="submit" class="btn" style="width: 100%; border-radius: 12px; padding: 14px; font-size: 15px; margin-bottom: 20px;">Finalizar Compra / Pedido</button>
                    </form>

                    <h3 style="font-size: 15px; color: var(--text-main); margin-top: 25px;">Mis Pedidos Activos</h3>
                    <table>
                        <tr>
                            <th>Producto</th>
                            <th style="text-align: center;">Cant.</th>
                            <th>Recreo</th>
                            <th>Estado</th>
                        </tr>
                        {historial_html if historial_html else '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No tenés pedidos aún.</td></tr>'}
                    </table>
                </div>
            </div>
        </body>
        </html>
    ''', mensaje=mensaje)

@app.route('/cambiar_estado/<int:pedido_id>', methods=['POST'])
def cambiar_estado(pedido_id):
    if 'usuario_id' not in session or session.get('rol') != 'encargado':
        return redirect(url_for('login'))
    
    nuevo_estado = request.form.get('estado')
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))
    conexion.commit()
    conexion.close()
    return redirect(url_for('panel_encargado'))

@app.route('/pedidos')
def panel_encargado():
    if 'usuario_id' not in session or session.get('rol') != 'encargado':
        return redirect(url_for('login'))

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT pedidos.id, usuarios.nombre, pedidos.producto, pedidos.cantidad, pedidos.recreo, pedidos.estado 
        FROM pedidos 
        JOIN usuarios ON pedidos.usuario_id = usuarios.id
        ORDER BY pedidos.id DESC
    ''')
    pedidos = cursor.fetchall()
    conexion.close()

    pedidos_html = ""
    for ped in pedidos:
        estado_actual = ped[5]
        if "Pendiente" in estado_actual:
            siguiente_estado_btn = f'''
                <form action="/cambiar_estado/{ped[0]}" method="POST" style="margin:0;">
                    <input type="hidden" name="estado" value="✅ Listo para retirar">
                    <button type="submit" class="btn" style="padding: 6px 12px; font-size: 11px; border-radius: 6px;">Marcar Listo</button>
                </form>
            '''
        else:
            siguiente_estado_btn = f'''
                <form action="/cambiar_estado/{ped[0]}" method="POST" style="margin:0;">
                    <input type="hidden" name="estado" value="⏳ Pendiente">
                    <button type="submit" class="btn btn-danger" style="padding: 6px 12px; font-size: 11px; border-radius: 6px;">Marcar Pendiente</button>
                </form>
            '''

        pedidos_html += f'''
            <tr>
                <td><b>{ped[1]}</b></td>
                <td>{ped[2]} ({ped[3]})</td>
                <td>{ped[4]}</td>
                <td><b>{ped[5]}</b></td>
                <td style="text-align: center;">{siguiente_estado_btn}</td>
            </tr>
        '''

    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Panel Encargado - Kiosco</title>
            {BASE_STYLE}
        </head>
        <body>
            <div class="phone-frame" style="max-width: 600px;">
                <div class="app-header">
                    <a href="/logout" class="logout-link">Salir</a>
                    <img src="{{{{ url_for('static', filename='log.png') }}}}" alt="Logo CET 1">
                    <h2>Panel de Encargado</h2>
                    <span style="font-size: 11px;">Administración de Pedidos</span>
                </div>
                <div class="content-body">
                    <table>
                        <tr>
                            <th>Alumno</th>
                            <th>Prod. (Cant)</th>
                            <th>Recreo</th>
                            <th>Estado</th>
                            <th style="text-align: center;">Acción</th>
                        </tr>
                        {pedidos_html if pedidos_html else '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No hay pedidos registrados.</td></tr>'}
                    </table>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)