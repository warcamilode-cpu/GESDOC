# 🐧 GUÍA DE INSTALACIÓN – UBUNTU SERVER 22.04 LTS
## GestDoc v2.0 – Desde instalación base hasta sistema funcionando
### Administración: SSH desde Windows + Webmin

---

## ANTES DE EMPEZAR – LO QUE NECESITAS TENER A MANO

- El PC con Ubuntu Server 22.04 encendido y conectado a la red local por cable
- Tu PC con Windows desde donde vas a administrar
- Un cable de red (no WiFi para el servidor, siempre cable)
- La contraseña que pusiste durante la instalación de Ubuntu
- Papel y lápiz para anotar IPs y contraseñas

---

## FASE 1 – PREPARAR EL ACCESO REMOTO DESDE WINDOWS

Esta fase la haces **directamente frente al servidor** (con teclado y monitor conectados).
Después de esto ya no necesitas estar físicamente frente a él.

---

### PASO 1 – Averiguar la IP del servidor

Escribe en el servidor:

```bash
ip addr show
```

Busca la sección de tu adaptador de red (normalmente `eth0` o `ens33`).
Verás algo como:

```
inet 192.168.1.105/24
```

Ese número **192.168.1.105** es la IP de tu servidor. **Anótala**, la vas a usar siempre.

---

### PASO 2 – Asignar IP fija al servidor

Por defecto Ubuntu obtiene la IP automáticamente del router (DHCP), lo que significa
que puede cambiar y perder la conexión. Vamos a fijarla permanentemente.

```bash
sudo nano /etc/netplan/00-installer-config.yaml
```

Borra todo el contenido y escribe esto (ajusta los valores a tu red):

```yaml
network:
  version: 2
  ethernets:
    eth0:                          # Cambia por tu adaptador (el que viste en ip addr)
      dhcp4: no
      addresses:
        - 192.168.1.105/24         # La IP que quieres fijar
      routes:
        - to: default
          via: 192.168.1.1         # La IP de tu router (gateway)
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

> **¿Cómo saber la IP de tu router?** Ejecuta `ip route | grep default`
> y verás algo como `default via 192.168.1.1`

Guarda con `Ctrl+O`, Enter, `Ctrl+X` para salir.

Aplica la configuración:

```bash
sudo netplan apply
```

Verifica que la IP quedó fija:
```bash
ip addr show
```

---

### PASO 3 – Instalar y verificar SSH

En Ubuntu Server 22.04 el SSH generalmente ya viene instalado. Verifica:

```bash
sudo systemctl status ssh
```

Si dice `active (running)` ya está listo. Si no está instalado:

```bash
sudo apt update
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

### PASO 4 – Conectarte desde tu PC Windows por SSH

Desde este punto **ya no necesitas estar frente al servidor**. Trabaja desde Windows.

**Opción A – Usando CMD o PowerShell de Windows (recomendado, ya viene instalado):**

Abre CMD en tu PC Windows y escribe:

```cmd
ssh tu_usuario@192.168.1.105
```

La primera vez te preguntará:
```
Are you sure you want to continue connecting? (yes/no)
```
Escribe `yes` y presiona Enter. Luego ingresa tu contraseña de Ubuntu.

**Opción B – Usando PuTTY (si prefieres interfaz gráfica):**

1. Descarga PuTTY: https://www.putty.org/
2. Instala y abre PuTTY
3. En **Host Name**: `192.168.1.105`
4. **Port**: `22`
5. **Connection type**: SSH
6. Haz clic en **Open**
7. Ingresa tu usuario y contraseña de Ubuntu

Ya estás dentro del servidor desde Windows. Todo lo que sigue lo haces desde aquí.

---

## FASE 2 – INSTALACIÓN DE COMPONENTES BASE

Todos estos comandos los ejecutas **desde tu SSH en Windows**.

---

### PASO 5 – Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

Esto puede tardar varios minutos dependiendo de las actualizaciones pendientes.
Si te pregunta sobre reinicios de servicios, presiona Enter para aceptar los valores por defecto.

---

### PASO 6 – Instalar herramientas esenciales

```bash
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    nano \
    net-tools \
    ufw \
    software-properties-common
```

---

### PASO 7 – Instalar Python 3.11

Ubuntu 22.04 trae Python 3.10 por defecto. Instalaremos 3.11 para mayor compatibilidad:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

Verifica:
```bash
python3.11 --version
```

Debe mostrar: `Python 3.11.x`

---

### PASO 8 – Instalar MySQL 8.0

