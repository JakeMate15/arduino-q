// Configuración
const SEND_INTERVAL = 100; // ms (Aumentado un poco para estabilidad)

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

// Estado global de control
let controlState = {
    type: 'stop', // 'joystick', 'turn', 'stop'
    data: { x: 0, y: 0 },
    dir: null
};

// Control por Teclado
const pressedKeys = new Set();

document.addEventListener('keydown', (e) => {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.preventDefault();
        pressedKeys.add(e.key);
        updateControlFromKeyboard();
    }
});

document.addEventListener('keyup', (e) => {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.preventDefault();
        pressedKeys.delete(e.key);
        updateControlFromKeyboard();
    }
});

function updateControlFromKeyboard() {
    if (pressedKeys.size === 0) {
        controlState.type = 'stop';
        controlState.data = { x: 0, y: 0 };
        return;
    }

    let x = 0;
    let y = 0;

    if (pressedKeys.has('ArrowUp')) y += 255;
    if (pressedKeys.has('ArrowDown')) y -= 255;

    // Si solo estamos presionando izquierda/derecha, usamos el modo 'turn' para giro sobre eje
    if (pressedKeys.has('ArrowLeft') && !pressedKeys.has('ArrowUp') && !pressedKeys.has('ArrowDown')) {
        controlState.type = 'turn';
        controlState.dir = 'izq';
        return;
    }
    if (pressedKeys.has('ArrowRight') && !pressedKeys.has('ArrowUp') && !pressedKeys.has('ArrowDown')) {
        controlState.type = 'turn';
        controlState.dir = 'der';
        return;
    }

    // Si hay combinación (ej: Arriba + Izquierda), usamos modo joystick para giro suave
    if (pressedKeys.has('ArrowLeft')) x -= 255;
    if (pressedKeys.has('ArrowRight')) x += 255;

    controlState.type = 'joystick';
    controlState.data = { x, y };
}

// Ciclo de envío constante (Heartbeat para el Watchdog)
setInterval(() => {
    if (controlState.type === 'joystick') {
        socket.emit('joystick', controlState.data);
    } else if (controlState.type === 'turn') {
        socket.emit('girar', { dir: controlState.dir, action: 'start' });
    } else if (controlState.type === 'stop') {
        // Opcional: enviar stop periódico para asegurar que el robot se detenga
        socket.emit('joystick', { x: 0, y: 0 });
    }
}, SEND_INTERVAL);

// Lógica de Grabación
recToggle.addEventListener('change', (e) => {
    socket.emit('toggle_recording', { active: e.target.checked });
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
        const force = Math.min(data.distance / 75, 1);
        const angle = data.angle.radian;
        const x = Math.round(Math.cos(angle) * force * 255);
        const y = Math.round(Math.sin(angle) * force * 255);

        controlState.type = 'joystick';
        controlState.data = { x, y };
    }
});

joystick.on('end', () => {
    controlState.type = 'stop';
    controlState.data = { x: 0, y: 0 };
});

// Botones de Giro
const btnLeft = document.getElementById('btn-left');
const btnRight = document.getElementById('btn-right');

function handleTurnStart(dir) {
    controlState.type = 'turn';
    controlState.dir = dir;
}

function handleTurnStop() {
    controlState.type = 'stop';
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

// --- Lógica de la Cámara ---
const iframe = document.getElementById('dynamicIframe');
const placeholder = document.getElementById('videoPlaceholder');
const currentHostname = window.location.hostname;
const targetPort = 4912;
const targetPath = '/embed';
const streamUrl = `http://${currentHostname}:${targetPort}${targetPath}`;

let cameraIntervalId;

iframe.onload = () => {
    if (cameraIntervalId) {
        clearInterval(cameraIntervalId);
    }
    placeholder.style.display = 'none';
    iframe.style.display = 'block';
};

const startLoadingCamera = () => {
    // Intentar cargar el stream de video
    if (iframe.style.display === 'none') {
        iframe.src = streamUrl;
    }
};

cameraIntervalId = setInterval(startLoadingCamera, 2000); // Reintentar cada 2 segundos
