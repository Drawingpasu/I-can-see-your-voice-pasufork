import numpy as np
from scipy.io import wavfile
from v.VowelSynthesizer import gen_vowel
from v.VowelSynthesizer.gen_vowel import vowelseps

path = "AppendCV/assets-c/"
filename = { #[ㅏ, ㅣ, ㅜ, ㅔ, ㅗ, ㅡ, ㅓ]
    'ㅅ': ["s.wav", "s.wav", "s.wav", "s.wav", "s.wav", "s.wav", "s.wav"],
    'ㅆ': ["ss.wav", "ss.wav", "ss.wav", "ss.wav", "ss.wav", "ss.wav", "ss.wav"],
    'ㅎ': ["h_a.wav", "h_i.wav", "h_u.wav", "h_e.wav", "h_o.wav", "h_eu.wav", "h_eo.wav"],
    'ㅁ': ["m.wav", "m.wav", "m.wav", "m.wav", "m.wav", "m.wav", "m.wav"],
    'ㄴ': ["n.wav", "n.wav", "n.wav", "n.wav", "n.wav", "n.wav", "n.wav"],
    'ㄹ': ["r.wav", "r.wav", "r.wav", "r.wav", "r.wav", "r.wav", "r.wav"],
    'ㅈ': ["j_consonant.wav", "j_consonant.wav", "j_consonant.wav", "j_consonant.wav", "j_consonant.wav", "j_consonant.wav", "j_consonant.wav"],
    'ㅊ': ["ch_consonant.wav", "ch_consonant.wav", "ch_consonant.wav", "ch_consonant.wav", "ch_consonant.wav", "ch_consonant.wav", "ch_consonant.wav"],
    'ㅉ': ["jj_consonant.wav", "jj_consonant.wav", "jj_consonant.wav", "jj_consonant.wav", "jj_consonant.wav", "jj_consonant.wav", "jj_consonant.wav"]
    
}


Vcode = {
    'ㅏ': 0, '아': 0,
    'ㅣ': 1, '이': 1,
    'ㅜ': 2, '우': 2,
    'ㅔ': 3, '에': 3, 'ㅐ': 3, '애': 3,
    'ㅗ': 4, '오': 4,
    'ㅡ': 5, '으': 5,
    'ㅓ': 6, '어': 6

}

#각 자음별 (초성일때) 자음->모음 전환되면서 겹치는 시간(초)
overlapsec = {
    '': 0, 'ㅇ': 0,
    'ㅅ': 0.015,
    'ㅆ': 0.015,
    'ㅎ': 0.070,
    'ㅁ': 0.015,
    'ㄴ': 0.015,
    'ㄹ': 0.015,
    'ㅈ': 0.015,
    'ㅊ': 0.015,
    'ㅉ': 0.015
}



def wav2strnp(c, vcode): #c는 문자임
    sample_rate, output = wavfile.read(path + filename[c][vcode])
    output = np.column_stack((output, output)).flatten().astype(np.int16)
    return output


def crossfade(au1, au2, transSec, sample_rate = 44100): #au1랑 au2는 모두 스테레오 넘파이 배열, transSec은 전환시간(초)
    if au1 is not None:
        n_au1 = int(len(au1) / 2)
        n_au2 = int(len(au2) / 2)
        #데시벨 그래프는 일단 모노로 그려서 칼럼으로 필거임.. 그래서 일단 저 위의 n들은 모노일때 기준으로, 그러니까 반 나눠서 샘플 수를 계산했음.

        n_trans = int(sample_rate * transSec) #겹칠 부분 만큼의 샘플 수 정의
        n_whole = n_au1 + n_au2 - n_trans #전체 이어붙인 그 오디오의 샘플 수 정의

        #데시벨 그래프 생성
        fadeout = np.append(np.ones(n_au1 - n_trans), np.linspace(1, 0, n_trans))
        fadein = np.append(np.linspace(0, 1, n_trans), np.ones(n_au2 - n_trans))

        #데시벨 그래프 스테레오화
        fadeout = np.column_stack((fadeout, fadeout)).flatten()
        fadein = np.column_stack((fadein, fadein)).flatten()

        out1 = fadeout * au1
        out1 = out1.astype(np.int16)
        out2 = fadein * au2
        out2 = out2.astype(np.int16)

        #출력물 담을 그릇 만들기
        output = np.zeros(n_whole)
        output = np.column_stack((output, output)).flatten()

        R = np.zeros(len(output) - len(out1), dtype=output.dtype)
        output = output + np.append(out1, R)

        L = np.zeros(len(output) - len(out2), dtype=output.dtype)
        output = output + np.append(L, out2)

        return output.astype(np.int16)

    else:
        return au2




# 그전에!!! append에서 받는 duration은 모음 기준임!!!
def append(c1, v, c2, pitch, duration, medial = False): #c1과 v와 c2는 문자, pitch는 튜플, duration은 실수, medial은 모음 사이 평음일때 True
    #(추가) 파열음 초성이거나 종성이 있으면 appendstop.py에서 만듦
    from c1.AppendCV import appendstop
    if c1 in appendstop.filename or c2 != '':
        return appendstop.append(c1, v, c2, pitch, duration, medial=medial)

    if v in ['ㅏ', '아', 'ㅣ', '이', 'ㅜ', '우', 'ㅔ', '에', 'ㅐ', '애', 'ㅗ', '오', 'ㅡ', '으', 'ㅓ', '어']:
        vowelcode = Vcode[v]

    else:
        realvowel = vowelseps[v][0]
        vowelcode = Vcode[realvowel]

    C = wav2strnp(c1, vowelcode) if c1 != '' and c1 != 'ㅇ' else None
    V = gen_vowel.make_sound(v, pitch, duration)

    CV = crossfade(C, V, overlapsec[c1])

    if c2 == '': #종성 없을때
        output = CV

    else:
        pass

    return output






