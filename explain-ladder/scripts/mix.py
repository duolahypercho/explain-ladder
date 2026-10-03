"""Mix narration (WORKDIR/vo/*.wav at timeline.json starts) with a soft music bed that ducks under the voice.

  ~/.cache/explain-ladder/venv/bin/python mix.py WORKDIR [--music 1.0] [--no-beat]

Writes WORKDIR/audio.wav (48 kHz stereo). Scene changes get a whoosh + soft hit at each segment boundary.
"""
import argparse, json, os, wave
import numpy as np
from scipy.signal import lfilter, butter

ap = argparse.ArgumentParser()
ap.add_argument("workdir")
ap.add_argument("--music", type=float, default=1.0, help="music bed volume multiplier (0 = voice only)")
ap.add_argument("--no-beat", action="store_true")
a = ap.parse_args()
W = a.workdir
SR = 48000
TL = json.load(open(os.path.join(W, "timeline.json")))
END = TL[-1]["end"]
N = int(SR * END) + SR
rs = np.random.default_rng(5)
out = np.zeros((2, N)); vo = np.zeros(N); mus = np.zeros((2, N))


def T(d):
    return np.arange(int(d * SR)) / SR


def bf(x, fc, kind):
    b, c = butter(2, np.array(fc) / (SR / 2), kind)
    return lfilter(b, c, x)


def put(buf, sig, t, g=1, pan=0):
    i = int(t * SR); n = min(len(sig), N - i)
    if n <= 0:
        return
    if buf.ndim == 1:
        buf[i:i + n] += sig[:n] * g
        return
    buf[0, i:i + n] += sig[:n] * g * np.cos((pan + 1) * np.pi / 4) * 1.414
    buf[1, i:i + n] += sig[:n] * g * np.sin((pan + 1) * np.pi / 4) * 1.414


for s in TL:
    with wave.open(os.path.join(W, "vo", s["id"] + ".wav")) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
    put(vo, x, s["start"])
vo = bf(vo, 90, "high")

# duck the music under the voice
env = np.abs(vo); k = np.exp(-1 / (SR * .15))
env = lfilter([1 - k], [1, -k], env)
env = np.minimum(1, env / (env.max() * .35 + 1e-9))

beat = 60 / 96
prog = [[110, 130.81, 164.81], [87.31, 110, 130.81], [130.81, 164.81, 196], [98, 123.47, 146.83]]  # Am F C G


def saw(fr, d, nh=8):
    t = T(d)
    return sum(np.sin(2 * np.pi * fr * h * t + rs.random() * 6) / h * np.exp(-h * .4) for h in range(1, nh))


t = 0; i = 0
while t < END:
    d = beat * 8; ch = prog[i % 4]; tt = T(d + 1)
    e = np.minimum(1, tt / .8) * np.minimum(1, np.maximum(0, (d + 1 - tt) / 1.0))
    for fq in ch:
        for det, pan in [(1, -.6), (1.005, .6)]:
            put(mus, bf(saw(fq * 2 * det, d + 1), 2200, "low") * e * .05, t, 1, pan)
    put(mus, np.sin(2 * np.pi * ch[0] / 2 * tt) * e * .12, t)
    t += d; i += 1

if not a.no_beat:
    def kick():
        t = T(.4); return np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 8)

    def hat():
        t = T(.05); return bf(rs.standard_normal(len(t)), 8000, "high") * np.exp(-t * 80)

    b = TL[0]["start"]
    while b < END - 2.5:
        put(mus, kick(), b, .35); put(mus, hat(), b + beat / 2, .07, .4); b += beat

mus *= (1 - .6 * env) * a.music


def whoosh(d=.6):
    t = T(d); return bf(rs.standard_normal(len(t)), [300, 4000], "band") * np.sin(np.pi * t / d) ** 2


def hit():
    t = T(1.4)
    return np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 8)) / SR) * np.exp(-t * 3) + bf(rs.standard_normal(len(t)), 800, "low") * np.exp(-t * 8) * .5


for s in TL[1:]:
    bnd = s["start"] - .45
    put(out, whoosh(), bnd - .35, .22, .3); put(out, hit(), bnd - .02, .28)
put(out, hit(), TL[-1]["start"] + TL[-1]["dur"] + .3, .45)

out[0] += vo + mus[0]; out[1] += vo + mus[1]
out = out[:, :int(END * SR)]
out = np.tanh(out * 1.1); out /= np.abs(out).max() / .9
tt = np.arange(out.shape[1]) / SR
out *= np.clip((END - tt) / 1.0, 0, 1)
with wave.open(os.path.join(W, "audio.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out.T * 32767).astype("<i2").tobytes())
print(f"audio.wav {END:.1f}s")
