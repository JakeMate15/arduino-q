// Configuración
const SEND_INTERVAL = 50; // ms

// Elementos del DOM
const statusEl = document.getElementById('connection-status');
const pwmLeftEl = document.getElementById('pwm-left');
const pwmRightEl = document.getElementById('pwm-right');
const distFrontalEl = document.getElementById('dist-frontal');
const distDerechoEl = document.getElementById('dist-derecho');
const errorContainer = document.getElementById('error-container');
const btnLeft = document.getElementById('btn-turn-left');
const btnRight = document.getElementById('btn-turn-right');

// Inicializar Socket.IO siguiendo el estándar de los ejemplos para Debian
const socket = io(window.location.origin, {
    path: '/socket.io',
    transports: ['polling', 'websocket']
});

let joystickData = { x: 0, y: 0 };
let lastSentTime = 0;
let turnInterval = null;

// Eventos de botones de giro
function bindTurnButton(btn, dir) {
    const startAction = () => {
        if (turnInterval) return; // Ya está girando

        // Enviar inmediatamente
        socket.emit('girar', { dir: dir, action: 'start' });

        // Repetir cada 100ms para que el watchdog del Arduino no se active
        turnInterval = setInterval(() => {
            socket.emit('girar', { dir: dir, action: 'start' });
        }, 100);
    };

    const stopAction = () => {
        if (turnInterval) {
            clearInterval(turnInterval);
            turnInterval = null;
        }
        socket.emit('girar', { dir: dir, action: 'stop' });
    };

    btn.addEventListener('mousedown', startAction);
    btn.addEventListener('mouseup', stopAction);
    btn.addEventListener('mouseleave', stopAction);

    // Soporte táctil
    btn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startAction();
    });
    btn.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopAction();
    });
}

bindTurnButton(btnLeft, 'izq');
bindTurnButton(btnRight, 'der');

// Inicializar Joystick (nipplejs)
const joystickZone = document.getElementById('joystick-zone');
const joystick = nipplejs.create({
    zone: joystickZone,
    mode: 'static',
    position: { left: '50%', top: '50%' },
    color: '#00878F',
    size: 150,
    lockY: true // Bloquear eje X en el frontend para mayor claridad
});

// Eventos del Joystick
joystick.on('move', (evt, data) => {
    if (data.distance) {
        const force = Math.min(data.distance / 75, 1);
        const angle = data.angle.radian;

        const x = Math.round(Math.cos(angle) * force * 255);
        const y = Math.round(Math.sin(angle) * force * 255);

        joystickData = { x, y };

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
