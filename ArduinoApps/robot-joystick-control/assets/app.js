// Configuración
const SEND_INTERVAL = 50; // ms

// Elementos del DOM
const statusEl = document.getElementById('connection-status');
const pwmLeftEl = document.getElementById('pwm-left');
const pwmRightEl = document.getElementById('pwm-right');
const distFrontalEl = document.getElementById('dist-frontal');
const distDerechoEl = document.getElementById('dist-derecho');
const errorContainer = document.getElementById('error-container');
const recToggle = document.getElementById('rec-toggle');

// Inicializar Socket.IO
const socket = io(`http://${window.location.host}`);

let joystickData = { x: 0, y: 0 };
let lastSentTime = 0;

// Lógica de Grabación
recToggle.addEventListener('change', (e) => {
    socket.emit('toggle_recording', { active: e.target.checked });
    if (e.target.checked) {
        console.log("Grabación iniciada");
    } else {
        console.log("Grabación detenida");
    }
});

// Inicializar Joystick (nipplejs)
const joystickZone = document.getElementById('joystick-zone');
const joystick = nipplejs.create({
    zone: joystickZone,
    mode: 'static',
    position: { left: '50%', top: '50%' },
    color: '#00878F',
    size: 150
});

// Eventos del Joystick
joystick.on('move', (evt, data) => {
    if (data.distance) {
        // Normalizar a rango -255 a 255
        // data.vector.x e y están en rango -1 a 1
        const force = Math.min(data.distance / 75, 1); // 75 es el radio (size/2)
        const angle = data.angle.radian;

        const x = Math.round(Math.cos(angle) * force * 255);
        const y = Math.round(Math.sin(angle) * force * 255);

        joystickData = { x, y };

        // Throttling: Enviar solo si ha pasado el intervalo
        const now = Date.now();
        if (now - lastSentTime > SEND_INTERVAL) {
            sendJoystickData();
            lastSentTime = now;
        }
    }
});

joystick.on('end', () => {
    joystickData = { x: 0, y: 0 };
    sendJoystickData();
});

function sendJoystickData() {
    socket.emit('joystick', joystickData);
}

// Botones de Giro
const btnLeft = document.getElementById('btn-left');
const btnRight = document.getElementById('btn-right');

function handleTurnStart(dir) {
    socket.emit('girar', { dir: dir, action: 'start' });
}

function handleTurnStop() {
    socket.emit('girar', { action: 'stop' });
}

// Eventos para Botón Izquierdo
btnLeft.addEventListener('mousedown', () => handleTurnStart('izq'));
btnLeft.addEventListener('mouseup', handleTurnStop);
btnLeft.addEventListener('mouseleave', handleTurnStop);
btnLeft.addEventListener('touchstart', (e) => { e.preventDefault(); handleTurnStart('izq'); });
btnLeft.addEventListener('touchend', handleTurnStop);

// Eventos para Botón Derecho
btnRight.addEventListener('mousedown', () => handleTurnStart('der'));
btnRight.addEventListener('mouseup', handleTurnStop);
btnRight.addEventListener('mouseleave', handleTurnStop);
btnRight.addEventListener('touchstart', (e) => { e.preventDefault(); handleTurnStart('der'); });
btnRight.addEventListener('touchend', handleTurnStop);

// Comunicación Socket.IO
socket.on('connect', () => {
    statusEl.textContent = 'Conectado';
    statusEl.className = 'status-connected';
    errorContainer.style.display = 'none';
});

socket.on('disconnect', () => {
    statusEl.textContent = 'Desconectado';
    statusEl.className = 'status-disconnected';
    errorContainer.textContent = 'Conexión perdida con el servidor.';
    errorContainer.style.display = 'block';
});

socket.on('sensores', (data) => {
    if (data.frontal !== undefined) {
        distFrontalEl.textContent = `${data.frontal} cm`;
        // Cambio de color si está muy cerca
        distFrontalEl.style.color = (data.frontal > 0 && data.frontal < 15) ? '#e74c3c' : '#00878F';
    }
    if (data.derecho !== undefined) {
        distDerechoEl.textContent = `${data.derecho} cm`;
    }
});

socket.on('motores', (data) => {
    if (data.izquierdo !== undefined) pwmLeftEl.textContent = data.izquierdo;
    if (data.derecho !== undefined) pwmRightEl.textContent = data.derecho;
});

socket.on('status', (data) => {
    console.log('Server status:', data.message);
});

