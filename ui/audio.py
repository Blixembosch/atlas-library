"""Atlas Library - Çocuklar İçin Ses Efektleri (Web Audio API)."""

from __future__ import annotations

import streamlit as st


def play_chime() -> None:
    """Okuma kaydedildiğinde veya onaylandığında çalan neşeli kısa tını."""
    js = """
    <script>
    (function() {
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
            notes.forEach(function(freq, i) {
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = "sine";
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.12, ctx.currentTime + i * 0.08);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.08 + 0.35);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime + i * 0.08);
                osc.stop(ctx.currentTime + i * 0.08 + 0.35);
            });
        } catch(e) {}
    })();
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


def play_celebration() -> None:
    """Günlük hedef tamamlandığında veya seviye atlandığında çalan kutlama melodisi."""
    js = """
    <script>
    (function() {
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var notes = [523.25, 659.25, 783.99, 1046.50, 1318.51];
            notes.forEach(function(freq, i) {
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = "triangle";
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.15, ctx.currentTime + i * 0.1);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.1 + 0.5);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime + i * 0.1);
                osc.stop(ctx.currentTime + i * 0.1 + 0.5);
            });
        } catch(e) {}
    })();
    </script>
    """
    st.components.v1.html(js, height=0, width=0)
