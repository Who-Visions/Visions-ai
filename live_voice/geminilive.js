/**
 * Gemini Live API Client
 * WebSocket wrapper for Gemini Live API on Vertex AI
 */

const MultimodalLiveResponseType = {
    TEXT: "TEXT",
    AUDIO: "AUDIO",
    SETUP_COMPLETE: "SETUP_COMPLETE",
    INTERRUPTED: "INTERRUPTED",
    TURN_COMPLETE: "TURN_COMPLETE",
    TOOL_CALL: "TOOL_CALL",
    ERROR: "ERROR",
    INPUT_TRANSCRIPTION: "INPUT_TRANSCRIPTION",
    OUTPUT_TRANSCRIPTION: "OUTPUT_TRANSCRIPTION",
};

/**
 * Parses response messages from Gemini Live API
 */
class MultimodalLiveResponseMessage {
    constructor(data) {
        this.data = "";
        this.type = "";
        this.endOfTurn = false;

        this.endOfTurn = data?.serverContent?.turnComplete;
        const parts = data?.serverContent?.modelTurn?.parts;

        try {
            if (data?.setupComplete) {
                this.type = MultimodalLiveResponseType.SETUP_COMPLETE;
            } else if (data?.serverContent?.turnComplete) {
                this.type = MultimodalLiveResponseType.TURN_COMPLETE;
            } else if (data?.serverContent?.interrupted) {
                this.type = MultimodalLiveResponseType.INTERRUPTED;
            } else if (data?.serverContent?.inputTranscription) {
                this.type = MultimodalLiveResponseType.INPUT_TRANSCRIPTION;
                this.data = {
                    text: data.serverContent.inputTranscription.text || "",
                    finished: data.serverContent.inputTranscription.finished || false,
                };
            } else if (data?.serverContent?.outputTranscription) {
                this.type = MultimodalLiveResponseType.OUTPUT_TRANSCRIPTION;
                this.data = {
                    text: data.serverContent.outputTranscription.text || "",
                    finished: data.serverContent.outputTranscription.finished || false,
                };
            } else if (data?.toolCall) {
                this.type = MultimodalLiveResponseType.TOOL_CALL;
                this.data = data?.toolCall;
            } else if (parts?.length && parts[0].text) {
                this.data = parts[0].text;
                this.type = MultimodalLiveResponseType.TEXT;
            } else if (parts?.length && parts[0].inlineData) {
                this.data = parts[0].inlineData.data;
                this.type = MultimodalLiveResponseType.AUDIO;
            }
        } catch (e) {
            console.error("Error parsing response:", e, data);
        }
    }
}

/**
 * Main Gemini Live API Client
 */
class GeminiLiveAPI {
    constructor(proxyUrl, projectId, model) {
        this.proxyUrl = proxyUrl;
        this.projectId = projectId;
        this.model = model;
        this.modelUri = `projects/${this.projectId}/locations/us-central1/publishers/google/models/${this.model}`;

        // Configuration
        this.responseModalities = ["AUDIO"];
        this.systemInstructions = "";
        this.googleGrounding = false;
        this.enableAffectiveDialog = true;
        this.voiceName = "Charon";
        this.temperature = 0.9;
        this.proactivity = { proactiveAudio: false };
        this.inputAudioTranscription = true;
        this.outputAudioTranscription = true;

        // Function calling
        this.enableFunctionCalls = false;
        this.functions = [];
        this.functionsMap = {};

        // Activity detection
        this.automaticActivityDetection = {
            disabled: false,
            silence_duration_ms: 2000,
            prefix_padding_ms: 500,
            end_of_speech_sensitivity: "END_SENSITIVITY_HIGH",
            start_of_speech_sensitivity: "START_SENSITIVITY_LOW",
        };
        this.activityHandling = "ACTIVITY_HANDLING_UNSPECIFIED";

        // Connection
        this.apiHost = "us-central1-aiplatform.googleapis.com";
        this.serviceUrl = `wss://${this.apiHost}/ws/google.cloud.aiplatform.v1beta1.LlmBidiService/BidiGenerateContent`;
        this.connected = false;
        this.webSocket = null;
        this.totalBytesSent = 0;

        // Callbacks
        this.onReceiveResponse = (message) => console.log("Response:", message);
        this.onConnectionStarted = () => console.log("Connected");
        this.onErrorMessage = (message) => console.error("Error:", message);

        console.log("GeminiLiveAPI initialized:", this.modelUri);
    }

    setProjectId(projectId) {
        this.projectId = projectId;
        this.modelUri = `projects/${this.projectId}/locations/us-central1/publishers/google/models/${this.model}`;
    }

    setSystemInstructions(instructions) {
        this.systemInstructions = instructions;
    }

    setGoogleGrounding(enabled) {
        this.googleGrounding = enabled;
    }

    setResponseModalities(modalities) {
        this.responseModalities = modalities;
    }

    setVoice(voiceName) {
        this.voiceName = voiceName;
    }

