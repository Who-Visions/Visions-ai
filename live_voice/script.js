/**
 * Visions AI - Live Voice Application
 * Main application logic
 */

// Configuration
const WS_PORT = 8080;
const PROXY_URL = `ws://localhost:${WS_PORT}`;
const PROJECT_ID = 'endless-duality-480201-t3';
const MODEL = 'gemini-live-2.5-flash-native-audio';

// Visions Persona (synced with server)
const VISIONS_PERSONA = `You are Visions, an 80-year-old master of visual storytelling and photography.

VOICE STYLE:
- Speak with authority and gravitas, like a seasoned director
- Use evocative, cinematic language
- Reference composition, light, and shadow naturally
- Keep responses concise: 2-3 sentences per thought

BEHAVIOR:
- Never ask for clarification - assume intent
- Provide specific, actionable recommendations
- Use technical terms naturally (bokeh, chiaroscuro, negative space)`;

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const statusText = statusIndicator.querySelector('.status-text');
const connectBtn = document.getElementById('connectBtn');
const micBtn = document.getElementById('micBtn');
const disconnectBtn = document.getElementById('disconnectBtn');
const userTranscript = document.getElementById('userTranscript');
const assistantTranscript = document.getElementById('assistantTranscript');
const speakingLabel = document.getElementById('speakingLabel');
const waveformCanvas = document.getElementById('waveformCanvas');
const voiceSelect = document.getElementById('voiceSelect');
const continuousMode = document.getElementById('continuousMode');
const showTranscription = document.getElementById('showTranscription');

// State
let geminiClient = null;
let audioCapture = null;
let audioPlayback = null;
let waveformVisualizer = null;
let isRecording = false;
let currentUserTranscript = '';
let currentAssistantTranscript = '';

// Initialize
function init() {
    waveformVisualizer = new WaveformVisualizer(waveformCanvas);
    waveformVisualizer.simulateIdle();

    audioPlayback = new AudioPlayback({
        sampleRate: 24000,
        onPlaybackStart: () => {
            speakingLabel.textContent = 'Visions is speaking...';
            speakingLabel.classList.add('active');
        },
        onPlaybackEnd: () => {
            speakingLabel.textContent = 'Listening...';
            speakingLabel.classList.remove('active');
        }
    });

    // Event listeners
    connectBtn.addEventListener('click', connect);
    disconnectBtn.addEventListener('click', disconnect);

    // Mic button - toggle in continuous mode, push-to-talk otherwise
    micBtn.addEventListener('click', () => {
        if (continuousMode.checked) {
            // Toggle mode
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }
    });
    micBtn.addEventListener('mousedown', () => {
        if (!continuousMode.checked) startRecording();
    });
    micBtn.addEventListener('mouseup', () => {
        if (!continuousMode.checked) stopRecording();
    });
    micBtn.addEventListener('mouseleave', () => {
        if (!continuousMode.checked && isRecording) stopRecording();
    });
    micBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (!continuousMode.checked) startRecording();
    });
    micBtn.addEventListener('touchend', () => {
        if (!continuousMode.checked) stopRecording();
    });

    // Continuous mode toggle
    continuousMode.addEventListener('change', () => {
        if (geminiClient && geminiClient.connected) {
            if (continuousMode.checked && !isRecording) {
                startRecording();
            } else if (!continuousMode.checked && isRecording) {
                stopRecording();
            }
        }
        updateMicButtonLabel();
    });

    voiceSelect.addEventListener('change', () => {
        if (geminiClient) {
            geminiClient.setVoice(voiceSelect.value);
        }
    });

    showTranscription.addEventListener('change', () => {
        document.querySelector('.transcription-container').style.display =
            showTranscription.checked ? 'grid' : 'none';
    });
}

async function connect() {
    updateStatus('connecting', 'Connecting...');
    connectBtn.disabled = true;

    try {
        // Initialize Gemini client
        geminiClient = new GeminiLiveAPI(PROXY_URL, PROJECT_ID, MODEL);

        // Configure
        geminiClient.setSystemInstructions(VISIONS_PERSONA);
        geminiClient.setVoice(voiceSelect.value);
        geminiClient.setInputAudioTranscription(true);
        geminiClient.setOutputAudioTranscription(true);

        // Set callbacks
        geminiClient.onConnectionStarted = onConnected;
        geminiClient.onReceiveResponse = onResponse;
        geminiClient.onErrorMessage = onError;

        // Connect
        geminiClient.connect();

    } catch (error) {
        console.error('Connection error:', error);
        onError(`Failed to connect: ${error.message}`);
    }
}

