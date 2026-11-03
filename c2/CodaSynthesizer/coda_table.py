"""
coda_table.py - 모음팀 dB 표(dBFilter)를 그대로 쓰는 종성 합성 모듈

make_coda(vowel, f0, coda, ...) -> 모음 + 종성 소리 (모음팀과 같은 형식: 48kHz 스테레오 int16 인터리브)

원리
  1) 모음 구간: dBFilter 표를 그대로 읽어 각 배음의 크기로 쓴다 (모음팀 make_sound와 같은 크기 단위).
  2) 종성 구간: 닫힘 목표(포먼트 경로 · 크기 · 코 울림 · 뭉개짐)로 가는 변화를 '비율'로 곱한다.
     모음 표에서 출발하므로 어떤 모음·음높이 뒤에서도 이음매와 전이가 맞는다.
  3) 모음 표는 점이 5~10개뿐이라 포먼트 수치로는 대략만 맞춰 전이 경로의 출발점으로만 쓰고,
     모음 구간의 소리는 표 값 그대로다 (맞춤 오차는 보정 계수가 흡수).
의존: numpy, scipy, 같은 폴더(또는 VowelSynthesizer 패키지)의 dBFilter.py
"""
import os
import numpy as np
from scipy.io import wavfile
from scipy.optimize import least_squares
from scipy.signal import resample_poly

try:
    from v.VowelSynthesizer import dBFilter
except ImportError:
    import dBFilter

HERE = os.path.dirname(os.path.abspath(__file__))
NOISE_DIR = os.environ.get("CODA_NOISE_DIR", HERE)      # b_burst.wav d_burst.wav g_hump.wav (44.1kHz 원본)

TABLES = {"ㅏ": "dBfilterA", "아": "dBfilterA", "ㅐ": "dBfilterE", "애": "dBfilterE", "ㅔ": "dBfilterE", "에": "dBfilterE",
          "ㅣ": "dBfilterI", "이": "dBfilterI", "ㅗ": "dBfilterO", "오": "dBfilterO", "ㅜ": "dBfilterU", "우": "dBfilterU",
          "ㅡ": "dBfilterEU", "으": "dBfilterEU", "ㅓ": "dBfilterEO", "어": "dBfilterEO"}
ASCII = {"ㅂ": "ap", "ㅁ": "am", "ㄷ": "at", "ㄴ": "an", "ㄱ": "ak", "ㅇ": "ang", "ㄹ": "al"}

# ------------------------------------------------------------ 포락선 부품 (coda_synth_final5와 동일)
def res(f, Fc, Q):
    r = f / Fc
    return 1.0 / np.sqrt((1 - r ** 2) ** 2 + (r / Q) ** 2)

def notch(f, Fz, Q):
    r = f / Fz
    return np.sqrt((1 - r ** 2) ** 2 + (r / Q) ** 2) / np.sqrt(1 + r ** 4)

Q1, Q3, Q4, F4 = 5.9, 12.0, 8.0, 3900.0
FN, QN, QZ, PG = 270.0, 5.0, 3.0, 0.15

def envelope(f, F1, F2, F3, Q2, n, Fz, F1v=None, D=0.0, Zv=0.0, qn=None, pg=None, par=0.0, plp=2400.0):
    qn = QN if qn is None else qn; pg = PG if pg is None else pg
    Q2e, Q3e = Q2 * (1 - 0.7 * D), Q3 * (1 - 0.7 * D)
    oral = res(f, F2, Q2e) * res(f, F3, Q3e) * res(f, F4, Q4)
    H = res(f, F1, Q1) * oral
    if n > 0:
        H = H * res(f, FN, qn) ** n * notch(f, Fz, QZ) ** n
        if F1v:
            H = H + n * pg * res(f, F1v, Q1) * oral * notch(f, Fz, QZ)
    if Zv > 0:
        H = H * notch(f, Fz, QZ) ** Zv
    if D > 0:
        H = H * res(f, 600.0, 0.8) ** D
    if par > 0:             # 병렬 포먼트: 직렬(cascade)은 F1이 낮으면 윗소리가 눌리므로 ㄹ에서는 위 포먼트를 따로 살림
        Hp = (res(f, F1, 5.9) / 5.9 + 0.9 * res(f, F2, 8.0) / 8.0 + 0.7 * res(f, F3, 10.0) / 10.0 + 0.15 * res(f, F4, 8.0) / 8.0)
        Hp = Hp / np.sqrt(1 + (f / plp) ** 6)       # 고역 감쇠(약 -18dB/옥타브): 배음이 5kHz까지 평평하게 이어지면 찌르는 소리가 난다
        if D > 0:
            Hp = Hp * res(f, 600.0, 0.8) ** D
        nc, npar = np.sqrt(np.sum(H ** 2)), np.sqrt(np.sum(Hp ** 2))
        H = nc * ((1 - par) * H / nc + par * Hp / npar)
    return H

# ------------------------------------------------------------ 모음 표 읽기 / 포먼트 맞춤
def table_db(vowel, freqs):
    if vowel not in TABLES:
        raise ValueError(f"단모음만 지원합니다 (이중모음은 끝 모음으로): {vowel}")
    arr = getattr(dBFilter, TABLES[vowel])()
    idx = np.clip(np.round(freqs).astype(int) - 1, 0, len(arr) - 1)     # 표는 1Hz 간격, 0번이 1Hz
    return arr[idx]

