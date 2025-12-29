// Silenciar mensajes de detección del framework
const originalConsoleLog = console.log;
console.log = function(...args) {
    // Filtrar mensajes de "classification Object" del framework
    const message = args.join(' ');
    if (message.includes('classification Object')) {
        return; // Silenciar estos mensajes
    }
    // Permitir todos los demás mensajes
    originalConsoleLog.apply(console, args);
};

// Configuración
const SEND_INTERVAL = 100; // ms (Heartbeat para el Watchdog)

// Elementos del DOM
const statusEl = document.getElementById('connection-status');
const pwmLeftEl = document.getElementById('pwm-left');
const pwmRightEl = document.getElementById('pwm-right');
const distFrontalEl = document.getElementById('dist-frontal');
const distDerechoEl = document.getElementById('dist-derecho');
const errorContainer = document.getElementById('error-container');
const recToggle = document.getElementById('rec-toggle');
const joystickSection = document.getElementById('joystick-section');
const autoIndicator = document.getElementById('auto-indicator');
const pidParamsSection = document.getElementById('pid-params-section');
const pidToggle = document.getElementById('pid-toggle');
const pidStatusLabel = document.getElementById('pid-status-label');

// Mode buttons
const modeBtns = document.querySelectorAll('.mode-btn');
const modeManual = document.getElementById('mode-manual');
const modePid = document.getElementById('mode-pid');
const modeIa = document.getElementById('mode-ia');

// PID parameter inputs
const pidSetpoint = document.getElementById('pid-setpoint');
const pidSpeed = document.getElementById('pid-speed');
const pidKp = document.getElementById('pid-kp');
const pidKi = document.getElementById('pid-ki');
const pidKd = document.getElementById('pid-kd');
const pidApply = document.getElementById('pid-apply');
const pidAutotuneBtn = document.getElementById('pid-autotune');
const autotuneContainer = document.getElementById('autotune-container');
const autotuneBar = document.getElementById('autotune-bar');
const autotunePercent = document.getElementById('autotune-percent');

// Inicializar Socket.IO
const socket = io(`http://${window.location.host}`);

// Estado actual
let currentMode = 'manual';
let iaAvailable = false;

// Estado global de control
let controlState = {
    type: 'stop', // 'joystick', 'turn', 'stop'
    data: { x: 0, y: 0 },
    dir: null
};

// --- Mode Management ---
function setMode(mode) {
    if (mode === 'ia' && !iaAvailable) {
        console.warn('IA mode not available');
        return;
    }
    
    currentMode = mode;
    socket.emit('change_mode', { mode: mode });
    
    // Update UI
    modeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    // Show/hide joystick section
    if (mode === 'manual') {
        joystickSection.style.display = 'flex';
        autoIndicator.style.display = 'none';
        pidParamsSection.style.display = 'none';
    } else {
        joystickSection.style.display = 'none';
        autoIndicator.style.display = 'flex';
        pidParamsSection.style.display = mode === 'pid' ? 'block' : 'none';
        
        // Always ensure PID is toggled OFF when switching modes for safety
        if (pidToggle) {
            pidToggle.checked = false;
            pidStatusLabel.textContent = 'OFF';
        }
    }
}

// Mode button click handlers
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        if (!btn.disabled) {
            setMode(btn.dataset.mode);
        }
    });
});

// PID parameter apply button
pidApply.addEventListener('click', () => {
    socket.emit('pid_params', {
        setpoint: parseFloat(pidSetpoint.value),
        base_speed: parseInt(pidSpeed.value),
        kp: parseFloat(pidKp.value),
        ki: parseFloat(pidKi.value),
        kd: parseFloat(pidKd.value)
    });
});

// PID Autotune Button
pidAutotuneBtn.addEventListener('click', () => {
    setMode('autotune');
    autotuneContainer.style.display = 'block';
    autotuneBar.style.width = '0%';
    autotunePercent.textContent = '0%';
});

// PID Activation Toggle
pidToggle.addEventListener('change', (e) => {
    const active = e.target.checked;
    socket.emit('toggle_pid', { active: active });
    pidStatusLabel.textContent = active ? 'ON' : 'OFF';
});

// --- Keyboard Control ---
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
    if (currentMode !== 'manual') return;
    
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