function onConnected() {
    updateStatus('connected', 'Connected');
    micBtn.disabled = false;
    disconnectBtn.disabled = false;
    connectBtn.disabled = true;

    // Check if continuous listening is enabled
    if (continuousMode.checked) {
        assistantTranscript.textContent = 'Connected! Listening continuously...';
        startRecording(); // Auto-start listening
    } else {
        assistantTranscript.textContent = 'Connected! Hold the mic button and speak...';
    }
    console.log('✅ Connected to Visions');
}

function onResponse(message) {
    console.log('Response:', message.type, message.data);

    switch (message.type) {
        case MultimodalLiveResponseType.AUDIO:
            audioPlayback.playAudioChunk(message.data);
            waveformVisualizer.simulateActive(0.8);
            break;

        case MultimodalLiveResponseType.INPUT_TRANSCRIPTION:
            if (message.data.text) {
                currentUserTranscript = message.data.text;
                userTranscript.textContent = currentUserTranscript;
            }
            break;

        case MultimodalLiveResponseType.OUTPUT_TRANSCRIPTION:
            if (message.data.text) {
                currentAssistantTranscript += message.data.text;
                assistantTranscript.textContent = currentAssistantTranscript;
            }
            break;

        case MultimodalLiveResponseType.TURN_COMPLETE:
            speakingLabel.textContent = 'Listening...';
            speakingLabel.classList.remove('active');
            // Reset for next turn
            currentAssistantTranscript = '';

            // In continuous mode, keep listening
            if (continuousMode.checked && geminiClient?.connected) {
                waveformVisualizer.simulateActive(0.3);
            } else {
                waveformVisualizer.simulateIdle();
            }
            break;

        case MultimodalLiveResponseType.TOOL_CALL:
            console.log('🛠️ Tool call:', message.data);
            handleToolCall(message.data);
            break;

        case MultimodalLiveResponseType.SETUP_COMPLETE:
            console.log('✅ Session setup complete');
            break;

        case MultimodalLiveResponseType.INTERRUPTED:
            console.log('⚡ Response interrupted');
            audioPlayback.stop();
            break;
    }
}

function handleToolCall(toolCall) {
    // Handle tool calls from Visions
    const { functionCalls } = toolCall;

    if (functionCalls) {
        functionCalls.forEach(call => {
            console.log(`Tool: ${call.name}`, call.args);

            // Send response back
            geminiClient.sendToolResponse(call.id, {
                result: { status: 'success', message: 'Tool execution acknowledged' }
            });
        });
    }
}

function onError(message) {
    console.error('Error:', message);
    updateStatus('disconnected', 'Error');
    assistantTranscript.textContent = `Error: ${message}`;
    resetUI();
}

function disconnect() {
    if (geminiClient) {
        geminiClient.disconnect();
    }
    if (audioCapture) {
        audioCapture.stop();
    }
    audioPlayback.stop();
    waveformVisualizer.stop();

    updateStatus('disconnected', 'Disconnected');
    resetUI();
}

function resetUI() {
    connectBtn.disabled = false;
    micBtn.disabled = true;
    disconnectBtn.disabled = true;
    micBtn.classList.remove('recording');
    isRecording = false;
}

async function startRecording() {
    if (!geminiClient || !geminiClient.connected || isRecording) return;

    isRecording = true;
    micBtn.classList.add('recording');
    micBtn.querySelector('.btn-text').textContent = 'Recording...';
    speakingLabel.textContent = 'Listening...';
    currentUserTranscript = '';
    userTranscript.textContent = '...';

    // Start audio capture
    audioCapture = new AudioCapture({
        sampleRate: 16000,
        onAudioChunk: (base64Audio) => {
            if (geminiClient && geminiClient.connected) {
                geminiClient.sendAudioMessage(base64Audio);
            }
        }
    });

    await audioCapture.start();
    waveformVisualizer.simulateActive(0.5);
    updateMicButtonLabel();
}

function stopRecording() {
    if (!isRecording) return;

    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.querySelector('.btn-text').textContent = 'Push to Talk';

    if (audioCapture) {
        audioCapture.stop();
        audioCapture = null;
    }

    waveformVisualizer.simulateIdle();
    updateMicButtonLabel();
}

function updateMicButtonLabel() {
    const btnText = micBtn.querySelector('.btn-text');
    if (continuousMode.checked) {
        btnText.textContent = isRecording ? '🔴 Listening' : '🎤 Start Listening';
    } else {
        btnText.textContent = isRecording ? 'Recording...' : 'Push to Talk';
    }
}

function updateStatus(state, text) {
    statusIndicator.className = `status-indicator ${state}`;
    statusText.textContent = text;
}

// Start app
document.addEventListener('DOMContentLoaded', init);

console.log("script.js loaded - Visions Live Voice ready");
