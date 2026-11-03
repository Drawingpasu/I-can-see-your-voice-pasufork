# 파열음 합성 v3 (참고 음원 측정값을 반영한 버전)
#
# 바뀐 점 (참고 음원: Typecast '지안'이 읽은 가카까/다타따/바파빠/아가/아다/아바)
#  1. F0: 평음은 낮게(약 250 -> 230Hz로 내려감), 격음·경음은 높게(약 310~330Hz)
#  2. 기식: 작게 시작해서 모음 쪽으로 갈수록 커짐 (이전과 반대)
#  3. 평음 기식은 격음만큼 셈, VOT도 평음이 더 김
#  4. 버스트는 모음보다 10dB 이상 작게
#  5. 모음 시작: 평음·격음은 35ms에 걸쳐 커지고, 경음은 바로 시작
#  6. 모음 사이 폐쇄: 성대 진동이 -20dB에서 시작해 사라짐, 버스트 아주 약함
#  7. 발성 유형별 H1-H2 (박선영·성철재 2022 표 5의 경향: 경음 < 평음 < 격음)
#
# 모음은 받은 '아' 파일의 배음 크기(스펙트럼 모양)를 그대로 쓰고 F0만 바꿔서 다시 합성한다.

import numpy as np
from scipy.signal import butter, sosfilt, firwin2, lfilter
from scipy.io import wavfile

SR = 44100
rng = np.random.default_rng(21)


def ms(x):
    return int(round(SR * x / 1000))


def lowpass(f):
    return butter(2, f, btype="lowpass", fs=SR, output="sos")


def bandpass(lo, hi):
    return butter(2, [lo, hi], btype="bandpass", fs=SR, output="sos")


# ------------------------------------------------------------
# 모음 스펙트럼 모양: 받은 '아' 파일에서 측정한 배음 크기 (dB)
# ------------------------------------------------------------
A_FREQ = np.array([260, 520, 780, 1040, 1300, 1560])
A_DB = np.array([-29, -14, -12, 0, -1, -4])


def env_db(f, warp=(1.0, 1.0)):
    lo, hi = warp
    r = np.clip((f - 1000) / 400, 0, 1)
    w = lo + (hi - lo) * r
    return np.interp(f / w, A_FREQ, A_DB, left=-29, right=-95)


# 조음 위치별 포먼트 전이 (자음 쪽 끝에서의 배율)
WARP = {"ㄱ": (1.25, 1.25), "ㄷ": (0.90, 1.18), "ㅂ": (0.75, 0.75), "ㅁ": (0.75, 0.75)}


# ------------------------------------------------------------
# 배음 합성기: 1ms 단위로 F0, 크기, 전이, H1 보정을 받아 연속으로 합성
# ------------------------------------------------------------
def synth(f0_ms, gain_ms, warp_ms, h1_ms, closure_db=None):
    # f0_ms, gain_ms, h1_ms: 길이 N(ms)의 배열 / warp_ms: (N, 2)
    # closure_db: 폐쇄 구간에서 쓸 배음 크기 [N, 6] (None이면 모음)
    n_ms = len(f0_ms)
    n = ms(n_ms)
    tt = np.arange(n) * 1000 / SR
    f0 = np.interp(tt, np.arange(n_ms), f0_ms)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    out = np.zeros(n)
    max_h = int(1700 / f0_ms.min()) + 1
    for h in range(1, max_h + 1):
        a_ms = np.zeros(n_ms)
        for i in range(n_ms):
            fh = f0_ms[i] * h
            db = env_db(fh, tuple(warp_ms[i]))
            if h == 1:
                db += h1_ms[i]
            if closure_db is not None and not np.isnan(closure_db[i, 0]):
                db = closure_db[i, min(h - 1, 5)] if h <= 6 else -95
            a_ms[i] = 10 ** (db / 20) * gain_ms[i]
        out += np.interp(tt, np.arange(n_ms), a_ms) * np.sin(h * phase)
    return out


