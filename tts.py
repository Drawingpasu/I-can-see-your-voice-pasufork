#문장 넣으면 음운 변동 -> 음성 합성 -> wav 저장까지 한번에 해주는 프로그램
#실행: python tts.py        (문장 입력받음, output.wav로 저장)
#      python tts.py 안녕    (안녕.wav로 저장)
#기존 모듈 코드는 안 고치고 불러다 쓰기만 함

import os
import sys
import types
import numpy as np

폴더 = os.path.dirname(os.path.abspath(__file__))

#설정 (단위는 초, Hz)
피치 = (260, 250)          #보통 음절 피치
마지막피치 = (250, 200)    #문장 마지막 음절 피치 (끝을 내려줌)
모음길이 = 0.2             #모음 지속시간 (append의 duration)
띄어쓰기쉼 = 0.12          #띄어쓰기에서 쉬는 시간
막힘시간 = 0.03            #어절 안에서 받침 ㄱ ㄷ ㅂ 뒤에 막혀 있는 시간
무음기준 = -50             #음절 끝에서 이것보다 작은 소리(dB)는 무음으로 보고 잘라냄
샘플레이트 = 48000


#모듈들이 초성, 중성, 종성 폴더 안에 나눠져 있고, 폴더 이름도 VowelSynthesizer-main처럼 되어 있어서 그냥은 import가 안 됨
#그래서 VowelSynthesizer라고 부르면 중성/VowelSynthesizer-main 폴더를 보게 연결해줌
위치 = {
    'AppendCV': '초성',           #ㅅ ㅆ ㅎ, ㄱㅋㄲ ㄷㅌㄸ ㅂㅍㅃ
    'VowelSynthesizer': '중성',   #단모음, 이중모음
    'CodaSynthesizer': '종성'     #ㄱ ㄴ ㄷ ㅁ ㅂ ㅇ
}
for 이름 in 위치:
    경로 = os.path.join(폴더, 위치[이름], 이름)
    if not os.path.isdir(경로):
        경로 = 경로 + '-main'
    모듈 = types.ModuleType(이름)
    모듈.__path__ = [경로]
    sys.modules[이름] = 모듈

from VowelSynthesizer import generator
from AppendCV import appendcvc, appendstop

#AppendCV는 자음 파일을 'AppendCV/assets-c/'에서 찾아서, 어디서 실행해도 찾게 경로를 바꿔줌
appendcvc.path = os.path.join(sys.modules['AppendCV'].__path__[0], 'assets-c') + os.sep


if len(sys.argv) > 1:
    파일이름 = sys.argv[1]
else:
    파일이름 = 'output'


# 1. 음운 변동
sys.path.insert(0, os.path.join(폴더, '음운 변동'))
import main
from hangul import First, Second, Third

음절들 = main.음절들


#2. 음성 합성
#종성 붙은 음절은 뒤에 0.27초짜리 꼬리(거의 무음)가 붙어 나와서, 그대로 이으면 끊겨 들림 (었다 -> 었/다)
#그래서 끝에 있는 무음은 잘라냄
def 끝무음자르기(소리):
    크기 = np.abs(소리[::2].astype(float)) 
    if 크기.max() == 0:
        return 소리
    마지막 = np.nonzero(크기 > 크기.max() * 10 ** (무음기준 / 20))[0][-1]
    return 소리[:(마지막 + 1) * 2]


한글음절 = []
for 음절 in 음절들:
    if 음절['한글아님'] is None:   #한글 아닌 글자(문장부호 등)는 빼고
        한글음절.append(음절)

조각들 = []
for i in range(len(한글음절)):
    음절 = 한글음절[i]
    초 = 음절['초']
    중 = 음절['중']
    종 = 음절['종']
    마지막음절 = (i == len(한글음절) - 1)

    #아직 소리 파일 없는 초성은 빼고 만듦
    if 초 not in appendcvc.overlapsec and 초 not in appendstop.filename:
        print(f"초성 '{초}'는 아직 없어서 빼고 만듭니다")
        초 = ''

    #모음 사이 평음인지: 같은 어절 안에서 앞 음절이 모음이나 ㄴ ㅁ ㅇ ㄹ 받침으로 끝나면 (해도, 안개)
    모음사이 = False
    if i > 0:
        앞 = 한글음절[i - 1]
        if not 앞['어절끝'] and 앞['종'] in ['', 'ㄴ', 'ㅁ', 'ㅇ', 'ㄹ']:
            모음사이 = True

    if 마지막음절:
        p = 마지막피치
    else:
        p = 피치

    소리 = appendcvc.append(초, 중, 종, p, 모음길이, medial=모음사이).astype(np.int16)
    조각들.append(끝무음자르기(소리))

    #받침 ㄱ ㄷ ㅂ 뒤에는 막힘 시간만큼 무음
    if 종 in ['ㄱ', 'ㄷ', 'ㅂ'] and not 음절['어절끝'] and not 마지막음절:
        조각들.append(np.zeros(int(샘플레이트 * 막힘시간) * 2, dtype=np.int16))   #스테레오라 *2

    #띄어쓰기에서 쉼
    if 음절['어절끝'] and not 마지막음절:
        조각들.append(np.zeros(int(샘플레이트 * 띄어쓰기쉼) * 2, dtype=np.int16))


#========== 3. 저장 ==========
if len(조각들) > 0:
    결과 = np.concatenate(조각들)
else:
    결과 = np.zeros(0, dtype=np.int16)

if 파일이름.endswith('.wav'):
    파일이름 = 파일이름[:-4]
generator.write_wav(파일이름, 결과, sample_rate=샘플레이트)
print(f"{파일이름}.wav")
