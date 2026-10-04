"""Lightweight, dependency-free sound system for Windows.

Uses the built-in `winsound` module with programmatically-generated
WAV files (via the `wave` + `struct` + `math` stdlib modules).
All playback is asynchronous (SND_ASYNC) so the UI never blocks.
"""

import math
import os
import struct
import threading
import wave

# winsound is Windows-only; gracefully degrade on other platforms
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False

_SAMPLE_RATE = 22050
_SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")


# ── WAV generation helpers ────────────────────────────────────────────

def _ensure_dir():
    os.makedirs(_SOUNDS_DIR, exist_ok=True)


def _write_wav(filepath: str, samples: list[int]):
    """Write 16-bit mono PCM WAV."""
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(b"".join(struct.pack("<h", s) for s in samples))


def _sine_samples(freq: float, duration_s: float, volume: float = 0.5) -> list[int]:
    """Generate sine-wave samples."""
    n = int(_SAMPLE_RATE * duration_s)
    amp = int(32767 * volume)
    return [int(amp * math.sin(2 * math.pi * freq * i / _SAMPLE_RATE)) for i in range(n)]


def _fade(samples: list[int], fade_ms: int = 5) -> list[int]:
    """Apply a tiny fade-in / fade-out to avoid clicks."""
    fade_n = int(_SAMPLE_RATE * fade_ms / 1000)
    out = list(samples)
    for i in range(min(fade_n, len(out))):
        out[i] = int(out[i] * (i / fade_n))
    for i in range(min(fade_n, len(out))):
        out[-(i + 1)] = int(out[-(i + 1)] * (i / fade_n))
    return out


# ── Generate the three sound files ────────────────────────────────────

def _generate_search_tick():
    """Very short, subtle tick."""
    path = os.path.join(_SOUNDS_DIR, "search.wav")
    if os.path.exists(path):
        return path
    _ensure_dir()
    samples = _fade(_sine_samples(880, 0.03, 0.15))
    _write_wav(path, samples)
    return path


def _generate_success():
    """Short pleasant two-tone chime."""
    path = os.path.join(_SOUNDS_DIR, "success.wav")
    if os.path.exists(path):
        return path
    _ensure_dir()
    tone1 = _sine_samples(523, 0.12, 0.35)   # C5
    gap = [0] * int(_SAMPLE_RATE * 0.03)
    tone2 = _sine_samples(784, 0.18, 0.35)    # G5
    samples = _fade(tone1 + gap + tone2)
    _write_wav(path, samples)
    return path


def _generate_path_step():
    """Soft short blip for path animation."""
    path = os.path.join(_SOUNDS_DIR, "path.wav")
    if os.path.exists(path):
        return path
    _ensure_dir()
    samples = _fade(_sine_samples(660, 0.04, 0.12))
    _write_wav(path, samples)
    return path


# ── Public API ────────────────────────────────────────────────────────

class SoundPlayer:
    """Manages optional sound playback.  Thread-safe, non-blocking."""

    def __init__(self):
        self.enabled = True
        # pre-generate on construction (instant; tiny files)
        self._search_wav = _generate_search_tick()
        self._success_wav = _generate_success()
        self._path_wav = _generate_path_step()

    # -- playback (always async) --

    def _play(self, filepath: str):
        if not self.enabled or not _HAS_WINSOUND:
            return
        # SND_ASYNC doesn't block; SND_NOSTOP avoids cutting previous
        try:
            threading.Thread(
                target=winsound.PlaySound,
                args=(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC),
                daemon=True,
            ).start()
        except Exception:
            pass  # never crash the app for a sound glitch

    def play_search_tick(self):
        self._play(self._search_wav)

    def play_success(self):
        self._play(self._success_wav)

    def play_path_step(self):
        self._play(self._path_wav)

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
