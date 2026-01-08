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
const joystickSection = document.getElementById('joystick-section');
const autoIndicator = document.getElementById('auto-indicator');
const autoParamsSection = document.getElementById('auto-params-section');
const autoToggle = document.getElementById('auto-toggle');
const autoStatusLabel = document.getElementById('auto-status-label');

// Video elements
const videoSection = document.getElementById('video-section');
const videoIframe = document.getElementById('video-iframe');
const videoPlaceholder = document.getElementById('video-placeholder');
const recentDetectionsEl = document.getElementById('recent-detections');

// Camera controls
const cameraToggle = document.getElementById('camera-toggle');
const cameraStatusText = document.getElementById('camera-status-text');

// Console elements
const consoleSection = document.getElementById('console-section');
const consoleInput = document.getElementById('console-input');
const consoleSendBtn = document.getElementById('console-send-btn');

// Auto mode controls
const listAInput = document.getElementById('list-a-input');
const listBInput = document.getElementById('list-b-input');
const updateListsBtn = document.getElementById('update-lists-btn');
const confidenceSlider = document.getElementById('confidence-slider');
const confidenceValue = document.getElementById('confidence-value');

// Mode buttons
const modeBtns = document.querySelectorAll('.mode-btn');
const modeManual = document.getElementById('mode-manual');
const modeAuto = document.getElementById('mode-auto');

// Inicializar Socket.IO
const socket = io(`http://${window.location.host}`);

// Estado actual
let currentMode = 'manual';

// Detections management
const MAX_RECENT_DETECTIONS = 5;
let detections = [];

// Estado global de control
let controlState = {
    type: 'stop', // 'joystick', 'turn', 'stop'
    data: { x: 0, y: 0 },
    dir: null
};

// --- Mode Management ---
function setMode(mode) {
    // Disable mode buttons during transition
    modeBtns.forEach(btn => btn.disabled = true);

    currentMode = mode;
    socket.emit('change_mode', { mode: mode });

    // Update active state
    modeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Clean control state when switching modes
    resetControlState();

    // Handle mode-specific UI with smooth transitions
    if (mode === 'manual') {
        showManualMode();
    } else if (mode === 'auto') {
        showAutoMode();
    }

    // Re-enable buttons after transition
    setTimeout(() => {
        modeBtns.forEach(btn => btn.disabled = false);
    }, 300);
}

function showManualMode() {
    // Add transitioning class for performance
    const sections = [joystickSection, autoIndicator, autoParamsSection, videoSection, consoleSection];
    sections.forEach(s => s.classList.add('section-transitioning'));

    // Show manual controls
    joystickSection.classList.remove('section-hidden');
    joystickSection.classList.add('section-visible');

    // Hide auto controls
    autoIndicator.classList.remove('section-visible');
    autoIndicator.classList.add('section-hidden');
    autoParamsSection.classList.remove('section-visible');
    autoParamsSection.classList.add('section-hidden');
    videoSection.classList.remove('section-visible');
    videoSection.classList.add('section-hidden');
    consoleSection.classList.remove('section-visible');
    consoleSection.classList.add('section-hidden');

    // Remove transitioning class after animation
    setTimeout(() => {
        sections.forEach(s => s.classList.remove('section-transitioning'));
    }, 300);
}

function showAutoMode() {
    // Add transitioning class for performance
    const sections = [joystickSection, autoIndicator, autoParamsSection, videoSection, consoleSection];
    sections.forEach(s => s.classList.add('section-transitioning'));

    // Hide manual controls
    joystickSection.classList.remove('section-visible');
    joystickSection.classList.add('section-hidden');

    // Show auto controls
    autoIndicator.classList.remove('section-hidden');
    autoIndicator.classList.add('section-visible');
    autoParamsSection.classList.remove('section-hidden');
    autoParamsSection.classList.add('section-visible');
    videoSection.classList.remove('section-hidden');
    videoSection.classList.add('section-visible');
    consoleSection.classList.remove('section-hidden');
    consoleSection.classList.add('section-visible');

    // Always ensure auto is toggled OFF when switching modes for safety
    if (autoToggle) {
        autoToggle.checked = false;
        autoStatusLabel.textContent = 'OFF';
    }

    // Start video stream
    initVideoStream();

    // Remove transitioning class after animation
    setTimeout(() => {
        sections.forEach(s => s.classList.remove('section-transitioning'));
    }, 300);
}

function resetControlState() {
    // Reset manual control state
    controlState.type = 'stop';
    controlState.data = { x: 0, y: 0 };
    controlState.dir = null;
    pressedKeys.clear();

    // Send stop command to ensure robot stops
    socket.emit('joystick', { x: 0, y: 0 });
}

// Mode button click handlers
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        setMode(btn.dataset.mode);
    });
});

// Auto Activation Toggle
autoToggle.addEventListener('change', (e) => {
    const active = e.target.checked;
    socket.emit('toggle_auto', { active: active });
    autoStatusLabel.textContent = active ? 'ON' : 'OFF';
});

