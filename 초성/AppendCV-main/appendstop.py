import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from CodaSynthesizer import appendcoda

#초성 파열음(ㄱㅋㄲ ㄷㅌㄸ ㅂㅍㅃ) 붙이는 코드. appendcvc.append()에서 파열음이나 종성이 있으면 여기로 넘어옴
#파열음 파일(assets-c 안의 *_consonant.wav)은 stops_v3 폴더 코드로 만든 자음 부분만 있는 파일
#모음+종성은 appendcoda.make_vc()로 만들어서 그 위에 자음을 얹음

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets-c')

filename = {
    'ㄱ': 'g_consonant.wav', 'ㅋ': 'k_consonant.wav', 'ㄲ': 'kk_consonant.wav',
    'ㄷ': 'd_consonant.wav', 'ㅌ': 't_consonant.wav', 'ㄸ': 'tt_consonant.wav',
    'ㅂ': 'b_consonant.wav', 'ㅍ': 'p_consonant.wav', 'ㅃ': 'pp_consonant.wav'
}

#자음 파일 시작에서 모음이 시작되는 위치(ms), stops_v3/README_stops_v3.txt 표 그대로
#평음·격음은 기식이 모음 시작 뒤까지 이어지므로 크로스페이드가 아니라 겹쳐서(더해서) 놓음
#경음 ㄸ, ㅃ은 파일보다 위치가 뒤라서 그 사이는 무음
vowelstart = {
    'ㄱ': 80, 'ㅋ': 48, 'ㄲ': 10,
    'ㄷ': 66, 'ㅌ': 30, 'ㄸ': 14,
    'ㅂ': 44, 'ㅍ': 40, 'ㅃ': 8
}

#평음/격음/경음 구분용 피치 배율 (음절 시작 피치에만 곱함, 끝 피치는 그대로)
#stops_v3의 F0 시작값 평252 격318 경326 Hz를 평음 기준 비율로 바꾼 것
kind = {'ㄱ': '평', 'ㄷ': '평', 'ㅂ': '평', 'ㅋ': '격', 'ㅌ': '격', 'ㅍ': '격', 'ㄲ': '경', 'ㄸ': '경', 'ㅃ': '경'}
F0_RATIO = {'평': 1.0, '격': 318 / 252, '경': 326 / 252}
USE_F0_RATIO = True