# ------------------------------------------------------------
# 잡음 재료
# ------------------------------------------------------------
# 참고 음원에서 측정한 대역별 에너지 비율 (dB)
#   대역: 0-500, 500-1000, 1000-1500, 1500-2000, 2000-3000, 3000-4000, 4000-6000, 6000-10000 Hz
BANDS = [(0, 500), (500, 1000), (1000, 1500), (1500, 2000), (2000, 3000), (3000, 4000), (4000, 6000), (6000, 10000)]
PROFILE = {
    # 버스트 첫 10ms: ㄱ = 가·카·까 평균, ㄷ = 다·타·따 평균
    "burst_ㄱ": [-9.6, -12.6, -14.9, -2.5, -13.8, -27.0, -15.3, -22.8],
    "burst_ㄷ": [-1.1, -9.7, -18.2, -19.2, -18.4, -19.9, -16.7, -18.3],
    # 기식 가운데 20ms: ㄱ = 가·카 평균, ㄷ = 다·타 평균
    "asp_ㄱ": [-20.7, -18.8, -7.4, -4.9, -8.7, -10.2, -8.2, -19.4],
    "asp_ㄷ": [-5.8, -14.4, -5.6, -9.3, -10.3, -10.0, -12.3, -22.0],
    # 참고 음원 카의 기식만 (1,500-2,000Hz에 뾰족하게 모임)
    "asp_ka": [-22.2, -17.2, -8.2, -3.1, -9.0, -14.1, -7.9, -21.5],
    # ㄷ 기식에서 낮은 쪽(0-500Hz)을 줄이고 3,000-6,000Hz를 키운 것 (ㅂ과 덜 헷갈리게)
    "asp_ㄷ_hi": [-15.0, -14.4, -6.6, -9.3, -8.3, -6.0, -7.3, -16.0],
}
_FIR = {}


def profile_filter(name, shift=1.0):
    # 대역별 에너지 비율 -> 주파수별 크기(진폭)로 바꿔 FIR 필터를 만든다
    # shift > 1이면 분포 전체를 그 배율만큼 높은 주파수로 옮긴다
    key = (name, shift)
    if key not in _FIR:
        prof = PROFILE[name]
        amps = np.array([np.sqrt(10 ** (d / 10) / (hi - lo)) for (lo, hi), d in zip(BANDS, prof)])
        amps = amps / max(amps)                     # 대역 에너지 / 대역 폭 = 1Hz당 에너지 -> 진폭
        f, g = [], []
        for (lo, hi), a in zip(BANDS, amps):        # 대역 안은 평평하게, 경계에서만 바뀌게
            lo2, hi2 = lo * shift, min(hi * shift, 11500)
            if lo2 >= 11500:
                break
            f += [lo2 + (60 if lo2 > 0 else 0), hi2 - 60]
            g += [a, a]
        f += [12000.0, SR / 2]
        g += [g[-1] * 0.3, 0.0]
        _FIR[key] = firwin2(1023, f, g, fs=SR)
    return _FIR[key]


# ㄱ 설정: 음역대(shift)와 거친 정도
#   am_db  : 1ms 단위로 크기가 무작위로 요동치는 정도 (dB)
#   spikes : 기식 중에 작은 파열이 튀는 횟수
#   burst_add : ㄱ 버스트 크기 보정 (dB, 음수면 약하게)
#   asp_add   : ㄱ 기식 크기 보정 (시작 dB, 모음 직전 dB)
#   onset_db  : 지정하면 ㄱ의 버스트·작은 파열 크기를 발성 유형과 상관없이 이 값으로 (까에서 통한 시작을 가·카에도)
#   spike_ms  : 지정하면 작은 파열을 버스트 뒤 이 시간(ms) 안에 몰아서 넣음
#   asp_prof  : ㄱ 기식에 쓸 분포 ("asp_ㄱ" = 가·카 평균, "asp_ka" = 참고 음원 카)
# 기본값 = K2 (청취로 '가'로 들린 설정)
#   충격음 없이, 1,500-2,200Hz에 모인 바람 소리 15ms로 시작 -> 참고 음원 '카' 분포의 거친 기식
G_SET = {"shift": 1.0, "am_db": 3.5, "spikes": 0, "burst_add": 0.0, "asp_add": (8, 2),
         "onset_db": None, "spike_ms": None, "asp_prof": "asp_ka",
         "no_click": True, "hump": (15, -10, (1500, 2200))}
# ㄷ 설정
#   hi_mix   : ㄷ 버스트에 섞는 높은 주파수 잡음 비율 (0이면 참고 음원 분포 그대로)
#   hi_cut   : 높은 주파수 잡음의 하한 (Hz)
#   burst_add: ㄷ 버스트 크기 보정 (dB)
#   asp_prof : ㄷ 기식 분포 이름
# 기본값 = L2 (청취로 '다'가 '바'와 갈린 설정)
D_SET = {"hi_mix": 0.6, "hi_cut": 2500, "burst_add": 4.0, "asp_prof": "asp_ㄷ_hi"}
#   no_click : True면 ㄱ의 버스트(충격음)와 작은 파열을 빼고, 잡음이 2~3ms에 걸쳐 시작하게
#   hump     : (길이ms, 크기dB, (낮은Hz, 높은Hz)) 버스트 대신 넣는 '모인 바람 소리' (연구개음 마찰)


