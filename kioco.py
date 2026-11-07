from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__, static_folder='.')
app.secret_key = 'clave_secreta_kiosco_cet1'

DB_NAME = "cet_kiosco.db"

def inicializar_db():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Tabla de usuarios con soporte para contraseña
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL,
            password TEXT
        )
    ''')
    
    # Crear un encargado por defecto si no existe (Usuario: admin, Clave: 1234)
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
    
    # Tabla de pedidos
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

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Kiosco CET N° 1</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f6f9; text-align: center; padding: 50px; }
                .card { background: white; max-width: 400px; margin: auto; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                a { display: block; background: #007bff; color: white; padding: 12px; margin-top: 15px; text-decoration: none; border-radius: 5px; font-weight: bold; }
                a:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Kiosco CET N° 1</h1>
                <p>Sistema de gestión y pedidos</p>
                <a href="/login">Ingresar al Sistema</a>
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
                error = "Nombre de encargado o contraseña incorrectos."
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

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Login - Kiosco CET 1</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 300px; }
                input, select, button { width: 100%; padding: 10px; margin-top: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
                button { background: #28a745; color: white; font-weight: bold; border: none; cursor: pointer; }
                button:hover { background: #218838; }
                .error { color: red; font-size: 14px; text-align: center; }
            </style>
            <script>
                function togglePassword() {
                    var rol = document.getElementById('rol').value;
                    var passDiv = document.getElementById('password-group');
                    if (rol === 'encargado') {
                        passDiv.style.display = 'block';
                    } else {
                        passDiv.style.display = 'none';
                    }
                }
            </script>
        </head>
        <body>
            <div class="box">
                <h2>Iniciar Sesión</h2>
                {% if error %}
                    <p class="error">{{ error }}</p>
                {% endif %}
                <form method="POST">
                    <label>Nombre:</label>
                    <input type="text" name="nombre" required placeholder="Tu nombre">
                    
                    <label>Rol:</label>
                    <select name="rol" id="rol" onchange="togglePassword()" required>
                        <option value="alumno">Alumno</option>
                        <option value="encargado">Encargado del Kiosco</option>
                    </select>

                    <div id="password-group" style="display:none;">
                        <label>Contraseña de Encargado:</label>
                        <input type="password" name="password" placeholder="Contraseña secreta">
                    </div>

                    <button type="submit">Ingresar</button>
                </form>
            </div>
        </body>
        </html>
    ''', error=error)

@app.route('/menu')
def menu():
    if 'usuario_id' not in session or session.get('rol') != 'alumno':
        return redirect(url_for('login'))
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conexion.close()

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Menú Kiosco</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f6f9; padding: 20px; text-align: center; }
                h1 { color: #333; }
                .logout { background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; float: right; }
            </style>
        </head>
        <body>
            <a href="/logout" class="logout">Cerrar Sesión</a>
            <h1>Bienvenido/a, {{ session['nombre'] }} (Alumno)</h1>
            <p>Acá podés ver el menú y hacer tus pedidos.</p>
            <ul>
                {% for p in productos %}
                    <li>{{ p[4] }} {{ p[1] }} - ${{ p[3] }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
    ''', productos=productos)

@app.route('/pedidos')
def panel_encargado():
    if 'usuario_id' not in session or session.get('rol') != 'encargado':
        return redirect(url_for('login'))

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT pedidos.id, usuarios.nombre, pedidos.producto, pedidos.recreo, pedidos.estado 
        FROM pedidos 
        JOIN usuarios ON pedidos.usuario_id = usuarios.id
    ''')
    pedidos = cursor.fetchall()
    conexion.close()

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Panel de Encargado - Pedidos</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f6f9; padding: 20px; }
                h1 { color: #333; text-align: center; }
                table { width: 100%; border-collapse: collapse; background: white; margin-top: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #007bff; color: white; }
                .logout { background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; float: right; }
            </style>
        </head>
        <body>
            <a href="/logout" class="logout">Cerrar Sesión</a>
            <h1>Panel de Control - Pedidos del Kiosco</h1>
            <p>Hola, <b>{{ session['nombre'] }}</b> (Encargado autorizado).</p>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Alumno</th>
                    <th>Producto</th>
                    <th>Recreo</th>
                    <th>Estado</th>
                </tr>
                {% for ped in pedidos %}
                <tr>
                    <td>{{ ped[0] }}</td>
                    <td>{{ ped[1] }}</td>
                    <td>{{ ped[2] }}</td>
                    <td>{{ ped[3] }}</td>
                    <td>{{ ped[4] }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" style="text-align: center;">No hay pedidos registrados todavía.</td>
                </tr>
                {% endfor %}
            </table>
        </body>
        </html>
    ''', pedidos=pedidos)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)