_cache = {}
def consonant(c, sample_rate = 48000): #자음 파일(44100Hz 모노)을 모음과 같은 샘플레이트로 바꿔서 float 모노로 돌려줌
    if (c, sample_rate) not in _cache:
        sr, x = wavfile.read(os.path.join(path, filename[c]))
        x = x.astype(float)
        if sr != sample_rate:
            g = np.gcd(sr, sample_rate)
            x = resample_poly(x, sample_rate // g, sr // g)
        _cache[(c, sample_rate)] = x
    return _cache[(c, sample_rate)]


#------------------------------------------------------------ 모음 사이 평음 (해도, 아가 같은 경우)
#어두용 파일은 기식이 길어서(ㄷ 66ms) 모음 사이에 쓰면 격음(ㅌ)처럼 들림
#그래서 stops_v3.py의 vcv() 설정대로: 성대가 약하게 울리는 막힘 -> 약한 터짐 + 짧은 바람 -> 짧은 VOT 뒤 모음
MEDIAL = ['ㄱ', 'ㄷ', 'ㅂ']
code_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stops_v3', 'stops_v3.py')

_v3 = None
def v3(): #stops_v3.py에서 함수와 설정만 가져옴 (맨 아래 '저장' 부분은 실행 안 해서 파일 안 만들어짐)
    global _v3
    if _v3 is None:
        src = open(code_path, encoding='utf-8').read()
        _v3 = {}
        exec(src[:src.index('outs = {}')], _v3)
    return _v3


def medial_release(place): #개방 소리 + VOT 구간 잡음, vcv()에서 잡음 만드는 부분 그대로 (44100Hz, 모음 RMS 1 기준)
    g = v3()
    ms, db, VV = g['ms'], g['db'], g['VCV_VOT'][place]
    n_noise = ms(VV + 8) #두 번째 모음 시작 뒤 8ms까지 이어짐
    x = np.zeros(n_noise)
    if place == 'ㄱ':
        _, _, band = g['G_SET']['hump']
        z = g['rng'].standard_normal(n_noise + 2000)
        hn = g['sosfilt'](g['bandpass'](*band), z)[2000:]
        hn /= np.std(hn)
        env = np.ones(n_noise)
        env[:ms(3)] = np.linspace(0, 1, ms(3)) ** 2
        env *= np.linspace(1, 0.15, n_noise)
        n_ms = n_noise // ms(1) + 2
        env *= np.interp(np.arange(n_noise) / ms(1), np.arange(n_ms), db(g['rng'].normal(0, g['G_SET']['am_db'], n_ms)))
        x += hn * env * db(g['VCV_BURST']['ㄱ'])
    else:
        bu = g['make_burst'](place, 4 if place == 'ㄷ' else 5) * db(g['VCV_BURST'][place])
        x[:len(bu)] += bu
        an = g['place_asp_noise']('ㄷ', n_noise) if place == 'ㄷ' else g['burst_noise']('ㅂ', n_noise)
        env = np.linspace(1, 0.1, n_noise)
        env[:ms(2)] *= np.linspace(0, 1, ms(2))
        x += an * env * db(g['VCV_BURST'][place] - 8)
    return x


def medial_append(c1, V, f0, sample_rate = 48000): #V는 모노 float 모음(+종성), f0은 막힘 중 성대 울림 피치
    g = v3()
    C, VV = g['CLOSE'][c1], g['VCV_VOT'][c1]
    n_C, n_VV = int(sample_rate * C / 1000), int(sample_rate * VV / 1000)

    vrms = np.sqrt(np.mean(V[int(sample_rate * 0.03):int(sample_rate * 0.13)] ** 2)) #모음 크기 기준

    #막힘 중 성대 울림: 1배음이 모음 대비 -18dB -> -40dB로 줄어듦, 2배음은 12dB 더 작게
    #개방 뒤 VOT 구간은 약한 울림만 (-32dB)
    n = n_C + n_VV
    t = np.arange(n) / sample_rate
    lvl = np.append(np.linspace(-18, -40, n_C), np.full(n_VV, -32))
    phase = 2 * np.pi * f0 * t
    voicing = vrms * np.sqrt(2) * 10 ** (lvl / 20) * (np.sin(phase) + 10 ** (-12 / 20) * np.sin(2 * phase))
    voicing[:int(sample_rate * 0.004)] *= np.linspace(0, 1, int(sample_rate * 0.004)) #앞 음절이랑 이어질때 딱 소리 안 나게

    rel = medial_release(c1)
    rel = resample_poly(rel, sample_rate // np.gcd(44100, sample_rate), 44100 // np.gcd(44100, sample_rate))

    output = np.zeros(max(n + len(V), n_C + len(rel)))
    output[:n] += voicing
    output[n_C:n_C + len(rel)] += rel * vrms
    output[n:n + len(V)] += V
    return output


def stop_pitch(c1, pitch): #파열음 종류에 맞게 시작 피치 조절
    if not USE_F0_RATIO:
        return pitch
    return (pitch[0] * F0_RATIO[kind[c1]], pitch[1])


# appendcvc.append(), appendcoda.append()랑 인자 똑같음. 파열음 아닌 초성은 appendcoda.append()로 넘김
# medial=True면 모음 사이 평음으로 만듦 (앞 음절이 모음이나 ㄴ ㅁ ㅇ ㄹ로 끝나고 같은 어절일 때, 판단은 부르는 쪽에서)
def append(c1, v, c2, pitch, duration, sample_rate = 48000, medial = False): #c1과 v와 c2는 문자, pitch는 튜플, duration은 실수(모음 기준)
    if c1 not in filename:
        return appendcoda.append(c1, v, c2, pitch, duration)

    if c2 != '' and c2 not in appendcoda.CODA_OK: #ㄹ 등 아직 없는 종성은 빼고 만듦
        print(f"종성 '{c2}'는 아직 지원하지 않아서 빼고 만듭니다")
        c2 = ''

    pitch = stop_pitch(c1, pitch)
    if c2 == '':
        from VowelSynthesizer import gen_vowel
        V = gen_vowel.make_sound(v, pitch, duration, sample_rate=sample_rate)
    else:
        V = appendcoda.make_vc(v, pitch, c2, duration, sample_rate=sample_rate)

    #모노로 계산하고 마지막에 스테레오로
    V = V[::2].astype(float)

    if medial and c1 in MEDIAL:
        output = medial_append(c1, V, pitch[0], sample_rate)
        output = np.clip(np.round(output), -32768, 32767).astype(np.int16)
        return np.column_stack((output, output)).flatten()

    C = consonant(c1, sample_rate)
    n_start = int(sample_rate * vowelstart[c1] / 1000)

    output = np.zeros(max(len(C), n_start + len(V)))
    output[:len(C)] += C
    output[n_start:n_start + len(V)] += V

    output = np.clip(np.round(output), -32768, 32767).astype(np.int16)
    return np.column_stack((output, output)).flatten()