def burst_noise(place, n):
    z = rng.standard_normal(n + 2000)
    if place == "ㅂ":
        a = sosfilt(lowpass(1100), z); out = a / np.std(a) + 0.10 * z
    else:
        shift = G_SET["shift"] if place == "ㄱ" else 1.0
        out = lfilter(profile_filter("burst_" + place, shift), 1, z)
        if place == "ㄷ" and D_SET["hi_mix"] > 0:
            # 높은 주파수 쪽으로 갈수록 커지는 잡음을 섞음 (치조음 버스트의 상승형 스펙트럼)
            hp = sosfilt(butter(2, [D_SET["hi_cut"], 9000], btype="bandpass", fs=SR, output="sos"), z)
            out = (1 - D_SET["hi_mix"]) * out / np.std(out[2000:]) + D_SET["hi_mix"] * hp / np.std(hp[2000:])
    out = out[2000:]
    return out / np.std(out)


def place_asp_noise(place, n):
    # 조음 위치 색을 가진 기식 (ㄱ, ㄷ: 참고 음원의 기식 분포)
    z = rng.standard_normal(n + 2000)
    shift = G_SET["shift"] if place == "ㄱ" else 1.0
    name = G_SET["asp_prof"] if place == "ㄱ" else (D_SET["asp_prof"] if place == "ㄷ" else "asp_" + place)
    out = lfilter(profile_filter(name, shift), 1, z)[2000:]
    return out / np.std(out)


def asp_noise(n):
    # 무성 ㅏ (받은 '아'의 포먼트 F1 1060, F2 1490 + F3 2700)
    z = rng.standard_normal(n + 2000)
    out = np.zeros(n + 2000)
    for f, amp, bw in [(1060, 1.0, 250), (1490, 0.7, 300), (2700, 0.4, 400)]:
        p = sosfilt(bandpass(f - bw / 2, f + bw / 2), z)
        out += amp * p / np.std(p)
    out = out[2000:]
    return out / np.std(out)


def make_burst(place, n_ms):
    n, n1 = ms(n_ms), ms(1)
    b = np.zeros(n)
    b[:n1] += burst_noise(place, n1) * np.exp(-np.arange(n1) / ms(0.3))
    b += 0.35 * burst_noise(place, n) * np.exp(-np.arange(n) / (n / 3))
    if place == "ㄱ":
        for d, s in [(3, 0.5), (6, 0.3)]:
            if ms(d) + n1 < n:
                b[ms(d):ms(d) + n1] += s * burst_noise(place, n1) * np.exp(-np.arange(n1) / ms(0.3))
    b[-ms(1):] *= np.linspace(1, 0, ms(1))
    return b / np.sqrt(np.mean(b ** 2))


def db(x):
    return 10 ** (x / 20)


# ------------------------------------------------------------
# 어두 CV 설정
#   VOT: 참고 음원 측정값 (파는 측정이 불안정해서 바·카 사이 값으로 둠)
#   F0: (시작, 50ms 뒤, 끝)
#   기식: (시작 dB, 모음 직전 dB)  모음 RMS 기준
#   H1 보정: 경음 -4dB(단단한 발성), 격음 +3dB(숨 섞인 발성)
# ------------------------------------------------------------
TYPE = {
    #      F0 (시작, 50ms 뒤, 끝)   기식 (시작, 끝)   모음 페이드인  H1 보정   버스트 dB
    "평": ((252, 232, 215),        (-27, -3),        35,            0,        -14),
    "격": ((318, 326, 300),        (-25, -5),        35,            +3,       -11),
    "경": ((326, 310, 285),        None,             4,             -4,       -10),
}
# 설정값 = 참고 음원 VOT - 10ms (기식이 모음 앞부분과 겹쳐서, 같은 방법으로 재면 10ms 길게 나오기 때문)
VOT = {"가": 80, "다": 66, "바": 44, "카": 48, "타": 30, "파": 40, "까": 10, "따": 14, "빠": 8}
PLACE = {"가": "ㄱ", "카": "ㄱ", "까": "ㄱ", "다": "ㄷ", "타": "ㄷ", "따": "ㄷ", "바": "ㅂ", "파": "ㅂ", "빠": "ㅂ"}
KIND = {"가": "평", "다": "평", "바": "평", "카": "격", "타": "격", "파": "격", "까": "경", "따": "경", "빠": "경"}
BURST_MS = {"ㄱ": 10, "ㄷ": 7, "ㅂ": 5}
VOWEL_MS, TRANS_MS = 300, 40
VOWEL_RMS = 0.15
NO_VOWEL = False      # True면 자음 부분만 만듦 (자음 파일 뽑을 때)