```bash
sudo apt install -y mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

**Asegurar la instalación:**

```bash
sudo mysql_secure_installation
```

Responde así a cada pregunta:

```
Would you like to setup VALIDATE PASSWORD component?  → N (No)
New password:                                          → Escribe una contraseña segura (anótala)
Re-enter new password:                                 → Repite la contraseña
Remove anonymous users?                                → Y
Disallow root login remotely?                          → Y
Remove test database?                                  → Y
Reload privilege tables?                               → Y
```

**Crear el usuario y la base de datos para GestDoc:**

```bash
sudo mysql -u root -p
```

Ingresa la contraseña de root que acabas de crear. Luego ejecuta:

```sql
CREATE DATABASE gestion_documental
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER 'gestdoc'@'localhost' IDENTIFIED BY 'GestDocDB2024!';

GRANT ALL PRIVILEGES ON gestion_documental.* TO 'gestdoc'@'localhost';

FLUSH PRIVILEGES;

EXIT;
```

**Importar el esquema:**

Primero copia el archivo `database.sql` al servidor. Desde tu PC Windows
abre otro CMD (no el que tiene el SSH) y ejecuta:

```cmd
scp C:\GestDoc\database.sql tu_usuario@192.168.1.105:/home/tu_usuario/
```

Regresa al CMD con SSH y ejecuta:

```bash
mysql -u gestdoc -p gestion_documental < ~/database.sql
```

Ingresa la contraseña `GestDocDB2024!`

Verifica que se importó:
```bash
mysql -u gestdoc -p gestion_documental -e "SHOW TABLES;"
```

Debes ver la lista de todas las tablas del sistema.

---

### PASO 9 – Instalar Redis

```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

Verifica:
```bash
redis-cli ping
```

Debe responder: **PONG**

**Configuración de seguridad básica para Redis:**

```bash
sudo nano /etc/redis/redis.conf
```

Busca y modifica estas líneas:

```
# Cambiar esto:
bind 127.0.0.1 -::1

# Por esto (solo escucha localmente, más seguro):
bind 127.0.0.1
```

Guarda y reinicia:
```bash
sudo systemctl restart redis-server
```

---

### PASO 10 – Instalar LibreOffice (para exportar PDF)

```bash
sudo apt install -y libreoffice --no-install-recommends
```

> `--no-install-recommends` instala solo lo necesario sin la interfaz gráfica,
> ahorrando espacio en el servidor.

Verifica:
```bash
libreoffice --version
```

---

## FASE 3 – INSTALAR Y CONFIGURAR GESTDOC

---

### PASO 11 – Copiar el proyecto al servidor

Desde tu PC Windows (en un CMD nuevo, no el SSH):

```cmd
scp -r C:\GestDoc\servidor tu_usuario@192.168.1.105:/opt/gestdoc/
scp -r C:\GestDoc\cliente  tu_usuario@192.168.1.105:/opt/gestdoc/
```

O si tienes el proyecto en un ZIP:
```cmd
scp C:\GestDoc\gestdoc.zip tu_usuario@192.168.1.105:/home/tu_usuario/
```

Y en el SSH del servidor:
```bash
sudo mkdir -p /opt/gestdoc
sudo unzip ~/gestdoc.zip -d /opt/gestdoc/
```

Crear directorios necesarios:
```bash
sudo mkdir -p /opt/gestdoc/servidor/plantillas_base
sudo mkdir -p /opt/gestdoc/servidor/temp
sudo mkdir -p /opt/gestdoc/logs
sudo mkdir -p /var/backups/gestdoc
```

---

### PASO 12 – Crear entorno virtual e instalar dependencias

```bash
cd /opt/gestdoc
sudo python3.11 -m venv venv
source venv/bin/activate
```

Debes ver `(venv)` al inicio de la línea.

```bash
pip install --upgrade pip

pip install \
    fastapi==0.111.0 \
    "uvicorn[standard]==0.29.0" \
    sqlalchemy==2.0.30 \
    pymysql==1.1.0 \
    "passlib[bcrypt]==1.7.4" \
    "python-jose[cryptography]==3.3.0" \
    redis==5.0.4 \
    python-docx==1.1.2 \
    docx2pdf==0.1.8 \
    python-multipart==0.0.9 \
    aiofiles==23.2.1
```

---

### PASO 13 – Configurar el sistema

**Configurar la base de datos** (`/opt/gestdoc/servidor/database.py`):

```bash
nano /opt/gestdoc/servidor/database.py
```

```python
DB_USUARIO   = "gestdoc"
DB_PASSWORD  = "GestDocDB2024!"    # La que creaste
DB_HOST      = "localhost"
DB_PUERTO    = "3306"
DB_NOMBRE    = "gestion_documental"
```

**Generar y configurar claves secretas** (`/opt/gestdoc/servidor/auth.py`):