// --- Heartbeat (Watchdog) ---
setInterval(() => {
    // Only send manual controls in manual mode
    if (currentMode !== 'manual') return;
    
    if (controlState.type === 'joystick') {
        socket.emit('joystick', controlState.data);
    } else if (controlState.type === 'turn') {
        socket.emit('girar', { dir: controlState.dir, action: 'start' });
    } else if (controlState.type === 'stop') {
        socket.emit('joystick', { x: 0, y: 0 });
    }
}, SEND_INTERVAL);

// --- Recording ---
recToggle.addEventListener('change', (e) => {
    socket.emit('toggle_recording', { active: e.target.checked });
});

// --- Joystick (nipplejs) ---
const joystickZone = document.getElementById('joystick-zone');

// Adapt joystick size for small screens
const joystickSize = window.innerWidth < 400 ? 120 : 150;

const joystick = nipplejs.create({
    zone: joystickZone,
    mode: 'static',
    position: { left: '50%', top: '50%' },
    color: '#00878F',
    size: joystickSize
});

joystick.on('move', (evt, data) => {
    if (currentMode !== 'manual') return;
    
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
    if (currentMode !== 'manual') return;
    controlState.type = 'stop';
    controlState.data = { x: 0, y: 0 };
});

// --- Turn Buttons ---
const btnLeft = document.getElementById('btn-left');
const btnRight = document.getElementById('btn-right');

function handleTurnStart(dir) {
    if (currentMode !== 'manual') return;
    controlState.type = 'turn';
    controlState.dir = dir;
}

function handleTurnStop() {
    if (currentMode !== 'manual') return;
    controlState.type = 'stop';
}

btnLeft.addEventListener('mousedown', () => handleTurnStart('izq'));
btnLeft.addEventListener('mouseup', handleTurnStop);
btnLeft.addEventListener('mouseleave', handleTurnStop);
btnLeft.addEventListener('touchstart', (e) => { e.preventDefault(); handleTurnStart('izq'); });
btnLeft.addEventListener('touchend', handleTurnStop);

btnRight.addEventListener('mousedown', () => handleTurnStart('der'));
btnRight.addEventListener('mouseup', handleTurnStop);
btnRight.addEventListener('mouseleave', handleTurnStop);
btnRight.addEventListener('touchstart', (e) => { e.preventDefault(); handleTurnStart('der'); });
btnRight.addEventListener('touchend', handleTurnStop);

// --- Socket.IO Events ---
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
        // Highlight when close to PID setpoint
        const setpoint = parseFloat(pidSetpoint.value);
        const diff = Math.abs(data.derecho - setpoint);
        if (currentMode === 'pid' && diff < 3) {
            distDerechoEl.style.color = '#2ecc71'; // Green when on target
        } else {
            distDerechoEl.style.color = '#00878F';
        }
    }
});

socket.on('motores', (data) => {
    if (data.izquierdo !== undefined) pwmLeftEl.textContent = data.izquierdo;
    if (data.derecho !== undefined) pwmRightEl.textContent = data.derecho;
});

socket.on('status', (data) => {
    console.log('Server status:', data.message);
});

socket.on('mode_changed', (data) => {
    currentMode = data.mode;
    modeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === data.mode);
    });
    
    // Update UI visibility
    if (data.mode === 'manual') {
        joystickSection.style.display = 'flex';
        autoIndicator.style.display = 'none';
        pidParamsSection.style.display = 'none';
    } else {
        joystickSection.style.display = 'none';
        autoIndicator.style.display = 'flex';
        pidParamsSection.style.display = data.mode === 'pid' ? 'block' : 'none';
    }
});

socket.on('pid_params', (data) => {
    // Update PID input fields with server values
    if (data.setpoint !== undefined) pidSetpoint.value = data.setpoint;
    if (data.base_speed !== undefined) pidSpeed.value = data.base_speed;
    if (data.kp !== undefined) pidKp.value = data.kp;
    if (data.ki !== undefined) pidKi.value = data.ki;
    if (data.kd !== undefined) pidKd.value = data.kd;
});

socket.on('autotune_progress', (data) => {
    const percent = Math.round(data.progress * 100) + '%';
    autotuneBar.style.width = percent;
    autotunePercent.textContent = percent;
    
    if (data.finished) {
        setTimeout(() => {
            autotuneContainer.style.display = 'none';
            // Results will be updated via the 'pid_params' event which follows
        }, 2000);
    }
});

socket.on('ia_available', (data) => {
    iaAvailable = data.available;
    modeIa.disabled = !iaAvailable;
    modeIa.title = iaAvailable ? 'Modo IA (XGBoost)' : 'Modelo IA no disponible - Entrena primero';
});
