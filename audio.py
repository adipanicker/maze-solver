"""Lightweight, dependency-free sound system for Windows.

Uses the built-in `winsound` module with programmatically-generated
WAV files (via the `wave` + `struct` + `math` stdlib modules).
Playback runs in a daemon thread so the Tkinter UI never blocks.

If WAV playback fails, falls back to `winsound.Beep()`.
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

_SAMPLE_RATE = 44100          # standard rate — best compatibility
_SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "assets", "sounds")

# Version tag embedded in filenames so stale files get regenerated
_VERSION = "v3"


# ── WAV generation helpers ────────────────────────────────────────────

def _ensure_dir():
    os.makedirs(_SOUNDS_DIR, exist_ok=True)


def _wav_path(name: str) -> str:
    return os.path.join(_SOUNDS_DIR, f"{name}_{_VERSION}.wav")


def _write_wav(filepath: str, samples: list[int]):
    """Write 16-bit mono PCM WAV at _SAMPLE_RATE."""
    raw = struct.pack(f"<{len(samples)}h", *samples)
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(raw)


def _sine(freq: float, duration_s: float, volume: float = 0.5) -> list[int]:
    """Generate sine-wave samples at the given frequency and duration."""
    n_samples = int(_SAMPLE_RATE * duration_s)
    amp = int(32767 * min(volume, 1.0))
    two_pi_f = 2.0 * math.pi * freq
    return [int(amp * math.sin(two_pi_f * i / _SAMPLE_RATE))
            for i in range(n_samples)]


def _fade_in_out(samples: list[int], fade_ms: int = 10) -> list[int]:
    """Apply linear fade-in and fade-out to prevent clicks."""
    fade_n = int(_SAMPLE_RATE * fade_ms / 1000)
    out = list(samples)
    length = len(out)
    for i in range(min(fade_n, length)):
        ratio = i / fade_n
        out[i] = int(out[i] * ratio)
        out[length - 1 - i] = int(out[length - 1 - i] * ratio)
    return out


def _mix(a: list[int], b: list[int]) -> list[int]:
    """Mix two sample lists (same length assumed, or pad shorter)."""
    length = max(len(a), len(b))
    result = []
    for i in range(length):
        sa = a[i] if i < len(a) else 0
        sb = b[i] if i < len(b) else 0
        mixed = sa + sb
        # clamp to 16-bit range
        mixed = max(-32768, min(32767, mixed))
        result.append(mixed)
    return result


# ── Generate the three sound files ────────────────────────────────────

def _generate_search_tick() -> str:
    """~80 ms subtle tick — two quick sine pings."""
    path = _wav_path("search")
    if os.path.exists(path):
        return path
    _ensure_dir()
    tone = _sine(1200, 0.08, 0.25)
    samples = _fade_in_out(tone, fade_ms=8)
    _write_wav(path, samples)
    return path


def _generate_success() -> str:
    """~400 ms pleasant three-tone ascending chime (C5 → E5 → G5)."""
    path = _wav_path("success")
    if os.path.exists(path):
        return path
    _ensure_dir()
    t1 = _sine(523.25, 0.12, 0.40)     # C5
    gap1 = [0] * int(_SAMPLE_RATE * 0.04)
    t2 = _sine(659.25, 0.12, 0.40)     # E5
    gap2 = [0] * int(_SAMPLE_RATE * 0.04)
    t3 = _sine(783.99, 0.20, 0.45)     # G5  (longer, slightly louder)
    samples = _fade_in_out(t1 + gap1 + t2 + gap2 + t3, fade_ms=10)
    _write_wav(path, samples)
    return path


def _generate_path_step() -> str:
    """~60 ms soft blip for path animation."""
    path = _wav_path("path")
    if os.path.exists(path):
        return path
    _ensure_dir()
    tone = _sine(880, 0.06, 0.18)
    samples = _fade_in_out(tone, fade_ms=6)
    _write_wav(path, samples)
    return path


# ── Public API ────────────────────────────────────────────────────────

class SoundPlayer:
    """Manages optional sound playback.  Thread-safe, non-blocking."""

    def __init__(self):
        self.enabled = True
        self._lock = threading.Lock()
        # Pre-generate WAV files (instant — tiny files)
        self._search_wav = _generate_search_tick()
        self._success_wav = _generate_success()
        self._path_wav = _generate_path_step()

    def _play(self, filepath: str, fallback_freq: int = 800,
              fallback_dur: int = 80):
        """Play a WAV file asynchronously.  Falls back to Beep on failure."""
        if not self.enabled or not _HAS_WINSOUND:
            return

        def _worker():
            try:
                # SND_FILENAME: play from file
                # SND_NOSTOP: don't interrupt a currently-playing sound
                winsound.PlaySound(
                    filepath,
                    winsound.SND_FILENAME | winsound.SND_NOSTOP
                )
            except Exception:
                # Fallback: simple beep (blocking, but we're in a thread)
                try:
                    winsound.Beep(fallback_freq, fallback_dur)
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def play_search_tick(self):
        self._play(self._search_wav, fallback_freq=1200, fallback_dur=30)

    def play_success(self):
        self._play(self._success_wav, fallback_freq=600, fallback_dur=300)

    def play_path_step(self):
        self._play(self._path_wav, fallback_freq=880, fallback_dur=40)

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled


# ── Diagnostic / verification ─────────────────────────────────────────

def verify_sounds():
    """Print WAV file diagnostics.  Run as:  python -m audio"""
    print("=== Sound file verification ===\n")
    sp = SoundPlayer()
    for label, fpath in [("search", sp._search_wav),
                         ("success", sp._success_wav),
                         ("path",   sp._path_wav)]:
        exists = os.path.exists(fpath)
        size = os.path.getsize(fpath) if exists else 0
        if exists and size > 0:
            try:
                with wave.open(fpath, "rb") as wf:
                    rate = wf.getframerate()
                    frames = wf.getnframes()
                    channels = wf.getnchannels()
                    sw = wf.getsampwidth()
                    dur_ms = (frames / rate) * 1000
                    print(f"  {label:10s}  OK   "
                          f"rate={rate}  ch={channels}  "
                          f"{sw * 8}-bit  frames={frames}  "
                          f"duration={dur_ms:.1f} ms  "
                          f"size={size} B")
            except Exception as e:
                print(f"  {label:10s}  ERROR reading WAV: {e}")
        else:
            print(f"  {label:10s}  MISSING or EMPTY  (exists={exists}, size={size})")

    print("\nAttempting playback test (success sound)...")
    if _HAS_WINSOUND:
        try:
            winsound.PlaySound(
                sp._success_wav,
                winsound.SND_FILENAME
            )
            print("  Playback completed (check if you heard a chime).")
        except Exception as e:
            print(f"  Playback error: {e}")
    else:
        print("  winsound not available on this platform.")


if __name__ == "__main__":
    verify_sounds()
