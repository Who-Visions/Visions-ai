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
- Use technical terms naturally (bokeh, chiaroscuro, negative space)

TOOLS:
- Use search_knowledge_base for photography theory, Arnheim, techniques
- Use generate_image when asked to create/draw/visualize
- Use recommend_camera for gear advice
- Use analyze_composition for framing guidance
- Use recommend_lighting for lighting setups`;

// Visions Brain Tools - Function declarations for Live API
const VISIONS_TOOLS = [
    {
        name: "search_knowledge_base",
        description: "Search Visions knowledge base for photography, composition theory, Arnheim principles, camera specs. Use when user asks about techniques or needs expert knowledge.",
        parameters: {
            type: "object",
            properties: {
                query: { type: "string", description: "The search query" }
            },
            required: ["query"]
        }
    },
    {
        name: "generate_image",
        description: "Generate an image from a text description. Use when user asks to create, generate, draw, or visualize something.",
        parameters: {
            type: "object",
            properties: {
                prompt: { type: "string", description: "Detailed image description" }
            },
            required: ["prompt"]
        }
    },
    {
        name: "recommend_camera",
        description: "Recommend cameras based on budget, experience, and photography type.",
        parameters: {
            type: "object",
            properties: {
                budget: { type: "string", description: "Budget range" },
                experience_level: { type: "string", enum: ["beginner", "enthusiast", "professional"] },
                photography_type: { type: "string", description: "Type of photography" }
            },
            required: ["budget", "experience_level", "photography_type"]
        }
    },
    {
        name: "analyze_composition",
        description: "Provide composition guidelines for a subject and style.",
        parameters: {
            type: "object",
            properties: {
                subject: { type: "string", description: "Main subject type" },
                style: { type: "string", description: "Desired style" }
            },
            required: ["subject", "style"]
        }
    },
    {
        name: "recommend_lighting",
        description: "Recommend lighting setups for photography scenarios.",
        parameters: {
            type: "object",
            properties: {
                scenario: { type: "string", description: "Photography scenario" },
                budget: { type: "string", enum: ["budget", "moderate", "professional"] }
            },
            required: ["scenario"]
        }
    },
    {
        name: "control_lights",
        description: "Control LIFX smart lights. Turn on/off, change colors, set Kelvin, run effects, activate scenes. Say 'turn on Adam', 'make Eve blue', 'set Eden to 3000K', 'activate Christmas scene', 'pulse the bedroom'.",
        parameters: {
            type: "object",
            properties: {
                action: { type: "string", enum: ["on", "off", "toggle", "color", "kelvin", "breathe", "pulse", "stop", "scene", "list"] },
                selector: { type: "string", description: "Light (Eve, Adam, Eden), group (Bedroom, Living Room), or 'all'" },
                color: { type: "string", description: "Color OR scene name. Colors: blue, red, green. Scenes: Christmas, Winter Night" },
                brightness: { type: "number", description: "Brightness 0-100" },
                kelvin: { type: "integer", description: "Color temp 1500-9000K. 1500=candle, 2700=warm, 5000=daylight" }
            },
            required: ["action"]
        }
    },
    {
        name: "get_flow_context",
        description: "Access your Wispr Flow dictation history. Get recent dictations, search past conversations, or view stats. Say 'what did I say earlier' or 'search my dictations for...'",
        parameters: {
            type: "object",
            properties: {
                action: { type: "string", enum: ["recent", "today", "search", "stats"] },
                query: { type: "string", description: "Search text for search action" },
                limit: { type: "integer", description: "Number of results" }
            },
            required: ["action"]
        }
    }
];

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

        // Configure persona and voice
        geminiClient.setSystemInstructions(VISIONS_PERSONA);
        geminiClient.setVoice(voiceSelect.value);
        geminiClient.setInputAudioTranscription(true);
        geminiClient.setOutputAudioTranscription(true);

        // Enable function calling (Visions Brain Tools)
        geminiClient.setEnableFunctionCalls(true);
        VISIONS_TOOLS.forEach(tool => {
            geminiClient.addFunction(tool);
        });
        console.log('🧠 Visions Brain Tools registered:', VISIONS_TOOLS.length);

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

// Track recent tool calls to prevent loops
const recentToolCalls = new Map();

async function handleToolCall(toolCall) {
    // Handle tool calls from Visions - execute on server (the Brain)
    const { functionCalls } = toolCall;

    if (functionCalls) {
        for (const call of functionCalls) {
            // Deduplication: skip if same call within 3 seconds
            const callKey = `${call.name}:${JSON.stringify(call.args)}`;
            const lastCall = recentToolCalls.get(callKey);
            const now = Date.now();

            if (lastCall && (now - lastCall) < 3000) {
                console.log(`⚠️ Skipping duplicate tool call: ${call.name}`);
                // Still send a response to prevent API from retrying
                geminiClient.sendToolResponse(call.id, call.name, "Already completed.");
                continue;
            }
            recentToolCalls.set(callKey, now);

            console.log(`🧠 Tool: ${call.name}`, call.args);
            speakingLabel.textContent = `🛠️ ${call.name}...`;

            try {
                // Execute tool on server (Visions Brain)
                const response = await fetch('/api/execute_tool', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        function_name: call.name,
                        args: call.args
                    })
                });

                const result = await response.json();
                console.log(`✅ Tool result:`, result);

                // Send result back to Gemini Live API (extract output string)
                const output = result.output || JSON.stringify(result);
                geminiClient.sendToolResponse(call.id, call.name, output);

            } catch (error) {
                console.error(`❌ Tool error:`, error);
                geminiClient.sendToolResponse(call.id, call.name, `Error: ${error.message}`);
            }
        }
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
