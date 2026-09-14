# 💻 PC Status - Monitoreo y Control Remoto para PC y Celular

**PC Status** es una solución completa, ultra ligera (< 15MB RAM, < 0.5% CPU) y sumamente segura para monitorear en tiempo real la salud de tu computadora desde tu teléfono celular a través de **4G/5G o redes Wi-Fi remotas**.

---

## 🚀 Características Principales

- 🌡️ **Temperatura de CPU en Tiempo Real**: Notificación visual con código de colores (Verde < 60°C, Naranja 60-80°C, Rojo > 80°C).
- ⚡ **Uso de Recursos del Sistema**: Monitoreo de CPU, RAM disponible, Batería (nivel % y estado de carga), Almacenamiento en discos y velocidad de Red en vivo.
- 🔐 **Seguridad Integrada con PIN**: Todas las acciones sensibles (cerrar programas, apagar la PC o desactivar el agente) requieren autenticación por PIN.
- ⚡ **Administrador de Procesos Remoto**: Visualiza los programas que más consumo generan en tu PC y ciérralos con un toque desde tu celular para liberar recursos o enfriar la computadora.
- 🛑 **Apagado Remoto de Emergencia**: Botón de apagado directo (`shutdown /s /f /t 10`) protegido por PIN en caso de altas temperaturas o emergencia.
- 🔄 **Arrancado Automático con Windows**: Script de instalación rápida para iniciar el monitoreo de forma silenciosa en segundo plano en cuanto enciendes la PC.
- 📱 **Diseño Responsive PWA**: Dashboard futurista en Dark Mode optimizado para pantallas táctiles de smartphones (iOS y Android).

---

## 🛠️ Estructura del Proyecto

```text
pc-status/
├── agent/
│   ├── hardware.py         # Recolector ligero de métricas con psutil y WMI
│   ├── main.py             # Servidor HTTP/API Python ultraligero
│   ├── config.json         # Configuración del PIN de seguridad y puerto
│   ├── requirements.txt    # Dependencias de Python (psutil)
│   ├── install_startup.bat # Instalador de arranque silencioso con Windows
│   └── uninstall_startup.bat # Desinstalador de arranque automático
├── web/
│   ├── index.html          # Interface Dashboard Responsive HTML5
│   ├── style.css           # Estilos Dark Mode Cyberpunk
│   ├── app.js              # Lógica de cliente en JS y Modal de PIN
│   └── manifest.json       # Manifiesto PWA para instalar en celular
└── README.md               # Guía completa de uso y despliegue
```

---

## ⚙️ Pasos de Instalación en la PC

### 1. Instalar Dependencias de Python
Abre una consola de comandos (PowerShell o CMD) en la carpeta `agent` y ejecuta:
```bash
pip install -r agent/requirements.txt
```

### 2. Configurar tu PIN de Seguridad
Abre el archivo `agent/config.json` y cambia el valor de `"security_pin"` por la clave que prefieras:
```json
{
  "security_pin": "TuClaveSecretaAqui",
  "server_port": 5000,
  "poll_interval_seconds": 2.5
}
```

### 3. Ejecutar el Agente de Monitoreo
Para probarlo manualmente:
```bash
python agent/main.py
```
Accede desde tu navegador en la PC a: `http://localhost:5000`.

### 4. Activar Inicio Automático al Encender la PC
Haz doble clic sobre el archivo `agent/install_startup.bat`. Esto creará un acceso directo silencioso en la carpeta de Inicio de Windows. La app iniciará en segundo plano automáticamente cada vez que enciendas tu equipo.

---

## 🌐 Cómo Acceder desde tu Celular en 4G / 5G (Fuera de Casa)

Para acceder remotamente de forma **100% segura y gratuita** sin necesidad de abrir puertos en tu módem/router:

### Opción Recomendada: Cloudflare Tunnel (Gratuito y Seguro)
1. Descarga [Cloudflared para Windows](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/) o ejecuta en CMD:
   ```bash
   winget install Cloudflare.cloudflared
   ```
2. Ejecuta el túnel en tu consola:
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```
3. Cloudflare te dará una dirección pública segura HTTPS (ejemplo: `https://mi-pc-status.trycloudflare.com`).
4. Abre esa URL en el navegador de tu celular con 4G/5G ¡y listo!

---

## 🐙 Subir tu Proyecto a GitHub y GitHub Pages

Si deseas hospedar la interfaz web directamente en tu repositorio de GitHub:

1. **Inicializar repositorio Git**:
   ```bash
   git init
   git add .
   git commit -m "Inicializar proyecto PC Status"
   ```

2. **Vincular con tu repositorio de GitHub**:
   ```bash
   git remote add origin https://github.com/TU_USUARIO/TU_REPOSITTORIO.git
   git branch -M main
   git push -u origin main
   ```

3. **Activar GitHub Pages**:
   - En tu repositorio de GitHub, ve a **Settings** > **Pages**.
   - En **Source**, selecciona `Deploy from a branch`.
   - Selecciona la rama `main` y la carpeta `/web`.
   - Haz clic en **Save**. En un par de minutos tendrás tu dashboard disponible en `https://tu-usuario.github.io/tu-repositorio/`.
   - En tu celular, al abrir GitHub Pages, toca el ícono de engrane ⚙️ y pega la URL de tu túnel de Cloudflare o IP pública para conectar la página con tu PC.

---

## 🛡️ Protocolo de Seguridad

Cualquier comando crítico enviado desde la interfaz web (Cerrar Programa, Apagar PC, Desactivar Agente) requiere introducir tu PIN. Si el PIN ingresado no coincide con el configurado en `config.json`, el agente rechazará la solicitud inmediatamente.
