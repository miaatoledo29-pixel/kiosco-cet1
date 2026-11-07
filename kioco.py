from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__, static_folder='.')
app.secret_key = 'clave_secreta_kiosco_cet1_2026'

DB_NAME = "cet_kiosco.db"

def inicializar_db():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL,
            password TEXT
        )
    ''')
    
    # Crear encargado por defecto (admin / 1234)
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'encargado'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nombre, rol, password) VALUES (?, ?, ?)", ("admin", "encargado", "1234"))
    
    # Tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            icono TEXT NOT NULL
        )
    ''')
    
    # Tabla de pedidos con columna cantidad y estado dinámico
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
            ("Tostado de Jamón y Queso", "Snacks", 1200.0, "🥪"),
            ("Pizeta individual", "Comidas", 1500.0, "🍕"),
            ("Alfajor regional", "Dulces", 800.0, "🍫"),
            ("Cereal bar", "Snacks", 500.0, "🌾"),
            ("Jugo en cajita", "Bebidas", 700.0, "🧃")
        ]
        cursor.executemany("INSERT INTO productos (nombre, categoria, precio, icono) VALUES (?, ?, ?, ?)", productos_iniciales)
        conexion.commit()
    conexion.close()

cargar_menu_inicial()

# ESTILOS CSS GENERALES (Estética moderna e institucional)
BASE_STYLE = '''
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-hover: #1e40af;
            --accent: #10b981;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #334155;
            --border: #cbd5e1;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: var(--card-bg);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        .header-logo {
            text-align: center;
            margin-bottom: 25px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 15px;
        }
        .header-logo h2 {
            margin: 5px 0 0;
            color: var(--primary);
            font-size: 22px;
        }
        .header-logo span {
            font-size: 14px;
            color: #64748b;
            font-weight: 600;
            letter-spacing: 1px;
        }
        h1, h3 { color: var(--primary); text-align: center; }
        .btn {
            display: inline-block;
            background: var(--primary);
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            border: none;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:hover { background: var(--primary-hover); }
        .btn-success { background: var(--accent); }
        .btn-success:hover { background: #059669; }
        .btn-danger { background: #ef4444; }
        .btn-danger:hover { background: #dc2626; }
        .logout { float: right; font-size: 13px; padding: 6px 12px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th { background: var(--primary); color: white; font-size: 14px; }
        tr:hover { background: #f1f5f9; }
        input, select {
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 6px;
            width: 100%;
            box-sizing: border-box;
            margin-top: 5px;
            margin-bottom: 15px;
        }
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
        }
    </style>
'''