def cv(syl):
    place, kind = PLACE[syl], KIND[syl]
    (f_s, f_m, f_e), asp, fade, h1, burst_db = TYPE[kind]
    vot = VOT[syl]

    # 모음 1ms 단위 설정
    N = VOWEL_MS
    t = np.arange(N)
    f0 = np.interp(t, [0, 50, N - 1], [f_s, f_m, f_e])
    gain = np.ones(N)
    gain[:fade] = np.linspace(0.3 if fade > 10 else 0.6, 1, fade)
    gain[-60:] *= np.linspace(1, 0, 60)
    k = np.clip(t / TRANS_MS, 0, 1)[:, None]
    w0 = np.array(WARP[place])
    warp = w0 + (1 - w0) * k
    h1v = h1 * np.clip(1 - t / 60, 0, 1)            # H1 보정은 모음 앞 60ms 동안만
    vowel = synth(f0, gain, warp, h1v)
    vowel *= VOWEL_RMS / np.sqrt(np.mean(vowel[ms(80):ms(200)] ** 2))

    total = ms(80) + ms(vot) + len(vowel) + ms(200)
    out = np.zeros(total)
    start = ms(80)

    # ㄱ 보정 (버스트 약하게, 기식 세게)
    if place == "ㄱ":
        burst_db = burst_db + G_SET["burst_add"]
        if G_SET["onset_db"] is not None:
            burst_db = G_SET["onset_db"]
        if asp is not None:
            asp = (asp[0] + G_SET["asp_add"][0], asp[1] + G_SET["asp_add"][1])

    if place == "ㄷ":
        burst_db = burst_db + D_SET["burst_add"]

    # 버스트
    if place == "ㄱ" and G_SET["no_click"]:
        if G_SET["hump"] is not None:
            # 충격음 대신, 1,500~2,000Hz 근처에 모인 거친 바람 소리가 3ms에 걸쳐 시작해서 서서히 줄어듦
            h_ms, h_db, band = G_SET["hump"]
            if kind == "경":
                h_ms = min(h_ms, 10)          # 까: 기식이 없으니 모인 바람 소리만 10ms
            n_h = ms(h_ms)
            z = rng.standard_normal(n_h + 2000)
            hn = sosfilt(bandpass(*band), z)[2000:]
            hn /= np.std(hn)
            env = np.ones(n_h)
            env[:ms(3)] = np.linspace(0, 1, ms(3)) ** 2
            env *= np.linspace(1, 0.25, n_h)
            n_ms = n_h // ms(1) + 2
            wob = db(rng.normal(0, G_SET["am_db"], n_ms))
            env *= np.interp(np.arange(n_h) / ms(1), np.arange(n_ms), wob)
            out[start:start + n_h] += hn * env * VOWEL_RMS * db(h_db)
    else:
        b = make_burst(place, BURST_MS[place]) * VOWEL_RMS * db(burst_db)
        out[start:start + len(b)] += b

    # 기식: 작게 시작해서 모음 직전에 가장 커짐, 모음 앞부분 20ms 밑으로 이어짐
    if asp is not None:
        n_asp = ms(vot + 20)
        noise = asp_noise(n_asp)
        if place in ("ㄱ", "ㄷ"):
            pcol = place_asp_noise(place, n_asp)
            # 조음 위치 색 -> 모음 색: 모음 시작 15ms 전부터 바뀜
            mix = np.clip((np.arange(n_asp) - (ms(vot) - ms(15))) / ms(30), 0, 1)
            noise = (1 - mix) * pcol + mix * noise
        else:
            bcol = burst_noise(place, n_asp)
            mix = np.clip(np.arange(n_asp) / ms(10), 0, 1)
            noise = (1 - mix) * bcol + mix * noise
        lvl_db = np.interp(np.arange(n_asp), [0, ms(vot), n_asp - 1], [asp[0], asp[1], asp[1] - 14])
        if place == "ㄱ" and G_SET["am_db"] > 0:
            # 1ms마다 크기가 무작위로 요동 (연구개음 특유의 거친 마찰), 모음에 가까워질수록 줄어듦
            n_ms = int(np.ceil(n_asp / ms(1))) + 1
            wob = rng.normal(0, G_SET["am_db"], n_ms) * np.clip(1 - np.arange(n_ms) / (vot + 5), 0.2, 1)
            lvl_db = lvl_db + np.interp(np.arange(n_asp) / ms(1), np.arange(n_ms), wob)
        env = db(lvl_db)
        rise = ms(3) if (place == "ㄱ" and G_SET["no_click"]) else ms(2)
        env[:rise] *= np.linspace(0, 1, rise) ** 2
        out[start + ms(2):start + ms(2) + n_asp] += (noise * env * VOWEL_RMS)[:total - start - ms(2)]

    # ㄱ: 혀 뒤쪽이 떨어지면서 작은 파열이 여러 번 튐
    if place == "ㄱ" and G_SET["spikes"] > 0 and not G_SET["no_click"]:
        span = G_SET["spike_ms"] if G_SET["spike_ms"] else max(vot * 0.7, 8)
        times = np.sort(rng.uniform(3, span, G_SET["spikes"]))
        for i, tm in enumerate(times):
            n1 = ms(1.5)
            sp = burst_noise("ㄱ", n1) * np.exp(-np.arange(n1) / ms(0.4))
            size = db(burst_db + 2) * (1 - 0.6 * i / max(G_SET["spikes"], 1))
            p0 = start + ms(tm)
            out[p0:p0 + n1] += sp * size * VOWEL_RMS

    v0 = start + ms(vot)
    if not NO_VOWEL:
        out[v0:v0 + len(vowel)] += vowel
    return out