_FIT = {}
def fit_vowel(vowel):
    """표(260Hz 배수 점)에 F1, F2, Q2, g를 맞춘다. 전이 경로의 출발점으로만 쓴다."""
    key = TABLES[vowel]
    if key in _FIT:
        return _FIT[key]
    f = 260.0 * np.arange(1, 12)
    d = table_db(vowel, f)
    ok = d > -60
    f, tgt = f[ok], 10 ** (d[ok] / 20)
    def cost(p):
        F1, F2, Q2, g = p
        return np.log(g * envelope(f, F1, F2, 2900.0, Q2, 0, 1000.0)) - np.log(tgt)
    best = None
    for F1 in (350, 550, 800, 1050):
        for F2 in (800, 1300, 1900, 2500):
            if F2 <= F1 * 1.1:
                continue
            r = least_squares(cost, [F1, F2, 8, 0.05], bounds=([250, 600, 2, 1e-5], [1300, 3000, 12, 100]))
            if best is None or r.cost < best.cost:
                best = r
    F1, F2, Q2, g = best.x
    _FIT[key] = dict(F1=F1, F2=F2, F3=2900.0, Q2=Q2, g=g, err_db=float(np.sqrt(2 * best.cost / len(f)) * 8.686))
    return _FIT[key]

# ------------------------------------------------------------ 종성 목표값 / 키 목록
PLACE = {"bil": dict(F1=420, F2=700, F3=1900, Fz=1040),
         "alv": dict(F1=420, F2=2450, F3=3550, Fz=1820),
         "vel": dict(F1=420, F2=1600, F3=2200, Fz=2860)}
CODAS = {"ㅂ": ("bil", "stop"), "ㅁ": ("bil", "nasal"), "ㄷ": ("alv", "stop"), "ㄴ": ("alv", "nasal"),
         "ㄱ": ("vel", "stop"), "ㅇ": ("vel", "nasal"), "ㄹ": (None, "lateral")}
BURST = {"ㅂ": dict(file="b_burst.wav", shape="click", ms=5, db=-18, delay=0.065),
         "ㄷ": dict(file="d_burst.wav", shape="click", ms=4, db=-9, delay=0.060)}
# 불파음 '바람 샘' (터뜨림 아님): 닫히기 직전 바람이 새다가 탁 막히며 끊김. 시각은 닫힘 시작 t1 기준(초)
LEAK = {"ㅂ": dict(file="b_burst.wav", db=-20, pre=0.025, post=0.012, rise=0.015, fade=0.002),
        "ㄷ": dict(file="d_burst.wav", db=-16, pre=0.025, post=0.010, rise=0.015, fade=0.002)}
CODA_TAIL = 0.27     # 모음 끝에서 소리가 끝날 때까지 길이(초)

