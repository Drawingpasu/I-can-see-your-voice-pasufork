# 9개 파열음의 자음 부분(버스트/모인 바람 소리 + 기식)만 저장. stops_v3.py와 같은 설정·같은 크기
import numpy as np
from scipy.io import wavfile
g = {}
exec(open("stops_v3.py").read(), g)          # 전체 세트도 다시 저장됨
ms, SR, scale = g["ms"], g["SR"], g["scale"]
g["NO_VOWEL"] = True
names = {"가": "g", "카": "k", "까": "kk", "다": "d", "타": "t", "따": "tt", "바": "b", "파": "p", "빠": "pp"}
for syl, name in names.items():
    x = g["cv"](syl) * scale
    nz = np.nonzero(np.abs(x) > 1e-5)[0]
    x = x[nz[0]:nz[-1] + 1]
    wavfile.write(f"{name}_consonant.wav", SR, (x * 32767).astype(np.int16))
    print(f"{syl} {name}_consonant.wav  {len(x) / SR * 1000:4.0f}ms  모음 시작 {g['VOT'][syl]}ms 지점")
