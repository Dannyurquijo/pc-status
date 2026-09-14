# 💻 PC Status - Monitoreo y Control Remoto Bajo Demanda

**PC Status** es una solución completa, ultra ligera (< 15MB RAM, < 0.5% CPU) y sumamente segura para monitorear en tiempo real la salud de tu computadora desde tu teléfono celular a través de **4G/5G o redes Wi-Fi remotas**.

---

## ⚡ Activación Bajo Demanda (Solo cuando tú lo solicites)

El sistema **NO** se inicia automáticamente al encender Windows. Se activa únicamente cuando tú lo solicites y se apaga automáticamente cuando apagues la computadora o cuando pidas desactivarlo.

### Cómo Iniciar el Monitoreo:
- **Opción A (Desde el Chat de IA)**: Pide *"inicia el monitoreo"* o *"activa PC status"*.
- **Opción B (Doble Clic)**: Ejecuta el archivo `start_agent.bat` en la raíz del proyecto.

### Cómo Detener el Monitoreo:
- **Opción A (Al apagar la PC)**: Se apaga automáticamente junto con la computadora.
- **Opción B (Desde el Chat de IA)**: Pide *"apaga el monitoreo"* o *"detén el agente"*.
- **Opción C (Desde la Web UI)**: Usa el botón **"Desactivar Monitoreo Remoto"** ingresando tu PIN de seguridad.
- **Opción D (Doble Clic)**: Ejecuta el archivo `stop_agent.bat`.

---

## 🚀 Características Principales

- 🌡️ **Temperatura de CPU en Tiempo Real**: Notificación visual con código de colores (Verde < 60°C, Naranja 60-80°C, Rojo > 80°C).
- ⚡ **Uso de Recursos del Sistema**: Monitoreo de CPU, RAM disponible, Batería (nivel % y estado de carga), Almacenamiento en discos y velocidad de Red en vivo.
- 🔐 **Seguridad Integrada con PIN**: Todas las acciones sensibles (cerrar programas, apagar la PC o desactivar el agente) requieren autenticación por PIN.
- ⚡ **Administrador de Procesos Remoto**: Visualiza los programas que más consumo generan en tu PC y ciérralos con un toque desde tu celular para liberar recursos o enfriar la computadora.
- 🛑 **Apagado Remoto de Emergencia**: Botón de apagado directo (`shutdown /s /f /t 10`) protegido por PIN en caso de altas temperaturas o emergencia.
- 📱 **Diseño Responsive PWA**: Dashboard futurista en Dark Mode optimizado para pantallas táctiles de smartphones (iOS y Android).

---

## 🛠️ Estructura del Proyecto

```text
pc-status/
├── start_agent.bat        # Inicia el agente bajo demanda (1 clic)
├── stop_agent.bat         # Detiene el agente bajo demanda (1 clic)
├── index.html             # Interface Dashboard Responsive HTML5
├── style.css              # Estilos Dark Mode Cyberpunk
├── app.js                 # Lógica de cliente en JS y Modal de PIN
├── manifest.json          # Manifiesto PWA para instalar en celular
├── agent/
│   ├── hardware.py        # Recolector ligero de métricas con psutil y WMI
│   ├── main.py            # Servidor HTTP/API Python ultraligero
│   ├── config.json        # Configuración del PIN de seguridad y puerto
│   └── requirements.txt   # Dependencias de Python (psutil)
└── README.md              # Guía completa de uso y despliegue
```

---

## 🌐 Acceso desde Celular en 4G / 5G (Cloudflare Tunnel)

1. Ejecuta `start_agent.bat` (o pídelo por el chat).
2. Abre tu túnel seguro: `cloudflared tunnel --url http://localhost:5000`
3. Abre tu Dashboard Web: [https://dannyurquijo.github.io/pc-status/](https://dannyurquijo.github.io/pc-status/)
4. Toca ⚙️ y coloca la URL del túnel.