def build_keys(coda, T0, vow, bursts=True, l_style="alvtrans", release="leak", leak_db=None, fast_d=True, leak_over=None):
    TOTAL = T0 + CODA_TAIL
    place, kind = CODAS[coda]
    new = coda in ("ㅂ", "ㄱ", "ㅇ", "ㄹ") or (fast_d and coda == "ㄷ")          # 빠른 닫힘(확정판): ㅁ ㄴ ㄷ은 느린 전이
    if new:
        t1 = T0 + {"stop": 0.03, "nasal": 0.02, "lateral": 0.05}[kind]
    else:
        t1 = T0 + {"stop": 0.07, "nasal": 0.07, "lateral": 0.08}[kind]
    tgt = dict(F1=400, F2=1150, F3=2800, Fz=1800) if kind == "lateral" else PLACE[place]
    def path(name, mid_t, mid_v, end=None):
        v0 = vow[name]
        return [(0, v0), (T0, v0), (mid_t, mid_v), (TOTAL, mid_v if end is None else end)]
    k = {"F1": path("F1", t1, tgt["F1"]), "F2": path("F2", t1, tgt["F2"]), "F3": path("F3", t1, tgt["F3"]),
         "Fz": [(0, tgt["Fz"]), (TOTAL, tgt["Fz"])], "n": [(0, 0), (TOTAL, 0)]}
    if kind == "stop":
        if new:
            k["G"] = [(0, 1), (T0, 1), (T0 + 0.015, 0.7), (t1, 0.12), (t1 + 0.03, 0.04), (t1 + 0.05, 0), (TOTAL, 0)]
            k["D"] = [(0, 0), (T0 + 0.01, 0), (t1, 1.0), (TOTAL, 1.0)]
        else:
            k["G"] = [(0, 1), (T0, 1), (T0 + 0.03, 0.6), (t1, 0.25), (t1 + 0.04, 0.08), (t1 + 0.07, 0), (TOTAL, 0)]
            k["D"] = [(0, 0), (T0 + 0.02, 0), (t1, 1.0), (TOTAL, 1.0)]
        if bursts and coda in BURST and (coda == "ㅂ" or release == "burst" or (leak_over and coda in leak_over)):   # ㄷ은 기본으로 바람/터짐 없음(청취 확정)
            if release == "burst":                       # 이전 방식: 닫힘 뒤 짧은 터짐(틱 소리)
                k["burst"] = (t1 + BURST[coda]["delay"], BURST[coda])
            else:                                        # 바람 샘: 닫히기 직전 새다가 탁 막힘
                spec = dict(LEAK[coda]); spec.update((leak_over or {}).get(coda, {}))
                if leak_db is not None:
                    spec["db"] = leak_db[0] if coda == "ㅂ" else leak_db[1]
                k["leak"] = (t1, spec)
    elif kind == "nasal":
        k["G"] = [(0, 1), (T0, 1), (t1, 0.2), (t1 + 0.06, 0.2), (t1 + 0.09, 0), (TOTAL, 0)]
        if new:
            k["D"] = [(0, 0), (T0 + 0.005, 0), (t1, 0.9), (TOTAL, 0.9)]
            k["n"] = [(0, 0), (T0, 0), (t1, 1), (TOTAL, 1)]
        else:
            k["D"] = [(0, 0), (T0 + 0.02, 0), (t1, 0.85), (TOTAL, 0.85)]
            k["n"] = [(0, 0), (T0, 0), (t1 - 0.02, 1), (TOTAL, 1)]
    if coda == "ㄱ":        # 혀뿌리가 막히는 모델 (버스트 없음) - 청취 확정
        tb = T0 + 0.045
        k["F1"] = path("F1", tb, 400); k["F2"] = path("F2", tb, 1750); k["F3"] = path("F3", tb, 2150)
        k["G"] = [(0, 1), (T0, 1), (tb - 0.012, 0.8), (tb, 0.7), (tb + 0.010, 0.06), (tb + 0.040, 0.03), (tb + 0.060, 0), (TOTAL, 0)]
        k["D"] = [(0, 0), (tb - 0.005, 0), (tb + 0.005, 1.0), (TOTAL, 1.0)]
    if coda == "ㅇ":        # ㄱ과 같은 혀뿌리 막힘 경로 + 비강 울림이 모음 끝부터 이어짐
        ng = dict(level=0.42, hold=0.19, n=3.0, fade=0.03, n_start=-0.04, qn=4.0, pg=None, gcont=True, D=0.9, post_F2=700, post_F3=1900)   # 청취 확정(과장3)
        ng.update((leak_over or {}).get("ㅇ", {}))
        tb = T0 + 0.045
        k["F1"] = path("F1", tb, 400); k["F2"] = path("F2", tb, 1750); k["F3"] = path("F3", tb, 2150)
        for nm_, key_ in (("F2", "post_F2"), ("F3", "post_F3")):     # 막힌 뒤 울림의 윗소리(으 같은 모음 느낌)를 줄이는 경로
            if ng[key_]:
                k[nm_] = k[nm_][:3] + [(tb + 0.015, ng[key_]), (TOTAL, ng[key_])]
        if ng["gcont"]:     # 소리가 뚝 떨어졌다 다시 울리지 않고 모음 크기에서 매끄럽게 울림으로 이어짐
            k["G"] = [(0, 1), (T0, 1), (tb - 0.012, 0.8), (tb, 0.62), (tb + 0.04, ng["level"] * 1.4),
                      (tb + ng["hold"], ng["level"]), (tb + ng["hold"] + ng["fade"], 0), (TOTAL, 0)]
        else:
            k["G"] = [(0, 1), (T0, 1), (tb - 0.012, 0.8), (tb, 0.7), (tb + 0.010, ng["level"]),
                      (tb + ng["hold"], ng["level"]), (tb + ng["hold"] + ng["fade"], 0), (TOTAL, 0)]
        k["D"] = [(0, 0), (tb - 0.005, 0), (tb + 0.005, ng["D"]), (TOTAL, ng["D"])]
        ns = T0 if ng["n_start"] is None else T0 + ng["n_start"]
        k["n"] = [(0, 0), (ns, 0), (tb + 0.005, ng["n"]), (TOTAL, ng["n"])] if ng["n_start"] is not None else [(0, 0), (tb - 0.015, 0), (tb + 0.005, ng["n"]), (TOTAL, ng["n"])]
        if ng["qn"]: k["qn"] = ng["qn"]
        if ng["pg"] is not None: k["pg"] = ng["pg"]
    if coda == "ㄹ":        # 미확정 시험판 (어느 것도 청취로 ㄹ 확정 못 함)
        tl, t2 = T0 + 0.025, T0 + 0.020
        k["Fz"] = [(0, 1900), (TOTAL, 1900)]; k["Z"] = [(0, 0), (TOTAL, 0)]; k["n"] = [(0, 0), (TOTAL, 0)]
        if l_style == "alvtrans":
            k["F1"] = path("F1", t2, 380); k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (t2, 2100), (T0 + 0.040, 1500), (TOTAL, 1500)]
            k["F3"] = [(0, vow["F3"]), (T0, vow["F3"]), (t2, 3400), (T0 + 0.040, 2800), (TOTAL, 2800)]
            k["G"] = [(0, 1), (T0, 1), (t2, 0.5), (T0 + 0.040, 0.35), (T0 + 0.080, 0.35), (T0 + 0.110, 0), (TOTAL, 0)]
            k["D"] = [(0, 0), (T0 + 0.01, 0), (T0 + 0.040, 0.1), (TOTAL, 0.1)]
        elif l_style in ("par_dark", "par_tap", "par_mid", "par_half"):
            # 설측음 /l/: 윗소리(F2·F3)가 살아 있는 지속음. 닫힘처럼 뚝 떨어지거나 비음처럼 저역만 남지 않고,
            # 혀끝이 닿는 동안 크기가 모음의 약 -7dB로 얕게 꺼졌다가 천천히 줄어든다.
            tl = T0 + 0.030
            F2t = {"par_dark": 1150, "par_tap": 1150, "par_mid": 1450, "par_half": 1150}[l_style]
            F3t = {"par_dark": 2800, "par_tap": 2800, "par_mid": 3000, "par_half": 2800}[l_style]
            gl = {"par_dark": 0.45, "par_tap": 0.45, "par_mid": 0.60, "par_half": 0.45}[l_style]
            k["F1"] = path("F1", tl, 380); k["F2"] = path("F2", tl, F2t); k["F3"] = path("F3", tl, F3t)
            pv = 0.5 if l_style == "par_half" else 1.0
            k["par"] = [(0, 0), (T0, 0), (tl, pv), (TOTAL, pv)]
            k["D"] = [(0, 0), (T0 + 0.01, 0), (tl, 0.05), (TOTAL, 0.05)]
            if l_style == "par_tap":    # 끝에서 혀끝이 윗잇몸에 스치듯 닿는 짧은 마무리 (F2 상승 + 빠른 감쇠)
                te = tl + 0.075
                k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tl, F2t), (te, F2t), (te + 0.012, 1900), (TOTAL, 1900)]
                k["G"] = [(0, 1), (T0, 1), (tl, gl), (te, gl), (te + 0.014, 0.0), (TOTAL, 0)]
            else:
                k["G"] = [(0, 1), (T0, 1), (tl, gl), (tl + 0.07, gl), (tl + 0.12, 0), (TOTAL, 0)]
        elif l_style in ("en_dark", "en_tip", "en_soft", "op_a", "op_b", "op_tip", "st_a", "st_b", "st_c"):
            # 영어 어말 어두운 /ɫ/: 입이 열린 채 F1·F2가 완만하게 내려가고 F3는 높게 남는 지속음 (뚝 끊기지 않음).
            # en_*: F1 400 (닫힌 느낌) / op_*: F1을 올려 열린 소리로 (암처럼 닫혀 들리는 문제 보완)
            D_ = dict(f1=400, f2=1000, f3=2800, tg=0.060, g=0.28, par=0.35, hold=0.07, fade=0.06, plp=2400.0, tip=False)
            D_.update({"en_dark": {}, "en_tip": dict(tip=True), "en_soft": dict(g=0.18, par=0.30, fade=0.07, plp=1800.0),
                       "op_a": dict(f1=600, f2=1200, f3=2800, tg=0.050, g=0.42, par=0.45),
                       "op_b": dict(f1=700, f2=1300, f3=2800, tg=0.050, g=0.45, par=0.50),
                       "op_tip": dict(f1=700, f2=1300, f3=2800, tg=0.050, g=0.45, par=0.50, tip=True),
                       # st_*: 혀끝이 닿는 순간 스펙트럼이 10ms 안에 급변하는 설측음 (매끄러운 글라이드 아님)
                       "st_a": dict(f1=360, f2=1100, f3=2900, tg=0.010, g=0.50, par=0.60, hold=0.08, fade=0.05, plp=2800.0),
                       "st_b": dict(f1=360, f2=1350, f3=2900, tg=0.010, g=0.50, par=0.60, hold=0.08, fade=0.05, plp=2800.0),
                       "st_c": dict(f1=360, f2=1350, f3=2900, tg=0.010, g=0.50, par=0.60, hold=0.08, fade=0.05, plp=2800.0, tip=True)}[l_style])
            P = D_
            tg = T0 + P["tg"]; te = tg + P["hold"]
            k["F1"] = path("F1", tg, P["f1"]); k["F2"] = path("F2", tg, P["f2"]); k["F3"] = path("F3", tg, P["f3"])
            k["par"] = [(0, 0), (T0, 0), (tg, P["par"]), (TOTAL, P["par"])]
            k["plp"] = P["plp"]
            k["D"] = [(0, 0), (T0 + 0.01, 0), (tg, 0.05), (TOTAL, 0.05)]
            k["G"] = [(0, 1), (T0, 1), (tg, P["g"]), (te, P["g"]), (te + P["fade"], 0), (TOTAL, 0)]
            if P["tip"]:        # 끝에서 혀끝이 윗잇몸에 가볍게 닿으며 F1이 내려가고 F2가 올라가며 줄어듦
                k["F1"] = [(0, vow["F1"]), (T0, vow["F1"]), (tg, P["f1"]), (te, P["f1"]), (te + 0.025, 330), (TOTAL, 330)]
                k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tg, P["f2"]), (te, P["f2"]), (te + 0.025, 1700), (TOTAL, 1700)]
                k["G"] = [(0, 1), (T0, 1), (tg, P["g"]), (te, P["g"]), (te + 0.025, P["g"] * 0.5), (te + 0.040, 0), (TOTAL, 0)]
        elif l_style in ("tp_a", "tp_b", "tp_c"):
            # 혀끝이 윗잇몸에 닿는 것으로 '끝나는' 설측음: 응 같은 지속 울림으로 끝나지 않고,
            # 열린 모음에서 15ms 만에 혀끝 자리(F2 상승, F1 하강)로 가서 짧게 유지한 뒤 접촉으로 뚝 끊긴다.
            #  tp_a: 접촉 유지 30ms / tp_b: 유지 55ms / tp_c: 접촉 중 소리가 한 번 꺼졌다 약하게 돌아오고(스치는 접촉) 끊김
            tg = T0 + 0.015
            hold = {"tp_a": 0.030, "tp_b": 0.055, "tp_c": 0.0}[l_style]
            te = tg + hold
            f2c, f3c = 1800, 3000
            k["par"] = [(0, 0), (T0, 0), (tg, 0.5), (TOTAL, 0.5)]; k["plp"] = 2800.0
            k["D"] = [(0, 0), (T0 + 0.01, 0), (tg, 0.05), (TOTAL, 0.05)]
            if l_style != "tp_c":
                k["F1"] = [(0, vow["F1"]), (T0, vow["F1"]), (tg, 360), (TOTAL, 360)]
                k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tg, f2c), (TOTAL, f2c)]
                k["F3"] = [(0, vow["F3"]), (T0, vow["F3"]), (tg, f3c), (TOTAL, f3c)]
                k["G"] = [(0, 1), (T0, 1), (tg, 0.55), (te, 0.55), (te + 0.008, 0.0), (TOTAL, 0)]
            else:
                k["F1"] = [(0, vow["F1"]), (T0, vow["F1"]), (tg, 360), (TOTAL, 360)]
                k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tg, f2c), (tg + 0.025, f2c), (tg + 0.050, 1400), (TOTAL, 1400)]
                k["F3"] = [(0, vow["F3"]), (T0, vow["F3"]), (tg, f3c), (TOTAL, f3c)]
                k["G"] = [(0, 1), (T0, 1), (tg, 0.5), (tg + 0.010, 0.12), (tg + 0.025, 0.12), (tg + 0.040, 0.5),
                          (tg + 0.060, 0.45), (tg + 0.068, 0.0), (TOTAL, 0)]
        elif l_style in ("tw_a", "tw_b", "tw_c"):
            # tp_* 보다 끝음이 조금 늘어지는 설측음: 혀끝 접촉(30ms) 뒤 닫히지 않고 입 안 소리(비음 아님)가 서서히 줄어든다.
            #  tw_a: 꼬리 50ms(F2 1500) / tw_b: 꼬리 90ms(F2 1500) / tw_c: 꼬리 70ms, 혀끝 자리(F2 1800) 유지
            tg = T0 + 0.015; te = tg + 0.030
            Tf, g_t, tail = {"tw_a": ((450, 1500, 2800), 0.30, 0.050), "tw_b": ((450, 1500, 2800), 0.30, 0.090),
                             "tw_c": ((420, 1800, 3000), 0.35, 0.070)}[l_style]
            k["par"] = [(0, 0), (T0, 0), (tg, 0.5), (TOTAL, 0.5)]; k["plp"] = 2800.0
            k["D"] = [(0, 0), (T0 + 0.01, 0), (tg, 0.05), (TOTAL, 0.05)]
            k["F1"] = [(0, vow["F1"]), (T0, vow["F1"]), (tg, 360), (te, 360), (te + 0.015, Tf[0]), (TOTAL, Tf[0])]
            k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tg, 1800), (te, 1800), (te + 0.015, Tf[1]), (TOTAL, Tf[1])]
            k["F3"] = [(0, vow["F3"]), (T0, vow["F3"]), (tg, 3000), (te, 3000), (te + 0.015, Tf[2]), (TOTAL, Tf[2])]
            k["G"] = [(0, 1), (T0, 1), (tg, 0.55), (te, 0.55), (te + 0.015, g_t), (te + 0.015 + tail, 0.0), (TOTAL, 0)]
        elif l_style in ("lw_a", "lw_b", "lw_c"):
            # tw_* 보다 에너지를 크게 낮춘 설측음: 모음 끝에서 크기가 확 줄고(코다는 모음보다 훨씬 약함),
            # F1을 높게(450~500Hz) 두어 덜 닫힌 소리로. 혀끝 접촉(30ms) 뒤 약한 꼬리가 70ms 늘어진다.
            #  lw_a: 접촉 -13dB / 꼬리 -16dB, lw_b: -16 / -20dB, lw_c: -20 / -24dB
            tg = T0 + 0.015; te = tg + 0.030
            gc, g_t = {"lw_a": (0.22, 0.15), "lw_b": (0.15, 0.10), "lw_c": (0.10, 0.06)}[l_style]
            k["par"] = [(0, 0), (T0, 0), (tg, 0.5), (TOTAL, 0.5)]; k["plp"] = 2800.0
            k["D"] = [(0, 0), (T0 + 0.01, 0), (tg, 0.05), (TOTAL, 0.05)]
            k["F1"] = [(0, vow["F1"]), (T0, vow["F1"]), (tg, 450), (te, 450), (te + 0.015, 500), (TOTAL, 500)]
            k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tg, 1800), (te, 1800), (te + 0.015, 1700), (TOTAL, 1700)]
            k["F3"] = [(0, vow["F3"]), (T0, vow["F3"]), (tg, 3000), (te, 3000), (te + 0.015, 2900), (TOTAL, 2900)]
            k["G"] = [(0, 1), (T0, 1), (tg, gc), (te, gc), (te + 0.015, g_t), (te + 0.085, 0.0), (TOTAL, 0)]
        elif l_style in ("eul_a", "eul_b", "eul_c", "eul_d", "eul_e", "eul_f"):
            # 유음(흐름소리) '아을': 모음 표(ㅏ)에서 모음팀 ㅡ 표로 약 70ms 매끄럽게 흘러가며 크기가 완만히 줄어든다.
            #  eul_a: -4~-10dB로 줄며 흐름 / eul_b: 더 약하게 / eul_c: eul_a + 중간에 혀가 스치는 짧은 얕은 꺼짐
            tg = T0 + 0.070
            k["F1"] = path("F1", tg, 509); k["F2"] = path("F2", tg, 1431); k["F3"] = path("F3", tg, 2900)
            k["tab"] = "ㅡ"
            xs = np.linspace(0, 1, 8)
            k["u"] = [(0, 0), (T0, 0)] + [(T0 + 0.070 * x, float(0.5 - 0.5 * np.cos(np.pi * x))) for x in xs] + [(TOTAL, 1)]
            if l_style == "eul_a":
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.07, 0.45), (T0 + 0.11, 0.30), (T0 + 0.16, 0.0), (TOTAL, 0)]
            elif l_style == "eul_b":
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.45), (T0 + 0.07, 0.30), (T0 + 0.11, 0.20), (T0 + 0.15, 0.0), (TOTAL, 0)]
            elif l_style == "eul_c":
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.07, 0.45), (T0 + 0.082, 0.18), (T0 + 0.098, 0.40),
                          (T0 + 0.12, 0.30), (T0 + 0.165, 0.0), (TOTAL, 0)]
            else:       # eul_c 바탕으로 끝음(꼬리)만 늘임: d +30ms / e +65ms / f +100ms, 같은 얕은 꺼짐 뒤 완만히 줄어듦
                end = {"eul_d": 0.195, "eul_e": 0.230, "eul_f": 0.265}[l_style]
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.07, 0.45), (T0 + 0.082, 0.18), (T0 + 0.098, 0.40),
                          (T0 + 0.12, 0.30), (T0 + 0.12 + 0.55 * (end - 0.12), 0.18), (T0 + end, 0.0), (TOTAL, 0)]
        elif l_style in ("fl_a", "fl_b", "fl_c"):
            # eul_c 바탕으로 길이는 늘이지 않고, 지속 울림이 앙으로 들리지 않게 '혀끝이 올라가는 순간'에 소리 색이 잠깐 위로 튀는(ㅣ 표 쪽) 움직임을 넣음
            #  fl_a: 중간(+75ms)에 튐 / fl_b: 더 크게 튐, 끝 짧게 / fl_c: 튐이 끝에서 일어나며 사라짐
            tg = T0 + 0.070
            k["F1"] = path("F1", tg, 509); k["F2"] = path("F2", tg, 1431); k["F3"] = path("F3", tg, 2900)
            if l_style == "fl_a":
                k["tabseq"] = [(0, "own"), (T0, "own"), (T0 + 0.040, "ㅡ"), (T0 + 0.058, "ㅣ"), (T0 + 0.082, "ㅣ"), (T0 + 0.100, "ㅡ"), (TOTAL, "ㅡ")]
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.07, 0.40), (T0 + 0.095, 0.30), (T0 + 0.12, 0.25), (T0 + 0.155, 0.0), (TOTAL, 0)]
            elif l_style == "fl_b":
                k["tabseq"] = [(0, "own"), (T0, "own"), (T0 + 0.035, "ㅡ"), (T0 + 0.050, "ㅣ"), (T0 + 0.080, "ㅣ"), (T0 + 0.095, "ㅡ"), (TOTAL, "ㅡ")]
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.065, 0.55), (T0 + 0.09, 0.30), (T0 + 0.115, 0.20), (T0 + 0.14, 0.0), (TOTAL, 0)]
            else:
                k["tabseq"] = [(0, "own"), (T0, "own"), (T0 + 0.050, "ㅡ"), (T0 + 0.110, "ㅣ"), (TOTAL, "ㅣ")]
                k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.08, 0.40), (T0 + 0.11, 0.30), (T0 + 0.135, 0.0), (TOTAL, 0)]
        elif l_style in ("sm_a", "sm_b", "sm_c"):
            # eul_c(ㅏ→ㅡ로 흐름 + 얕은 꺼짐)에 ㅣ 표를 아주 조금, 60ms에 걸쳐 완만히(한(Hann) 곡선) 섞어 위로 살짝 움직이게 함
            #  ㅣ 최대 비율: sm_a 0.18 / sm_b 0.30 / sm_c 0.45  (fl_*는 1.0까지 갑자기 튀어 어색했음)
            wmax = {"sm_a": 0.18, "sm_b": 0.30, "sm_c": 0.45}[l_style]
            tg = T0 + 0.070
            k["F1"] = path("F1", tg, 509); k["F2"] = path("F2", tg, 1431); k["F3"] = path("F3", tg, 2900)
            tm = [(0, (1, 0, 0)), (T0, (1, 0, 0))]
            for x in np.linspace(0, 1, 10)[1:]:
                tt = T0 + 0.070 * x; u_ = 0.5 - 0.5 * np.cos(np.pi * x)
                bump = wmax * (0.5 - 0.5 * np.cos(2 * np.pi * np.clip((tt - (T0 + 0.045)) / 0.060, 0, 1)))
                tm.append((tt, (1 - u_, u_ * (1 - bump), u_ * bump + 0 * bump)))
            for tt in np.linspace(T0 + 0.070, T0 + 0.110, 6)[1:]:
                bump = wmax * (0.5 - 0.5 * np.cos(2 * np.pi * np.clip((tt - (T0 + 0.045)) / 0.060, 0, 1)))
                tm.append((tt, (0, 1 - bump, bump)))
            tm.append((TOTAL, (0, 1, 0)))
            k["tabmix"] = tm
            k["G"] = [(0, 1), (T0, 1), (T0 + 0.04, 0.6), (T0 + 0.07, 0.45), (T0 + 0.082, 0.18), (T0 + 0.098, 0.40),
                      (T0 + 0.12, 0.30), (T0 + 0.165, 0.0), (TOTAL, 0)]
        elif l_style == "flap":
            tc = T0 + 0.015
            k["F1"] = [(0, vow["F1"]), (T0, vow["F1"]), (tc, 380), (tc + 0.012, 380), (tc + 0.030, 480), (TOTAL, 480)]
            k["F2"] = [(0, vow["F2"]), (T0, vow["F2"]), (tc, 1800), (tc + 0.012, 1800), (tc + 0.030, 1450), (TOTAL, 1450)]
            k["F3"] = [(0, vow["F3"]), (T0, vow["F3"]), (tc, 3000), (tc + 0.012, 3000), (tc + 0.030, 2800), (TOTAL, 2800)]
            k["G"] = [(0, 1), (T0, 1), (tc, 0.15), (tc + 0.012, 0.15), (tc + 0.030, 0.4), (tc + 0.070, 0.4), (tc + 0.095, 0), (TOTAL, 0)]
            k["D"] = [(0, 0), (TOTAL, 0)]
            k["burst"] = (tc, dict(file="d_burst.wav", shape="click", ms=3, db=-22))
        else:               # bright
            k["F1"] = path("F1", tl, 380); k["F2"] = path("F2", tl, 1100); k["F3"] = path("F3", tl, 2800)
            k["G"] = [(0, 1), (T0, 1), (tl, 0.35), (tl + 0.055, 0.35), (tl + 0.085, 0), (TOTAL, 0)]
            k["D"] = [(0, 0), (T0 + 0.01, 0), (tl, 0.10), (TOTAL, 0.10)]
    return k