@app.route('/')
def index():
    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Kiosco CET N° 1</title>
            {BASE_STYLE}
        </head>
        <body>
            <div class="container" style="max-width: 400px; text-align: center; margin-top: 60px;">
                <div class="header-logo">
                    <span>🏫 CET N° 1</span>
                    <h2>Kiosco Escolar</h2>
                </div>
                <p>Sistema oficial de reservas y gestión</p>
                <br>
                <a href="/login" class="btn" style="width: 100%; box-sizing: border-box;">Ingresar al Sistema</a>
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
                error = "Usuario o contraseña de encargado incorrectos."
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
            <title>Login - Kiosco CET 1</title>
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
            <div class="container" style="max-width: 380px; margin-top: 50px;">
                <div class="header-logo">
                    <span>🏫 CET N° 1</span>
                    <h2>Iniciar Sesión</h2>
                </div>
                {{% if error %}}
                    <p style="color: #ef4444; text-align: center; font-weight: bold;">{{{{ error }}}}</p>
                {{% endif %}}
                <form method="POST">
                    <label><b>Nombre / Apellido:</b></label>
                    <input type="text" name="nombre" required placeholder="Ej: Juan Pérez">
                    
                    <label><b>Rol:</b></label>
                    <select name="rol" id="rol" onchange="togglePassword()" required>
                        <option value="alumno">Alumno</option>
                        <option value="encargado">Encargado del Kiosco</option>
                    </select>

                    <div id="password-group" style="display:none;">
                        <label><b>Contraseña de Encargado:</b></label>
                        <input type="password" name="password" placeholder="••••">
                    </div>

                    <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">Ingresar</button>
                </form>
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
            mensaje = "¡Tus pedidos fueron enviados con éxito!"
        else:
            mensaje = "Por favor, seleccioná al menos un producto indicando su cantidad."

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    # Historial de pedidos del alumno actual
    cursor.execute("SELECT producto, cantidad, recreo, estado FROM pedidos WHERE usuario_id = ? ORDER BY id DESC", (session['usuario_id'],))
    mis_pedidos = cursor.fetchall()
    conexion.close()

    productos_html = ""
    for p in productos:
        productos_html += f'''
            <tr>
                <td style="font-size: 22px; width: 40px; text-align: center;">{p[4]}</td>
                <td>
                    <b>{p[1]}</b><br>
                    <small style="color: #64748b;">{p[2]} • ${p[3]}</small>
                </td>
                <td style="width: 100px;">
                    <input type="number" name="cant_{p[0]}" min="0" value="0" style="margin: 0; text-align: center; font-weight: bold;">
                </td>
            </tr>
        '''

    historial_html = ""
    for mp in mis_pedidos:
        historial_html += f'''
            <tr>
                <td>{mp[0]}</td>
                <td style="text-align: center;"><b>{mp[1]}</b></td>
                <td>{mp[2]}</td>
                <td><span style="font-weight: bold;">{mp[3]}</span></td>
            </tr>
        '''

    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Menú - Kiosco CET 1</title>
            {BASE_STYLE}
        </head>
        <body>
            <div class="container">
                <a href="/logout" class="btn btn-danger logout">Cerrar Sesión</a>
                <div class="header-logo">
                    <span>🏫 CET N° 1 - Menú Escolar</span>
                    <h2>Bienvenido/a, {{{{ session['nombre'] }}}}</h2>
                </div>

                {{% if mensaje %}}
                    <div class="alert-success">{{{{ mensaje }}}}</div>
                {{% endif %}}

                <form method="POST">
                    <h3>Seleccioná tus productos y cantidades</h3>
                    <table>
                        <tr>
                            <th colspan="2">Producto</th>
                            <th style="text-align: center;">Cantidad</th>
                        </tr>
                        {productos_html}
                    </table>

                    <div style="margin-top: 20px;">
                        <label><b>Seleccionar Recreo de Retiro:</b></label>
                        <select name="recreo" required>
                            <option value="10:00 hs">10:00 hs (Primer Recreo)</option>
                            <option value="11:30 hs">11:30 hs (Segundo Recreo)</option>
                        </select>
                    </div>

                    <button type="submit" class="btn btn-success" style="width: 100%; font-size: 16px; margin-top: 10px;">Enviar Pedidos</button>
                </form>

                <h3 style="margin-top: 40px;">Mis Pedidos Realizados</h3>
                <table>
                    <tr>
                        <th>Producto</th>
                        <th style="text-align: center;">Cant.</th>
                        <th>Recreo</th>
                        <th>Estado</th>
                    </tr>
                    {historial_html if historial_html else '<tr><td colspan="4" style="text-align: center; color: #64748b;">No tenés pedidos activos.</td></tr>'}
                </table>
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
        # Botones para alternar el estado
        siguiente_estado_btn = ""
        if "Pendiente" in estado_actual:
            siguiente_estado_btn = f'''
                <form action="/cambiar_estado/{ped[0]}" method="POST" style="margin:0;">
                    <input type="hidden" name="estado" value="✅ Listo para retirar">
                    <button type="submit" class="btn btn-success" style="padding: 5px 10px; font-size: 12px;">Marcar Listo</button>
                </form>
            '''
        else:
            siguiente_estado_btn = f'''
                <form action="/cambiar_estado/{ped[0]}" method="POST" style="margin:0;">
                    <input type="hidden" name="estado" value="⏳ Pendiente">
                    <button type="submit" class="btn btn-danger" style="padding: 5px 10px; font-size: 12px;">Marcar Pendiente</button>
                </form>
            '''

        pedidos_html += f'''
            <tr>
                <td>#{ped[0]}</td>
                <td><b>{ped[1]}</b></td>
                <td>{ped[2]}</td>
                <td style="text-align: center; font-weight: bold;">{ped[3]}</td>
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
            <title>Panel Encargado - Kiosco CET 1</title>
            {BASE_STYLE}
        </head>
        <body>
            <div class="container" style="max-width: 1000px;">
                <a href="/logout" class="btn btn-danger logout">Cerrar Sesión</a>
                <div class="header-logo">
                    <span>🏫 CET N° 1 - Panel de Gestión</span>
                    <h2>Panel de Control de Pedidos</h2>
                </div>
                <p>Encargado autorizado: <b>{{{{ session['nombre'] }}}}</b></p>
                
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Alumno</th>
                        <th>Producto</th>
                        <th style="text-align: center;">Cant.</th>
                        <th>Recreo</th>
                        <th>Estado Actual</th>
                        <th style="text-align: center;">Acción</th>
                    </tr>
                    {pedidos_html if pedidos_html else '<tr><td colspan="7" style="text-align: center; color: #64748b;">No hay pedidos registrados.</td></tr>'}
                </table>
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