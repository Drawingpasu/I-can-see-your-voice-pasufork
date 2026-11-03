import numpy as np
from v.VowelSynthesizer import gen_vowel
from v.VowelSynthesizer.gen_vowel import vowelseps
from c1.AppendCV import appendcvc
from c2.CodaSynthesizer import coda_table

#기존 모듈(VowelSynthesizer, AppendCV, coda_table)은 손대지 않고, 여기서 불러다가 종성까지 붙임

CODA_OK = ['ㄱ', 'ㄴ', 'ㄷ', 'ㅁ', 'ㅂ', 'ㅇ'] #coda_table이 지원하는 종성 (ㄹ은 아직 미완성)

#이중모음 + 종성일때 쓰는 변수 (단위는 초)
DiphTailSec = 0.06      #이중모음 뒤에 붙이는 끝모음+종성의 모음 구간 길이
DiphOverlapSec = 0.05   #이중모음이랑 끝모음+종성을 겹치는 시간 (coda_table 시작 페이드 25ms보다 길어야 소리가 안 꺼짐)


def make_vc(v, pitch, c2, duration, sample_rate = 48000): #모음 + 종성, v와 c2는 문자, pitch는 튜플, duration은 실수(모음 기준)
    if v in coda_table.TABLES: #단모음이면 coda_table이 모음까지 한번에 만듦
        return coda_table.make_coda(v, pitch, c2, vowel_dur=duration, sample_rate=sample_rate)

    #이중모음이면: 이중모음은 gen_vowel로 만들고, 끝모음+종성을 coda_table로 만들어서 크로스페이드
    body = gen_vowel.make_sound(v, pitch, duration, sample_rate=sample_rate)
    tail = coda_table.make_coda(vowelseps[v][1], pitch[1], c2, vowel_dur=DiphTailSec, sample_rate=sample_rate)
    return appendcvc.crossfade(body, tail, DiphOverlapSec, sample_rate=sample_rate)


# appendcvc.append()랑 인자 똑같음, 종성 없으면 그냥 appendcvc.append() 결과를 그대로 돌려줌
def append(c1, v, c2, pitch, duration): #c1과 v와 c2는 문자, pitch는 튜플, duration은 실수
    if c2 == '':
        return appendcvc.append(c1, v, c2, pitch, duration)

    if c2 not in CODA_OK: #ㄹ 등 아직 없는 종성은 종성 빼고 만듦
        print(f"종성 '{c2}'는 아직 지원하지 않아서 빼고 만듭니다")
        return appendcvc.append(c1, v, '', pitch, duration)

    #초성 고르는 부분은 appendcvc.append()랑 똑같이
    if v in appendcvc.Vcode:
        vowelcode = appendcvc.Vcode[v]
    else:
        vowelcode = appendcvc.Vcode[vowelseps[v][0]]

    C = appendcvc.wav2strnp(c1, vowelcode) if c1 != '' and c1 != 'ㅇ' else None
    VC = make_vc(v, pitch, c2, duration)

    return appendcvc.crossfade(C, VC, appendcvc.overlapsec[c1])