# ------------------------------------------------------------
# 모음 사이 VCV (아가, 아다, 아바, 아마)
#   폐쇄: ㄱ 60, ㄷ 60, ㅂ 65ms (참고 음원), ㅁ 70ms
#   폐쇄 중 성대 진동: 모음 대비 약 -18dB -> -40dB로 줄어듦 (ㅁ은 비음으로 계속 울림)
#   첫 모음 F0 215 -> 208Hz, 두 번째 모음 240 -> 200Hz
# ------------------------------------------------------------
CLOSE = {"ㄱ": 60, "ㄷ": 60, "ㅂ": 65, "ㅁ": 70}
# 모음 사이 개방 소리 (모음 대비 dB)
#   ㄱ: 충격음 없이 1,500-2,200Hz에 모인 거친 바람 소리 (어두 ㄱ K2와 같은 원리)
#   ㄷ: 짧고 날카로운 높은 버스트 (어두 ㄷ L2와 같은 원리)
#   ㅂ: 아주 약한 낮은 버스트
VCV_BURST = {"ㄱ": -10, "ㄷ": -9, "ㅂ": -18}
# 개방 뒤 두 번째 모음이 커지기 전까지의 시간 (참고 음원: 아가 약 16ms, 아다·아바 약 10ms)
VCV_VOT = {"ㄱ": 16, "ㄷ": 10, "ㅂ": 10, "ㅁ": 0}
NASAL_DB = [-6, -14, -24, -32, -26, -24]


