// games/bomberman/static/audio.js
// Procedural 8-bit sound synthesizers & Chiptune BGM using the Web Audio API (Zero external assets needed!)

export class ChiptuneBGM {
  constructor(soundEngine) {
    this.engine = soundEngine;
    this.isPlaying = false;
    this.timer = null;
    this.step = 0;
    this.bpm = 135;
    this.stepTime = (60 / this.bpm) / 4; // 16th note in seconds (~0.111s)
    this.volume = 0.12;

    // 16-step melody (frequencies in Hz, 0 = rest)
    this.melody = [
      523.25, 0, 659.25, 523.25, 783.99, 0, 659.25, 0,
      587.33, 0, 523.25, 0, 440.00, 523.25, 587.33, 0
    ];

    // 16-step bassline (Triangle wave)
    this.bass = [
      130.81, 130.81, 164.81, 164.81, 196.00, 196.00, 164.81, 164.81,
      146.83, 146.83, 130.81, 130.81, 110.00, 110.00, 146.83, 146.83
    ];

    // Percussion pattern: 0=none, 1=hi-hat, 2=snare
    this.drums = [
      1, 0, 1, 2, 1, 0, 1, 2,
      1, 0, 1, 2, 1, 1, 1, 2
    ];
  }

  start() {
    if (this.isPlaying) return;
    this.engine.init();
    if (!this.engine.ctx) return;
    this.isPlaying = true;
    this.step = 0;
    this.scheduleNext();
  }

  stop() {
    this.isPlaying = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  toggle() {
    if (this.isPlaying) {
      this.stop();
    } else {
      this.start();
    }
    return this.isPlaying;
  }

  scheduleNext() {
    if (!this.isPlaying) return;
    this.playStep(this.step);
    this.step = (this.step + 1) % 16;
    this.timer = setTimeout(() => {
      this.scheduleNext();
    }, this.stepTime * 1000);
  }

  playStep(stepIndex) {
    if (this.engine.muted || !this.engine.ctx) return;
    const ctx = this.engine.ctx;
    const t = ctx.currentTime;
    const duration = this.stepTime * 0.9;

    // 1. Melody (Square wave)
    const melFreq = this.melody[stepIndex];
    if (melFreq > 0) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      osc.type = 'square';
      osc.frequency.setValueAtTime(melFreq, t);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(1600, t);

      gain.gain.setValueAtTime(this.volume * 0.4, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + duration);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + duration);
    }

    // 2. Bassline (Triangle wave)
    const bassFreq = this.bass[stepIndex];
    if (bassFreq > 0) {
      const bOsc = ctx.createOscillator();
      const bGain = ctx.createGain();

      bOsc.type = 'triangle';
      bOsc.frequency.setValueAtTime(bassFreq, t);

      bGain.gain.setValueAtTime(this.volume * 0.6, t);
      bGain.gain.exponentialRampToValueAtTime(0.001, t + duration);

      bOsc.connect(bGain);
      bGain.connect(ctx.destination);

      bOsc.start(t);
      bOsc.stop(t + duration);
    }

    // 3. Drums (White noise)
    const drumType = this.drums[stepIndex];
    if (drumType > 0) {
      this.playDrum(drumType, t);
    }
  }

  playDrum(type, t) {
    const ctx = this.engine.ctx;
    const bufferSize = Math.floor(ctx.sampleRate * (type === 2 ? 0.08 : 0.025));
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noise = ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = ctx.createBiquadFilter();
    const gain = ctx.createGain();

    if (type === 2) {
      // Snare
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(1000, t);
      gain.gain.setValueAtTime(this.volume * 0.5, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);
      noise.start(t);
      noise.stop(t + 0.08);
    } else {
      // Hi-hat
      filter.type = 'highpass';
      filter.frequency.setValueAtTime(6000, t);
      gain.gain.setValueAtTime(this.volume * 0.2, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.025);
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);
      noise.start(t);
      noise.stop(t + 0.025);
    }
  }
}

