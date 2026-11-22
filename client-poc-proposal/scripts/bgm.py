"""紹介動画用の BGM を、音源素材を使わずにコードで合成する（著作権の心配がないオリジナル曲）。

やわらかい和音（パッド）＋ピアノ風のアルペジオ＋低音に、残響をかけた静かな曲。
使い方: uv run --with numpy --with scipy python bgm.py --duration 100 --out out/bgm.wav
"""

import argparse
import wave

import numpy as np
from scipy.signal import fftconvolve

SR = 44100
BPM = 74
BEAT = 60 / BPM

# 2小節ずつの和音（C の明るく落ち着いた進行）: Cadd9 → Am7 → Fmaj7 → Gsus4
CHORDS = [
    ["C3", "G3", "C4", "D4", "E4"],
    ["A2", "E3", "G3", "C4", "E4"],
    ["F2", "C3", "E3", "A3", "C4"],
    ["G2", "D3", "G3", "C4", "D4"],
]
ARP = [  # 1小節8分音符×8 のアルペジオ（和音ごと）
    ["C4", "G4", "D5", "E5", "G5", "E5", "D5", "G4"],
    ["A3", "E4", "G4", "C5", "E5", "C5", "G4", "E4"],
    ["F3", "C4", "E4", "A4", "C5", "A4", "E4", "C4"],
    ["G3", "D4", "G4", "C5", "D5", "C5", "G4", "D4"],
]
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def freq(name: str) -> float:
    pitch, octave = name[:-1], int(name[-1])
    midi = 12 * (octave + 1) + NOTE[pitch]
    return 440.0 * 2 ** ((midi - 69) / 12)


def piano(f: float, length: float, amp: float) -> np.ndarray:
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(t / 0.006, 1) * np.exp(-t / 0.85)
    partials = [(1, 1.0), (2.001, 0.32), (3.003, 0.10), (4.006, 0.04)]
    sig = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (k - 1) * 0.9) for k, a in partials)
    return amp * env * sig


def pad(freqs: list[float], length: float, amp: float, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(int(length * SR)) / SR
    attack, release = 1.6, 1.8
    env = np.minimum(t / attack, 1) * np.minimum((length - t) / release, 1)
    env = np.clip(env, 0, 1)
    sig = np.zeros_like(t)
    for f in freqs:
        for cents in (-4, 0, 4):
            ff = f * 2 ** (cents / 1200)
            ph = rng.uniform(0, 2 * np.pi)
            sig += np.sin(2 * np.pi * ff * t + ph) + 0.12 * np.sin(4 * np.pi * ff * t + ph)
    return amp * env * sig / (len(freqs) * 3)


def bass(f: float, length: float, amp: float) -> np.ndarray:
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(t / 0.02, 1) * np.exp(-t / 1.6)
    return amp * env * (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t))


def add(buf: np.ndarray, sig: np.ndarray, start: float, pan: float = 0.0) -> None:
    i = int(start * SR)
    if i >= buf.shape[1]:
        return
    n = min(len(sig), buf.shape[1] - i)
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + n] += sig[:n] * left
    buf[1, i:i + n] += sig[:n] * right


def reverb(x: np.ndarray, seconds: float = 2.6, wet: float = 0.32, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.empty_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * t / seconds)
        ir = np.convolve(ir, np.ones(24) / 24, mode="same")  # 高い音をやわらげる
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = (1 - wet) * x[ch] + wet * fftconvolve(x[ch], ir)[: x.shape[1]]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rng = np.random.default_rng(3)
    total = args.duration + 3.0
    buf = np.zeros((2, int(total * SR)))
    bar = BEAT * 4
    t0, k = 0.0, 0
    while t0 < total:
        ci = k % 4
        chord = CHORDS[ci]
        add(buf, pad([freq(n) for n in chord[1:]], bar * 2 + 1.8, 0.16, rng), t0, 0.0)
        for b in range(2):  # 2小節
            add(buf, bass(freq(chord[0]), bar, 0.10), t0 + b * bar, 0.0)
            for j, n in enumerate(ARP[ci]):
                vel = 0.085 if j % 2 == 0 else 0.065
                if b == 1 and j >= 6:
                    continue  # 2小節目の終わりは少し間を空ける
                add(buf, piano(freq(n), 2.4, vel), t0 + b * bar + j * BEAT / 2, -0.35 if j % 2 else 0.35)
        if k % 2 == 1:  # 4小節ごとに高い音を一つ
            add(buf, piano(freq(chord[-1]) * 2, 3.0, 0.035), t0 + bar * 1.5, 0.5)
        t0 += bar * 2
        k += 1

    buf = reverb(buf)
    n = int(args.duration * SR)
    buf = buf[:, :n]
    fade_in, fade_out = int(1.5 * SR), int(3.5 * SR)
    buf[:, :fade_in] *= np.linspace(0, 1, fade_in)
    buf[:, -fade_out:] *= np.linspace(1, 0, fade_out) ** 1.5
    buf *= 0.89 / np.max(np.abs(buf))
    pcm = (buf.T * 32767).astype("<i2")
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"saved {args.out} ({args.duration:.1f}s)")


if __name__ == "__main__":
    main()
