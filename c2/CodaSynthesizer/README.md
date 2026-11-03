# CodaSynthesizer - 종성(받침) 붙이는 모듈

_**개발시 주의사항: [VowelSynthesizer](../../v/VowelSynthesizer), [AppendCV](../../c1/AppendCV)를 불러다 씀. 최상위 tts.py로 실행하면 폴더 연결이 자동으로 됨** (따로 쓸 땐 `VowelSynthesizer`, `AppendCV` 이름으로 import 되게 해야 함)_

기존 모듈(gen_vowel.py, appendcvc.py, coda_table.py) 코드는 하나도 안 고침. appendcoda.py가 셋을 불러다가 이어붙이기만 함.

## appendcoda.py

.append(c1, v, c2, pitch, duration) - appendcvc.append()랑 인자 완전히 똑같음. 대신 c2(종성)까지 붙여줌
- c2가 ''이면 appendcvc.append() 결과 그대로
- c2가 ㄱ ㄴ ㄷ ㅁ ㅂ ㅇ 이면 종성 붙임
- c2가 ㄹ이면 아직 미완성이라 종성 빼고 만들고 메시지 출력
- duration은 여전히 **모음 기준**. 종성 붙으면 뒤에 0.27초 정도 더 길어짐
- numpy.ndarray형(스테레오 int16)을 반환함

.make_vc(v, pitch, c2, duration) - 초성 없이 모음+종성만
- 단모음: coda_table.make_coda()가 모음까지 한번에 만듦
- 이중모음: gen_vowel.make_sound()로 이중모음 만들고, 끝모음+종성(coda_table)을 DiphOverlapSec(0.05초)만큼 겹쳐서 크로스페이드

## coda_table.py
종성팀 모듈 원본 그대로. b_burst.wav, d_burst.wav, g_hump.wav가 같은 폴더에 있어야 함.

## 사용 예
```python
from CodaSynthesizer import appendcoda
from VowelSynthesizer import generator

y = appendcoda.append('ㅎ', 'ㅏ', 'ㄴ', (260, 240), 0.2)   # 한
generator.write_wav('han', y)
```

음운 변동 결과(음절 dict)에 바로 쓰면:
```python
y = appendcoda.append(음절['초'], 음절['중'], 음절['종'], (260, 240), 0.2)
```
(음운 변동 First의 초성 중 AppendCV에 파일이 있는 건 아직 ㅅ ㅆ ㅎ ㅇ 뿐)