class SoundEngine {
  constructor() {
    this.ctx = null;
    this.muted = false;
    this.volume = 0.25;
    this.bgm = new ChiptuneBGM(this);
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    return this.muted;
  }

  startBGM() {
    this.bgm.start();
  }

  stopBGM() {
    this.bgm.stop();
  }

  toggleBGM() {
    return this.bgm.toggle();
  }

  playBombDrop() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(320, t);
    osc.frequency.exponentialRampToValueAtTime(80, t + 0.12);

    gain.gain.setValueAtTime(this.volume * 0.8, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.12);
  }

  playExplosion() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const bufferSize = this.ctx.sampleRate * 0.4;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);

    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(800, t);
    filter.frequency.exponentialRampToValueAtTime(60, t + 0.38);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(this.volume * 1.2, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.38);

    // Add bass boom
    const osc = this.ctx.createOscillator();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(140, t);
    osc.frequency.exponentialRampToValueAtTime(30, t + 0.35);

    const bassGain = this.ctx.createGain();
    bassGain.gain.setValueAtTime(this.volume * 1.0, t);
    bassGain.gain.exponentialRampToValueAtTime(0.001, t + 0.35);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);

    osc.connect(bassGain);
    bassGain.connect(this.ctx.destination);

    noise.start(t);
    osc.start(t);
    noise.stop(t + 0.4);
    osc.stop(t + 0.4);
  }

  playPowerup() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const notes = [330, 440, 554, 659]; // E4, A4, C#5, E5
    notes.forEach((freq, i) => {
      const t = this.ctx.currentTime + i * 0.06;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(this.volume * 0.4, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(t);
      osc.stop(t + 0.08);
    });
  }

  playKick() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(180, t);
    osc.frequency.exponentialRampToValueAtTime(360, t + 0.08);

    gain.gain.setValueAtTime(this.volume * 0.7, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.09);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.09);
  }

  playPunch() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(360, t);
    osc.frequency.exponentialRampToValueAtTime(80, t + 0.1);

    gain.gain.setValueAtTime(this.volume * 1.1, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.1);
  }

  playCurse() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const notes = [220, 207, 196, 174, 130];
    notes.forEach((freq, i) => {
      const t = this.ctx.currentTime + i * 0.07;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(this.volume * 0.45, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.09);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(t);
      osc.stop(t + 0.09);
    });
  }

  playPierce() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    const gain = this.ctx.createGain();

    osc.type = 'square';
    osc.frequency.setValueAtTime(1600, t);
    osc.frequency.exponentialRampToValueAtTime(350, t + 0.14);

    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(1200, t);
    filter.Q.setValueAtTime(3.0, t);

    gain.gain.setValueAtTime(this.volume * 0.6, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.14);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.14);
  }

  playDeath() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const notes = [440, 392, 349, 293, 220];
    notes.forEach((freq, i) => {
      const t = this.ctx.currentTime + i * 0.1;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(this.volume * 0.5, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(t);
      osc.stop(t + 0.12);
    });
  }

  playWin() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const melody = [523, 659, 784, 1046, 784, 1046];
    melody.forEach((freq, i) => {
      const t = this.ctx.currentTime + i * 0.11;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(this.volume * 0.6, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.16);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(t);
      osc.stop(t + 0.16);
    });
  }

  playDoorOpen() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const notes = [440, 554, 659, 880];
    notes.forEach((freq, i) => {
      const t = this.ctx.currentTime + i * 0.08;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      gain.gain.setValueAtTime(this.volume * 0.5, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.2);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(t);
      osc.stop(t + 0.2);
    });
  }

  playWarning() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(600, t);
    osc.frequency.setValueAtTime(900, t + 0.1);

    gain.gain.setValueAtTime(this.volume * 0.4, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.2);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(t);
    osc.stop(t + 0.2);
  }
}

export const sound = new SoundEngine();
export const bgm = sound.bgm;
