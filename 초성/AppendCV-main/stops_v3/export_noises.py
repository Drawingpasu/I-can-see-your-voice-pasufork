# 지금 설정(stops_v3.py)의 노이즈 원본을 1초씩 저장
# 음절에 들어간 노이즈와 같은 필터를 쓰며, 길이·크기 모양은 REAPER 등에서 직접 잘라 쓰는 용도
import numpy as np
from scipy.io import wavfile
g = {}
exec(open("stops_v3.py").read().split("outs = {}")[0], g)
SR, ms = g["SR"], g["ms"]
N = SR  # 1초


def save(fn, y):
    y = 0.5 * y / np.max(np.abs(y))
    y[:ms(3)] *= np.linspace(0, 1, ms(3))
    y[-ms(20):] *= np.linspace(1, 0, ms(20))
    wavfile.write(fn, SR, (y * 32767).astype(np.int16))
    print(fn)


# ㄱ: 모인 바람 소리 (버스트 대신 쓰는 1,500-2,200Hz 잡음, 거친 요동 포함)
_, _, band = g["G_SET"]["hump"]
z = g["rng"].standard_normal(N + 2000)
hn = g["sosfilt"](g["bandpass"](*band), z)[2000:]
n_ms = N // ms(1) + 2
wob = g["db"](g["rng"].normal(0, g["G_SET"]["am_db"], n_ms))
save("g_hump.wav", hn / np.std(hn) * np.interp(np.arange(N) / ms(1), np.arange(n_ms), wob))
# ㄱ: 기식 (참고 음원 '카' 분포, 거친 요동 포함)
asp = g["place_asp_noise"]("ㄱ", N)
wob = g["db"](g["rng"].normal(0, g["G_SET"]["am_db"], n_ms))
save("g_asp.wav", asp * np.interp(np.arange(N) / ms(1), np.arange(n_ms), wob))
# ㄷ: 버스트 (L2: 참고 분포 40% + 2,500-9,000Hz 60%)
save("d_burst.wav", g["burst_noise"]("ㄷ", N))
# ㄷ: 기식 (L2: 낮은 쪽 줄이고 3,000-6,000Hz 키운 분포)
save("d_asp.wav", g["place_asp_noise"]("ㄷ", N))
# ㅂ: 버스트 (1,100Hz 이하 + 넓은대역 10%)
save("b_burst.wav", g["burst_noise"]("ㅂ", N))
# 공통: 무성 ㅏ (기식이 모음으로 넘어가는 부분, ㅂ 기식)
save("voiceless_a.wav", g["asp_noise"](N))