```bash
# Generar dos claves únicas
python3 -c "import secrets; print(secrets.token_hex(32))"
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copia cada clave y pégala en el archivo:

```bash
nano /opt/gestdoc/servidor/auth.py
```

```python
SECRET_KEY         = "pega_aqui_primera_clave_generada"
REFRESH_SECRET_KEY = "pega_aqui_segunda_clave_generada"
```

---

### PASO 14 – Probar el servidor manualmente

```bash
cd /opt/gestdoc/servidor
source /opt/gestdoc/venv/bin/activate
python main.py
```

Desde tu PC Windows abre Chrome y ve a:
```
http://192.168.1.105:8000/docs
```

Si ves la documentación de la API, **el servidor funciona correctamente**.

Detén el servidor con `Ctrl+C` y continúa.

---

### PASO 15 – Crear el servicio del sistema (systemd)

Para que GestDoc arranque automáticamente con Ubuntu:

```bash
sudo nano /etc/systemd/system/gestdoc.service
```

Pega este contenido (cambia `tu_usuario` por tu usuario real de Ubuntu):

```ini
[Unit]
Description=GestDoc - Sistema de Gestión Documental
Documentation=http://localhost:8000/docs
After=network.target mysql.service redis-server.service
Wants=mysql.service redis-server.service

[Service]
Type=simple
User=tu_usuario
Group=tu_usuario
WorkingDirectory=/opt/gestdoc/servidor
ExecStart=/opt/gestdoc/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=append:/opt/gestdoc/logs/gestdoc.log
StandardError=append:/opt/gestdoc/logs/gestdoc_error.log
Environment="PYTHONPATH=/opt/gestdoc/servidor"

[Install]
WantedBy=multi-user.target
```

Activa e inicia el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gestdoc
sudo systemctl start gestdoc
```

Verifica que esté corriendo:

```bash
sudo systemctl status gestdoc
```

Debe mostrar `● gestdoc.service` con `Active: active (running)` en verde.

---

### PASO 16 – Configurar el Firewall

```bash
sudo ufw allow OpenSSH           # SSH – nunca lo bloquees o perderás acceso
sudo ufw allow 8000/tcp          # API GestDoc
sudo ufw allow 10000/tcp         # Webmin (lo instalaremos ahora)
sudo ufw enable
```

Te preguntará confirmación, escribe `y`.

Verifica:
```bash
sudo ufw status
```

---

## FASE 4 – INSTALAR WEBMIN (Panel de administración web)

Webmin te da una interfaz gráfica en el navegador para administrar el servidor
sin necesidad de recordar comandos. Muy útil para ver servicios, logs y archivos.

---

### PASO 17 – Instalar Webmin

```bash
curl -o setup-repos.sh https://raw.githubusercontent.com/webmin/webmin/master/setup-repos.sh
sudo sh setup-repos.sh
sudo apt install -y webmin
```

Verifica que arrancó:
```bash
sudo systemctl status webmin
```

---

### PASO 18 – Acceder a Webmin desde Windows

Abre Chrome o Edge en tu PC Windows y ve a:

```
https://192.168.1.105:10000
```

> **Nota:** El navegador dirá que la conexión no es segura (certificado
> autofirmado). Haz clic en **"Advanced"** → **"Proceed to 192.168.1.105"**.
> Es completamente normal en redes locales.

Ingresa con:
- **Username:** tu usuario de Ubuntu
- **Password:** tu contraseña de Ubuntu

Ya tienes el panel de administración web.

**Lo más útil de Webmin para tu día a día:**

Desde el menú lateral puedes acceder a:
- **System → Bootup and Shutdown** → Ver y controlar servicios (gestdoc, mysql, redis)
- **System → System Logs** → Ver logs del sistema y de GestDoc
- **Tools → File Manager** → Explorador de archivos del servidor
- **Tools → Terminal** → Terminal web (alternativa al SSH)
- **Hardware → Disk and Network Filesystems** → Ver espacio en disco

---

## FASE 5 – CONFIGURAR BACKUPS AUTOMÁTICOS

### PASO 19 – Script de backup

```bash
sudo nano /opt/gestdoc/scripts/backup.sh
```