def vcv(place):
    # 구간: 첫 모음 V1 | 폐쇄 C | 개방 뒤 짧은 VOT 구간 VV | 두 번째 모음 V2
    V1, C, V2 = 250, CLOSE[place], 320
    VV = VCV_VOT[place]
    N = V1 + C + VV + V2
    t = np.arange(N)
    rel_ms = V1 + C                                      # 개방 시점
    v2_ms = rel_ms + VV                                  # 두 번째 모음 시작
    f0 = np.interp(t, [0, V1, rel_ms, v2_ms + 60, N - 1], [218, 208, 232, 238, 200])

    gain = np.ones(N)
    gain[:15] = np.linspace(0, 1, 15)
    gain[V1 - 20:V1] = np.linspace(1, 0.35, 20)          # 첫 모음이 자음 쪽으로 20ms에 걸쳐 줄어듦
    if place != "ㅁ":
        gain[v2_ms:v2_ms + 15] = np.linspace(0.25, 1, 15)  # 두 번째 모음은 15ms에 걸쳐 커짐
    gain[-60:] *= np.linspace(1, 0, 60)

    w0 = np.array(WARP[place])
    warp = np.ones((N, 2))
    for i in range(N):
        if i < V1:
            k = np.clip((i - (V1 - TRANS_MS)) / TRANS_MS, 0, 1)
        elif i < v2_ms:
            k = 1
        else:
            k = 1 - np.clip((i - v2_ms) / TRANS_MS, 0, 1)
        warp[i] = 1 + (w0 - 1) * k

    clo = np.full((N, 6), np.nan)
    for i in range(V1, rel_ms):
        r = (i - V1) / C
        if place == "ㅁ":
            clo[i] = NASAL_DB
        else:
            base = -12 + (-38 + 12) * r                  # 폐쇄 중 성대 진동: 약 -18dB에서 -40dB로 줄어듦
            clo[i] = [base, base - 12, -95, -95, -95, -95]
    for i in range(rel_ms, v2_ms):                        # 개방 뒤 VOT 구간: 약한 성대 진동만 다시 시작
        clo[i] = [-26, -36, -95, -95, -95, -95]
    x = synth(f0, gain, warp, np.zeros(N), clo)
    for edge, length in [(V1, 4), (rel_ms, 2), (v2_ms, 3)]:
        a, b_ = ms(edge) - ms(length), ms(edge) + ms(length)
        x[a:b_] = np.convolve(x[a:b_].copy(), np.ones(16) / 16, mode="same")
    x *= VOWEL_RMS / np.sqrt(np.mean(x[ms(80):ms(200)] ** 2))

    # 개방 소리 + VOT 구간의 잡음
    rel = ms(rel_ms)
    n_noise = ms(VV + 8)                                  # 두 번째 모음 시작 뒤 8ms까지 이어짐
    if place == "ㄱ":
        # 충격음 없이 1,500-2,200Hz에 모인 거친 바람 소리
        _, _, band = G_SET["hump"]
        z = rng.standard_normal(n_noise + 2000)
        hn = sosfilt(bandpass(*band), z)[2000:]
        hn /= np.std(hn)
        env = np.ones(n_noise)
        env[:ms(3)] = np.linspace(0, 1, ms(3)) ** 2
        env *= np.linspace(1, 0.15, n_noise)
        n_ms = n_noise // ms(1) + 2
        env *= np.interp(np.arange(n_noise) / ms(1), np.arange(n_ms), db(rng.normal(0, G_SET["am_db"], n_ms)))
        x[rel:rel + n_noise] += hn * env * VOWEL_RMS * db(VCV_BURST["ㄱ"])
    elif place in ("ㄷ", "ㅂ"):
        # 짧은 버스트 + 그 뒤 짧은 기식 (ㄷ은 L2의 높은 기식 분포)
        bu = make_burst(place, 4 if place == "ㄷ" else 5) * VOWEL_RMS * db(VCV_BURST[place])
        x[rel:rel + len(bu)] += bu
        an = place_asp_noise("ㄷ", n_noise) if place == "ㄷ" else burst_noise("ㅂ", n_noise)
        env = np.linspace(1, 0.1, n_noise)
        env[:ms(2)] *= np.linspace(0, 1, ms(2))
        x[rel:rel + n_noise] += an * env * VOWEL_RMS * db(VCV_BURST[place] - 8)
    return np.concatenate([np.zeros(ms(80)), x, np.zeros(ms(200))])


# ------------------------------------------------------------
# 저장
# ------------------------------------------------------------
def save(fn, x):
    wavfile.write(fn, SR, (x * 32767).astype(np.int16))


outs = {}
for syl in ["가", "카", "까", "다", "타", "따", "바", "파", "빠"]:
    outs[syl] = cv(syl)
for place, name in [("ㄱ", "아가"), ("ㄷ", "아다"), ("ㅂ", "아바"), ("ㅁ", "아마")]:
    outs[name] = vcv(place)

peak = max(np.max(np.abs(v)) for v in outs.values())
scale = 0.9 / peak
roman = {"가": "ga", "카": "ka", "까": "kka", "다": "da", "타": "ta", "따": "tta",
         "바": "ba", "파": "pa", "빠": "ppa", "아가": "aga", "아다": "ada", "아바": "aba", "아마": "ama"}
for k, v in outs.items():
    save(f"v3_{roman[k]}.wav", v * scale)

gap = np.zeros(ms(250))
line_gap = np.zeros(ms(500))
seq = []
for line in [["가", "카", "까"], ["다", "타", "따"], ["바", "파", "빠"], ["아가"], ["아다"], ["아바"], ["아마"]]:
    for s in line:
        seq += [outs[s] * scale, gap]
    seq.append(line_gap)
save("v3_all.wav", np.concatenate(seq))
print("저장 완료")
