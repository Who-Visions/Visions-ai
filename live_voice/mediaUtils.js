/**
 * Media Utilities for Gemini Live API
 * Handles audio capture, playback, and waveform visualization
 */

class AudioCapture {
    constructor(options = {}) {
        this.sampleRate = options.sampleRate || 16000; // 16kHz for Gemini input
        this.bufferSize = options.bufferSize || 4096;
        this.onAudioChunk = options.onAudioChunk || (() => { });

        this.mediaStream = null;
        this.audioContext = null;
        this.workletNode = null;
        this.isRecording = false;
    }

    async start() {
        try {
            // Get microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                },
            });

            // Create audio context
            this.audioContext = new AudioContext({ sampleRate: this.sampleRate });

            // Create source from microphone
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Create script processor for capturing audio
            const processor = this.audioContext.createScriptProcessor(this.bufferSize, 1, 1);

            processor.onaudioprocess = (event) => {
                if (!this.isRecording) return;

                const inputData = event.inputBuffer.getChannelData(0);
                const pcmData = this.float32ToPCM16(inputData);
                const base64Audio = this.arrayBufferToBase64(pcmData.buffer);

                this.onAudioChunk(base64Audio);
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.isRecording = true;
            console.log("🎤 Audio capture started");

            return true;
        } catch (error) {
            console.error("Failed to start audio capture:", error);
            return false;
        }
    }

    stop() {
        this.isRecording = false;

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        console.log("🎤 Audio capture stopped");
    }

    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return pcm16;
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
}

class AudioPlayback {
    constructor(options = {}) {
        this.sampleRate = options.sampleRate || 24000; // 24kHz for Gemini output
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.onPlaybackStart = options.onPlaybackStart || (() => { });
        this.onPlaybackEnd = options.onPlaybackEnd || (() => { });
    }

    init() {
        if (!this.audioContext) {
            this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
        }
    }

    async playAudioChunk(base64Audio) {
        this.init();

        const pcmData = this.base64ToPCM16(base64Audio);
        const float32Data = this.pcm16ToFloat32(pcmData);

        // Create audio buffer
        const audioBuffer = this.audioContext.createBuffer(1, float32Data.length, this.sampleRate);
        audioBuffer.copyToChannel(float32Data, 0);

        // Queue and play
        this.audioQueue.push(audioBuffer);

        if (!this.isPlaying) {
            this.playNext();
        }
    }

    playNext() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            this.onPlaybackEnd();
            return;
        }

        this.isPlaying = true;
        this.onPlaybackStart();

        const audioBuffer = this.audioQueue.shift();
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);

        source.onended = () => this.playNext();
        source.start();
    }

    stop() {
        this.audioQueue = [];
        this.isPlaying = false;
    }

    base64ToPCM16(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return new Int16Array(bytes.buffer);
    }

    pcm16ToFloat32(pcm16Array) {
        const float32 = new Float32Array(pcm16Array.length);
        for (let i = 0; i < pcm16Array.length; i++) {
            float32[i] = pcm16Array[i] / (pcm16Array[i] < 0 ? 0x8000 : 0x7FFF);
        }
        return float32;
    }
}

class WaveformVisualizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.animationId = null;
        this.analyser = null;
        this.dataArray = null;
        this.isActive = false;

        // Style
        this.barColor = '#6366f1';
        this.backgroundColor = 'transparent';
        this.barWidth = 3;
        this.barGap = 2;
        this.barRadius = 2;
    }

    connect(audioContext, sourceNode) {
        this.analyser = audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        sourceNode.connect(this.analyser);
    }

    start() {
        this.isActive = true;
        this.draw();
    }

    stop() {
        this.isActive = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.clear();
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    draw() {
        if (!this.isActive) return;

        this.animationId = requestAnimationFrame(() => this.draw());

        if (this.analyser) {
            this.analyser.getByteFrequencyData(this.dataArray);
        }

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const bars = 40;
        const totalWidth = bars * (this.barWidth + this.barGap) - this.barGap;
        const startX = (this.canvas.width - totalWidth) / 2;
        const centerY = this.canvas.height / 2;

        for (let i = 0; i < bars; i++) {
            let value = 0;
            if (this.dataArray) {
                const index = Math.floor(i * this.dataArray.length / bars);
                value = this.dataArray[index] / 255;
            } else {
                // Idle animation
                value = 0.1 + 0.05 * Math.sin(Date.now() / 500 + i * 0.5);
            }

            const barHeight = value * (centerY - 10) * 2;
            const x = startX + i * (this.barWidth + this.barGap);
            const y = centerY - barHeight / 2;

            // Draw bar with glow
            this.ctx.fillStyle = this.barColor;
            this.ctx.shadowBlur = value * 10;
            this.ctx.shadowColor = this.barColor;

            this.roundedRect(x, y, this.barWidth, barHeight, this.barRadius);
        }
    }

    roundedRect(x, y, width, height, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + width - radius, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.ctx.lineTo(x + width, y + height - radius);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.ctx.lineTo(x + radius, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.fill();
    }

    // Simulate waveform when no analyser connected
    simulateIdle() {
        this.dataArray = null;
        this.start();
    }

    simulateActive(intensity = 0.5) {
        if (!this.dataArray) {
            this.dataArray = new Uint8Array(128);
        }
        for (let i = 0; i < this.dataArray.length; i++) {
            this.dataArray[i] = Math.floor(Math.random() * 255 * intensity);
        }
    }
}

// Export
window.AudioCapture = AudioCapture;
window.AudioPlayback = AudioPlayback;
window.WaveformVisualizer = WaveformVisualizer;

console.log("mediaUtils.js loaded");