    setProactivity(proactivity) {
        this.proactivity = proactivity;
    }

    setInputAudioTranscription(enabled) {
        this.inputAudioTranscription = enabled;
    }

    setOutputAudioTranscription(enabled) {
        this.outputAudioTranscription = enabled;
    }

    setEnableFunctionCalls(enabled) {
        this.enableFunctionCalls = enabled;
    }

    addFunction(func) {
        this.functions.push(func);
        this.functionsMap[func.name] = func;
    }

    connect() {
        this.setupWebSocket();
    }

    disconnect() {
        if (this.webSocket) {
            this.webSocket.close();
            this.connected = false;
        }
    }

    sendMessage(message) {
        if (this.webSocket && this.webSocket.readyState === WebSocket.OPEN) {
            this.webSocket.send(JSON.stringify(message));
        }
    }

    onReceiveMessage(messageEvent) {
        const messageData = JSON.parse(messageEvent.data);
        const message = new MultimodalLiveResponseMessage(messageData);
        this.onReceiveResponse(message);
    }

    setupWebSocket() {
        console.log("Connecting to:", this.proxyUrl);
        this.webSocket = new WebSocket(this.proxyUrl);

        this.webSocket.onclose = (event) => {
            console.log("WebSocket closed:", event);
            this.connected = false;
            this.onErrorMessage("Connection closed");
        };

        this.webSocket.onerror = (event) => {
            console.error("WebSocket error:", event);
            this.connected = false;
            this.onErrorMessage("Connection error");
        };

        this.webSocket.onopen = () => {
            console.log("WebSocket connected");
            this.connected = true;
            this.totalBytesSent = 0;
            this.sendInitialSetupMessages();
            this.onConnectionStarted();
        };

        this.webSocket.onmessage = this.onReceiveMessage.bind(this);
    }

    getFunctionDefinitions() {
        return this.functions.map(func => func.getDefinition ? func.getDefinition() : func);
    }

    sendInitialSetupMessages() {
        // Send service URL first
        this.sendMessage({ service_url: this.serviceUrl });

        // Build session setup
        const tools = this.getFunctionDefinitions();
        const sessionSetupMessage = {
            setup: {
                model: this.modelUri,
                generation_config: {
                    response_modalities: this.responseModalities,
                    temperature: this.temperature,
                    speech_config: {
                        voice_config: {
                            prebuilt_voice_config: {
                                voice_name: this.voiceName,
                            },
                        },
                    },
                },
                system_instruction: { parts: [{ text: this.systemInstructions }] },
                tools: tools.length > 0 ? { function_declarations: tools } : {},
                proactivity: this.proactivity,
                realtime_input_config: {
                    automatic_activity_detection: this.automaticActivityDetection,
                    activity_handling: this.activityHandling,
                },
            },
        };

        // Enable transcription
        if (this.inputAudioTranscription) {
            sessionSetupMessage.setup.input_audio_transcription = {};
        }
        if (this.outputAudioTranscription) {
            sessionSetupMessage.setup.output_audio_transcription = {};
        }

        // Google grounding
        if (this.googleGrounding) {
            sessionSetupMessage.setup.tools = { google_search: {} };
        }

        // Affective dialog
        if (this.enableAffectiveDialog) {
            sessionSetupMessage.setup.generation_config.enable_affective_dialog = true;
        }

        console.log("Sending setup:", sessionSetupMessage);
        this.sendMessage(sessionSetupMessage);
    }

    sendTextMessage(text) {
        this.sendMessage({
            client_content: {
                turns: [{ role: "user", parts: [{ text }] }],
                turn_complete: true,
            },
        });
    }

    sendToolResponse(toolCallId, functionName, result) {
        // Gemini Live API expects function_responses array
        // The response.output field must be a STRING, not an object
        const outputString = typeof result === 'string' ? result : JSON.stringify(result);

        const toolResponse = {
            tool_response: {
                function_responses: [{
                    id: toolCallId,
                    name: functionName,
                    response: {
                        output: outputString
                    }
                }]
            }
        };
        console.log('📤 Sending tool response:', JSON.stringify(toolResponse));
        this.sendMessage(toolResponse);
    }

    sendRealtimeInputMessage(data, mimeType) {
        this.sendMessage({
            realtime_input: {
                media_chunks: [{ mime_type: mimeType, data }],
            },
        });
        this.totalBytesSent += new TextEncoder().encode(data).length;
    }

    sendAudioMessage(base64PCM) {
        this.sendRealtimeInputMessage(base64PCM, "audio/pcm");
    }

    sendImageMessage(base64Image, mimeType = "image/jpeg") {
        this.sendRealtimeInputMessage(base64Image, mimeType);
    }

    getBytesSent() {
        return this.totalBytesSent;
    }
}

// Export for use
window.GeminiLiveAPI = GeminiLiveAPI;
window.MultimodalLiveResponseType = MultimodalLiveResponseType;

console.log("geminilive.js loaded");