```bash
#!/bin/bash
# ── GestDoc Backup Automático ─────────────────────────────────
FECHA=$(date +%Y%m%d_%H%M%S)
RUTA=/var/backups/gestdoc
LOG=/opt/gestdoc/logs/backup.log

mkdir -p $RUTA

echo "[$FECHA] Iniciando backup..." >> $LOG

# Backup de la base de datos
mysqldump -u gestdoc -pGestDocDB2024! gestion_documental \
    | gzip > $RUTA/db_$FECHA.sql.gz

if [ $? -eq 0 ]; then
    echo "[$FECHA] OK - BD: db_$FECHA.sql.gz" >> $LOG
else
    echo "[$FECHA] ERROR - Falló backup de BD" >> $LOG
fi

# Backup de plantillas
tar -czf $RUTA/plantillas_$FECHA.tar.gz \
    /opt/gestdoc/servidor/plantillas_base/ 2>/dev/null

echo "[$FECHA] OK - Plantillas guardadas" >> $LOG

# Limpiar temporales del servidor (más de 1 día)
find /opt/gestdoc/servidor/temp -type f -mtime +1 -delete
echo "[$FECHA] OK - Temporales limpiados" >> $LOG

# Eliminar backups con más de 30 días
find $RUTA -name "*.sql.gz" -mtime +30 -delete
find $RUTA -name "*.tar.gz" -mtime +30 -delete
echo "[$FECHA] OK - Backups antiguos eliminados" >> $LOG

echo "[$FECHA] Backup completado exitosamente" >> $LOG
```

```bash
sudo chmod +x /opt/gestdoc/scripts/backup.sh
```

**Programar con Cron (todos los días a las 2:00 AM):**

```bash
sudo crontab -e
```

Agrega esta línea al final:

```cron
0 2 * * * /opt/gestdoc/scripts/backup.sh
```

---

## FASE 6 – INSTALAR EL CLIENTE EN LAS PCS DE USUARIOS (Windows)

### PASO 20 – En cada PC de usuario (Windows)

1. Instala Python 3.11 desde python.org
   → **Marca "Add Python to PATH"**

2. Instala las dependencias:
   ```cmd
   pip install PyQt5 requests websocket-client
   ```

3. Copia la carpeta `cliente` al PC del usuario

4. Edita `api_client.py`:
   ```python
   BASE_URL = "http://192.168.1.105:8000"  # IP de tu servidor Ubuntu
   ```

5. Crea un acceso directo a `iniciar_cliente.bat` en el escritorio

---

## VERIFICACIÓN FINAL COMPLETA

Ejecuta este checklist en orden. Todos deben pasar:

```bash
# 1. MySQL corriendo
sudo systemctl is-active mysql
# → Debe decir: active

# 2. Redis corriendo
sudo systemctl is-active redis-server
redis-cli ping
# → Debe decir: active / PONG

# 3. GestDoc corriendo
sudo systemctl is-active gestdoc
# → Debe decir: active

# 4. API respondiendo
curl http://localhost:8000/salud
# → Debe mostrar: {"estado":"operativo","version":"2.0.0",...}

# 5. Webmin corriendo
sudo systemctl is-active webmin
# → Debe decir: active

# 6. Firewall activo
sudo ufw status
# → Debe mostrar los puertos 22, 8000, 10000 como ALLOW
```

**Desde tu PC Windows (en el navegador):**
```
http://192.168.1.105:8000/salud  → Debe responder con JSON
http://192.168.1.105:8000/docs   → Documentación de la API
https://192.168.1.105:10000      → Panel Webmin
```

---

## COMANDOS DE USO DIARIO

Estos son los que más vas a usar por SSH o desde Webmin:

```bash
# Ver estado de todos los servicios de una vez
sudo systemctl status gestdoc mysql redis-server

# Reiniciar el servidor de la API (tras cambios de código)
sudo systemctl restart gestdoc

# Ver logs en tiempo real
sudo journalctl -u gestdoc -f

# Ver los últimos 50 errores
sudo journalctl -u gestdoc -n 50 --no-pager

# Ver uso de recursos
htop

# Ver espacio en disco
df -h

# Hacer backup manual
sudo /opt/gestdoc/scripts/backup.sh
```

---

## RESUMEN FINAL DE LA ARQUITECTURA

```
Tu PC Windows (192.168.1.X)
│
│  SSH (puerto 22)  ──────────────────────────┐
│  Webmin (puerto 10000)  ────────────────────┤
│  API desde clientes (puerto 8000)  ─────────┤
│                                             │
└─────────────────────────────────────────────▼
                Ubuntu Server 22.04 (192.168.1.105)
                │
                ├── MySQL 8.0        (puerto 3306, solo local)
                ├── Redis Server     (puerto 6379, solo local)
                ├── FastAPI/Uvicorn  (puerto 8000, red local)
                ├── Webmin           (puerto 10000, red local)
                └── Nginx            (opcional, para producción avanzada)

Clientes (PCs de usuarios, Windows)
│
└── PyQt5 → HTTP → API (puerto 8000)
         → WebSocket → Notificaciones en tiempo real
```

---

*GestDoc v2.0 – Guía Ubuntu Server 22.04 LTS*
*Tiempo estimado de instalación completa: 45-90 minutos*