# ------------------------------------------------------------ 터짐 (제공된 잡음 파일)
_NOISE = {}
def noise_slice(name, n, start_s, sr):
    if (name, sr) not in _NOISE:
        s0, w = wavfile.read(os.path.join(NOISE_DIR, name)); w = w.astype(float) / 32768
        if s0 != sr:
            g = np.gcd(int(sr), int(s0)); w = resample_poly(w, int(sr) // g, int(s0) // g)
        _NOISE[(name, sr)] = w
    s = int(round(start_s * sr)); y = _NOISE[(name, sr)][s:s + n].copy()
    return y / np.std(y)

def make_release(spec, vowel_rms, sr):
    ms = lambda x: int(round(sr * x / 1000))
    n = ms(spec["ms"]); n1 = ms(1)
    b = np.zeros(n)
    b[:n1] += noise_slice(spec["file"], n1, 0.100, sr) * np.exp(-np.arange(n1) / ms(0.3))
    b += 0.35 * noise_slice(spec["file"], n, 0.300, sr) * np.exp(-np.arange(n) / (n / 3))
    b[-n1:] *= np.linspace(1, 0, n1)
    b /= np.sqrt(np.mean(b ** 2))
    return b * vowel_rms * 10 ** (spec["db"] / 20)

# ------------------------------------------------------------ 합성
DT = 0.0025
def synth_float(vowel, f0, coda, vowel_dur=0.12, sample_rate=48000, bursts=True, l_style="alvtrans", _vtab=None, release="leak", leak_db=None, fast_d=True, leak_over=None):
    """모음+종성을 float(int16 단위)로 합성"""
    sr = int(sample_rate)
    f0a, f0b = (f0, f0) if np.isscalar(f0) else (f0[0], f0[1])
    T0 = float(vowel_dur); TOTAL = T0 + CODA_TAIL
    fit = fit_vowel(vowel)
    vow = dict(F1=fit["F1"], F2=fit["F2"], F3=fit["F3"])
    keys = build_keys(coda, T0, vow, bursts, l_style, release, leak_db, fast_d, leak_over)
    t1 = keys["F1"][2][0]
    K = int(5720 // min(f0a, f0b))
    ks = np.arange(1, K + 1)
    tf = np.arange(0, TOTAL + DT, DT)
    f0t = np.interp(tf, [0, TOTAL], [f0a, f0b])
    tr = lambda key, t: np.interp(t, *zip(*keys[key]))
    onset = 0.5 - 0.5 * np.cos(np.pi * np.clip(tf / 0.025, 0, 1))
    amps = np.zeros((len(tf), K))
    p_ref = None
    for i, t in enumerate(tf):
        fr = ks * f0t[i]
        taper = np.clip((5720 - fr) / 520, 0, 1)
        # 모음 표 값 (모음팀 generate_sin과 같은 크기 단위: 32767 * 10^((dB-12)/20))
        vtab = (32767 * 10 ** ((table_db(vowel, fr) - 12) / 20)) if _vtab is None else _vtab[i]
        if "tabmix" in keys:     # (own, ㅡ, ㅣ) 세 표의 비율을 시간에 따라 부드럽게 바꿈
            tm = keys["tabmix"]; ts_ = [a for a, _ in tm]
            c_ = [float(np.interp(t, ts_, [m[q] for _, m in tm])) for q in range(3)]
            lin = lambda v: 10 ** ((table_db(v, fr) - 12) / 20)      # 표가 없는(-500dB) 배음이 섞일 때 죽지 않도록 크기(선형)로 섞음
            amps[i] = 32767 * (c_[0] * lin(vowel) + c_[1] * lin("ㅡ") + c_[2] * lin("ㅣ")) * tr("G", t) * onset[i] * taper
            continue
        if "tabseq" in keys:     # 여러 모음 표를 시간 순서로 섞음 (예: ㅏ→ㅡ→ㅣ 잠깐→ㅡ)
            ts_ = [a for a, _ in keys["tabseq"]]; j = int(np.clip(np.searchsorted(ts_, t, side="right") - 1, 0, len(ts_) - 2))
            w = float(np.clip((t - ts_[j]) / (ts_[j + 1] - ts_[j]), 0, 1)); va = keys["tabseq"][j][1]; vb = keys["tabseq"][j + 1][1]
            va = vowel if va == "own" else va; vb = vowel if vb == "own" else vb
            amps[i] = 32767 * 10 ** (((1 - w) * table_db(va, fr) + w * table_db(vb, fr) - 12) / 20) * tr("G", t) * onset[i] * taper
            continue
        if "tab" in keys:        # 유음 '을': 모음 표에서 다른 모음(ㅡ) 표로 dB를 매끄럽게 섞어 흘러감
            u = float(tr("u", t)); dbv = table_db(vowel, fr); dbt = table_db(keys["tab"], fr)
            amps[i] = 32767 * 10 ** (((1 - u) * dbv + u * dbt - 12) / 20) * tr("G", t) * onset[i] * taper
            continue
        env_v = fit["g"] * envelope(fr, fit["F1"], fit["F2"], fit["F3"], fit["Q2"], 0, 1000.0)
        corr0 = vtab / env_v
        defined = table_db(vowel, fr) > -60          # 표에 값이 있는 배음만 음원 보정을 유지, 표가 'X'(무음)인 배음은 보정 없음(1)
        S = np.exp(np.mean(np.log(corr0[defined]))) if defined.any() else 1.0   # 표(int16 단위)와 포락선(단위 1)의 크기 단위 차이
        cpart = S * np.where(defined, np.clip(corr0 / S, 1 / 8, 8), 1.0)
        p = np.clip((t - T0) / (t1 - T0), 0, 1)
        corr = cpart + (corr0 - cpart) * (1 - p)
        env = fit["g"] * envelope(fr, tr("F1", t), tr("F2", t), tr("F3", t), fit["Q2"], float(tr("n", t)),
                                  float(tr("Fz", t)), fit["F1"], float(tr("D", t)),
                                  Zv=(float(tr("Z", t)) if "Z" in keys else 0.0), qn=keys.get("qn"), pg=keys.get("pg"),
                                  par=(float(tr("par", t)) if "par" in keys else 0.0), plp=keys.get("plp", 2400.0))
        a = env * corr
        pr = np.sqrt(np.sum(vtab ** 2))
        if p_ref is None:
            p_ref = pr
        comp = min(pr / np.sqrt(np.sum(a ** 2)), 30.0)
        amps[i] = a * comp * tr("G", t) * onset[i] * taper
    n_samp = int(TOTAL * sr); ts = np.arange(n_samp) / sr
    fi = np.interp(ts, tf, f0t); phase = 2 * np.pi * (np.cumsum(fi) - fi[0]) / sr   # t=0에서 위상 0
    x = np.zeros(n_samp)
    for k in range(K):
        x += np.interp(ts, tf, amps[:, k]) * np.sin((k + 1) * phase)
    lk = keys.get("leak")
    if lk:
        tc, sp = lk
        vowel_rms = np.sqrt(np.sum((32767 * 10 ** ((table_db(vowel, ks * f0a) - 12) / 20)) ** 2) / 2) if _vtab is None else np.sqrt(np.sum(_vtab[0] ** 2) / 2)
        i0, i1 = int((tc - sp["pre"]) * sr), int((tc + sp["post"]) * sr); n = i1 - i0
        env = np.ones(n); r = int(sp["rise"] * sr); env[:r] = 0.5 - 0.5 * np.cos(np.pi * np.arange(r) / r)
        f = int(sp["fade"] * sr); env[-f:] *= np.cos(0.5 * np.pi * np.arange(f) / f) ** 2     # 탁 막히며 끊김
        nz = noise_slice(sp["file"], n, 0.4, sr)
        if sp.get("lp"):                               # 고역 쉬익 소리를 줄여 '츠'처럼 따로 들리지 않게
            from scipy.signal import butter, sosfilt
            nz = sosfilt(butter(4, sp["lp"], "low", fs=sr, output="sos"), nz); nz /= np.std(nz)
        if sp.get("mod"):                              # 성대 맥박에 맞춰 바람을 끊어 모음과 한 소리로 붙게 함
            nz = nz * (0.5 + 0.5 * np.cos(phase[i0:i1])) ** sp["mod"]; nz /= np.sqrt(np.mean(nz ** 2))
        x[i0:i1] += nz * env * vowel_rms * 10 ** (sp["db"] / 20)
    b = keys.get("burst")
    if b:
        t_start, spec = b
        vowel_rms = np.sqrt(np.sum((32767 * 10 ** ((table_db(vowel, ks * f0a) - 12) / 20)) ** 2) / 2) if _vtab is None else np.sqrt(np.sum(_vtab[0] ** 2) / 2)
        y = make_release(spec, vowel_rms, sr)
        i0 = int(t_start * sr); x[i0:i0 + len(y)] += y
    return x

def make_coda(vowel, f0, coda, vowel_dur=0.12, sample_rate=48000, bursts=True, l_style="alvtrans", release="leak", leak_db=None, fast_d=True, leak_over=None, ng_style="op_a"):
    """모음팀 make_sound와 같은 형식(스테레오 int16 인터리브)으로 '모음+종성'을 돌려준다.
    vowel: 'ㅏ' 'ㅐ' 'ㅔ' 'ㅣ' 'ㅗ' 'ㅜ' 'ㅡ' 'ㅓ' (또는 아 애 에 이 오 우 으 어)
    f0: 숫자 또는 (시작, 끝) 튜플 / coda: ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ / vowel_dur: 모음 정상 구간(초)
    bursts=False 면 ㅂ·ㄷ 끝의 바람/터짐을 뺀다. release='leak'(기본: 새다가 탁 막힘) / 'burst'(옛 터짐). leak_db=(ㅂ,ㄷ) dB로 세기 조절. ㄹ은 미확정 시험판."""
    if coda == "ㅇ" and ng_style == "op_a":      # 앙: 열린 지속음 방식(op_a) 청취 지정. ng_style="nasal" 이면 이전 비강 울림 방식
        coda, l_style = "ㄹ", "op_a"
    x = synth_float(vowel, f0, coda, vowel_dur, sample_rate, bursts, l_style, None, release, leak_db, fast_d, leak_over)
    if np.abs(x).max() > 32767:
        raise ValueError("진폭이 16비트를 넘음")
    m = np.round(x).astype(np.int16)
    return np.column_stack((m, m)).flatten()
