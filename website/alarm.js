export class RepeatingAlarm {
  constructor(Context = globalThis.AudioContext || globalThis.webkitAudioContext) {
    this.Context = Context;
    this.context = null;
    this.timer = null;
    this.voices = new Set();
  }
  unlock() {
    if (!this.Context) return;
    this.context ??= new this.Context();
    this.context.resume().catch(() => {});
  }
  pulse() {
    if (!this.context) return;
    const ctx = this.context, oscillator = ctx.createOscillator(), gain = ctx.createGain();
    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
    oscillator.frequency.setValueAtTime(1100, ctx.currentTime + 0.16);
    gain.gain.setValueAtTime(0, ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0.8, ctx.currentTime + 0.008);
    gain.gain.setValueAtTime(0.8, ctx.currentTime + 0.31);
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.33);
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    const voice = { oscillator, gain };
    this.voices.add(voice);
    oscillator.onended = () => {
      oscillator.disconnect(); gain.disconnect(); this.voices.delete(voice);
    };
    oscillator.start(); oscillator.stop(ctx.currentTime + 0.34);
  }
  start() {
    if (this.timer !== null) return;
    this.unlock();
    if (!this.context) return;
    this.pulse();
    this.timer = setInterval(() => this.pulse(), 450);
  }
  stop() {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
    for (const { oscillator, gain } of this.voices) {
      gain.gain.cancelScheduledValues(this.context.currentTime);
      gain.gain.setValueAtTime(0, this.context.currentTime);
      try { oscillator.stop(); } catch {}
      oscillator.disconnect(); gain.disconnect();
    }
    this.voices.clear();
  }
}
