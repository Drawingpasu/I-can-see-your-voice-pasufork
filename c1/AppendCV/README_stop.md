# appendstop.py - 초성 파열음(ㄱㅋㄲ ㄷㅌㄸ ㅂㅍㅃ) 붙이는 코드

파열음팀 결과(stops_v3)를 그대로 가져옴. 자세한 설명은 [stops_v3/README_stops_v3.txt](stops_v3/README_stops_v3.txt)
- assets-c/ 안의 *_consonant.wav : 자음 부분만 있는 파일 9개 (2_consonants) ← 합성에 실제로 쓰는 것. ㅅ ㅆ ㅎ 파일이랑 같은 폴더
- stops_v3/ : stops_v3.py 등 원본 코드 (4_code), noises/ 노이즈 원본 (3_noises) ← 참고/다시 만들 때

## appendcvc.py랑 연결
appendcvc.append()에 아래만 추가함 (나머지 원래 코드는 그대로)
- 인자 `medial = False` 추가
- 맨 앞에서 초성이 파열음이거나 종성이 있으면 appendstop.append()로 넘김

그래서 `appendcvc.append(c1, v, c2, pitch, duration, medial)` 하나로 모든 초성, 종성을 만들 수 있음

## appendstop.py

.append(c1, v, c2, pitch, duration, medial) - 초성이 파열음이면 여기서 만들고, 아니면 appendcoda.append()로 넘김 (종성)
1. 모음(+종성)을 gen_vowel / appendcoda로 만들고
2. 자음 파일(44100Hz)을 48000Hz로 바꾼 다음
3. README 표의 '아를 놓을 위치'(vowelstart)에 모음이 시작되게 겹쳐서 더함 (기식이 모음 앞부분이랑 겹쳐야 해서 크로스페이드 안 씀)

피치: 평음/격음/경음 구분이 피치에도 있어서, 음절 시작 피치에 F0_RATIO(평 1.0, 격 1.26, 경 1.29)를 곱함. 끄려면 `appendstop.USE_F0_RATIO = False`

## 모음 사이 평음 (medial=True)
어두용 파일은 기식이 길어서(ㄷ 66ms) 모음 사이에 쓰면 ㅌ처럼 들림 (해도 -> 해토). 그래서 `medial=True`면 stops_v3.py의 vcv() 설정대로 만듦
1. 막힘 CLOSE(ㄱ ㄷ 60, ㅂ 65ms): 성대가 약하게 울림 (모음 대비 -18dB -> -40dB)
2. 개방: vcv()의 잡음 부분 그대로 (stops_v3.py의 make_burst 등을 불러다 씀, stops_v3.py는 안 고침)
3. VCV_VOT(ㄱ 16, ㄷ ㅂ 10ms) 뒤 모음 시작

언제 medial로 할지는 부르는 쪽(tts.py)이 정함: 같은 어절 안에서 앞 음절이 모음이나 ㄴ ㅁ ㅇ ㄹ 받침으로 끝날 때

## 한계
- 자음 파일은 '아' 앞에서 만든 것 하나뿐이라 다른 모음 앞에서도 같은 파일을 씀
- 모음 사이 평음은 앞 모음의 포먼트 전이(vcv()의 WARP)는 안 넣음