// Update object lists button
updateListsBtn.addEventListener('click', () => {
    const listA = listAInput.value.split(',').map(s => s.trim()).filter(s => s);
    const listB = listBInput.value.split(',').map(s => s.trim()).filter(s => s);
    socket.emit('set_object_lists', { list_a: listA, list_b: listB });

    // Visual feedback
    const originalText = updateListsBtn.textContent;
    updateListsBtn.classList.add('success');
    updateListsBtn.textContent = '';
    updateListsBtn.disabled = true;

    setTimeout(() => {
        updateListsBtn.classList.remove('success');
        updateListsBtn.textContent = originalText;
        updateListsBtn.disabled = false;
    }, 1500);
});

// Confidence slider
confidenceSlider.addEventListener('input', (e) => {
    const value = parseFloat(e.target.value);
    confidenceValue.textContent = value.toFixed(2);
    socket.emit('override_th', value);
});

// Camera toggle (solo oculta/muestra video, detección sigue activa)
cameraToggle.addEventListener('change', (e) => {
    const enabled = e.target.checked;
    socket.emit('toggle_camera', { enabled: enabled });
    cameraStatusText.textContent = enabled ? 'ON' : 'OFF';

    // Ocultar/mostrar el video visualmente
    if (enabled) {
        videoIframe.style.display = 'block';
        videoPlaceholder.style.display = 'none';
    } else {
        videoIframe.style.display = 'none';
        videoPlaceholder.innerHTML = '<p>Video oculto (detección activa)</p>';
        videoPlaceholder.style.display = 'flex';
    }
});

// Console message
function sendConsoleMessage() {
    const message = consoleInput.value.trim();
    if (message) {
        socket.emit('console_message', { message: message });
        consoleInput.value = '';

        // Visual feedback
        consoleSendBtn.disabled = true;
        const originalText = consoleSendBtn.textContent;
        consoleSendBtn.textContent = '✓';

        setTimeout(() => {
            consoleSendBtn.textContent = originalText;
            consoleSendBtn.disabled = false;
        }, 1000);
    }
}

consoleSendBtn.addEventListener('click', sendConsoleMessage);

consoleInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendConsoleMessage();
    }
});

// --- Video Stream Management ---
function initVideoStream() {
    const currentHostname = window.location.hostname;
    const targetPort = 4912;
    const targetPath = '/embed';
    const streamUrl = `http://${currentHostname}:${targetPort}${targetPath}`;

    // Only set the src once, don't keep reloading
    if (!videoIframe.src || videoIframe.src === '') {
        videoIframe.src = streamUrl;

        videoIframe.onload = () => {
            videoPlaceholder.style.display = 'none';
            videoIframe.style.display = 'block';
        };

        videoIframe.onerror = () => {
            console.warn('Error loading video stream');
            // Don't hide placeholder if there's an error
        };
    } else {
        // Video already loaded, just show it
        videoPlaceholder.style.display = 'none';
        videoIframe.style.display = 'block';
    }
}

// --- Detections Management ---
function addDetection(detection) {
    detections.unshift(detection);
    if (detections.length > MAX_RECENT_DETECTIONS) {
        detections.pop();
    }
    renderDetections();
}

function renderDetections() {
    if (detections.length === 0) {
        recentDetectionsEl.innerHTML = '<li class="no-detections">No se han detectado objetos</li>';
        return;
    }

    recentDetectionsEl.innerHTML = '';
    detections.forEach(det => {
        const li = document.createElement('li');
        const confidence = Math.floor(det.confidence * 100);
        const time = new Date(det.timestamp).toLocaleTimeString();
        li.innerHTML = `<span class="detection-name">${det.content}</span>
                        <span class="detection-confidence">${confidence}%</span>
                        <span class="detection-time">${time}</span>`;
        recentDetectionsEl.appendChild(li);
    });
}

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

joystick.on('move', (_evt, data) => {
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
        distDerechoEl.style.color = '#00878F';
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

    // Clean control state
    resetControlState();

    // Update UI visibility with smooth transitions
    if (data.mode === 'manual') {
        showManualMode();
    } else if (data.mode === 'auto') {
        showAutoMode();
    }
});

socket.on('detection', (data) => {
    addDetection(data);
});

socket.on('object_lists', (data) => {
    if (data.list_a) {
        listAInput.value = data.list_a.join(', ');
    }
    if (data.list_b) {
        listBInput.value = data.list_b.join(', ');
    }
});

socket.on('camera_status', (data) => {
    if (data.enabled !== undefined) {
        cameraToggle.checked = data.enabled;
        cameraStatusText.textContent = data.enabled ? 'ON' : 'OFF';

        // Sincronizar visibilidad del video con el estado
        if (data.enabled) {
            videoIframe.style.display = 'block';
            videoPlaceholder.style.display = 'none';
        } else {
            videoIframe.style.display = 'none';
            videoPlaceholder.innerHTML = '<p>Video oculto (detección activa)</p>';
            videoPlaceholder.style.display = 'flex';
        }
    }
});

// --- Initialize UI on page load ---
function initializeUI() {
    // Ensure manual mode is visible on load
    joystickSection.classList.add('section-visible');
    joystickSection.classList.remove('section-hidden');

    // Initialize detections list
    renderDetections();
}

// Call init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUI);
} else {
    initializeUI();
}
