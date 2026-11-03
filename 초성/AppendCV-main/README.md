# AppendCV

_**개발시 주의사항: 이 AppendCV는 이 모듈이 깔린 프로젝트에 [VowelSynthesizer](https://github.com/Drawingpasu/VowelSynthesizer)가 같이 (AppendCV랑 같은 높이에) 있는 상태여야 정상 작동됨.**_

why: appendcvc.py안의 대부분의 함수들이 실행하면서 [VowelSynthesizer](https://github.com/Drawingpasu/VowelSynthesizer)에 있는 함수와 변수 등을 호출함... 그래서 AppendCV가 작동하려면 먼저 저게 있어야함...


## appendcvc.py

.wav2strnp(c, vcode) - [자음 꾸러미](assets-c)에 이미 있는 wav 파일을 스테레오 소리를 담은 넘파이 정수 배열로 변환하는 함수
- c: 한글 자음 문자임. 뭐 'ㅅ', 'ㅎ' 이런거...
- vcode: 0~6의 정수 중 하나임. 저 c에 해당하는 초성 바로 뒤에 오는 중성(모음)이 뭔지 숫자로 적으면 됨. **0번부터 6번까지 순서대로 ㅏ, ㅣ, ㅜ, ㅔ, ㅗ, ㅡ, ㅓ 임**
- numpy.ndarray형을 반환함

- ***주의: [자음 꾸러미](assets-c)에 있는 자음 파일은 다음 조건을 만족시켜야만 합성 오류가 나지 않음:***

  **1. 샘플레이트: 44100(Hz)**
  
  **2. bit-depth: 16bit**
  
  **3. 방향성: Mono**
 
  협업 시 주의 바람...

  
.crossfade(audio1, audio2, transSec, sample_rate) - audio1, audio2 순으로 transSec초 만큼을 겹쳐서 크로스 페이드 한 결과물을 스테레오 소리를 담은 넘파이 정수 배열로 변환하는 함수
- audio1, audio2: 스테레오 소리를 담은 넘파이 정수 배열임. 물론 애네도 위에서 저 ***주의***에서 언급한 저 세 조건들을 만족하고 있는 상태여야 정상적으로 합성됨
- transSec: 저 두 음원을 얼마나 겹칠지... 실수임. 단위는 초
- sample_rate: ㄹㅇ 샘플레이트임... 기본값은 44100인데 건드리지 않는걸 권장
- numpy.ndarray형을 반환함


.append(c1, v, c2, pitch, duration) - 얘가 핵심임, 한 음절을 만들어주는 함수임. 사실 저 위 두 함수는 얠 만들기 위해서 만들어진거임...
- c1: 한글 자음 문자임, 한 음절에서 **초성**에 해당하는 부분을 적으면 됨
- v: 한글 모음 문자임, 한 음절에서 **중성**에 해당하는 부분을 적으면 됨
- c2: 한글 자음 문자임, 한 음절에서 **종성**에 해당하는 부분을 적으면 됨
- pitch: 원소 갯수가 2개인, 정수를 담은 튜플임. (a, b) 이렇게 있으면 a는 시작할때 기음(f0)의 Hz, b는 끝날때 기음(f0)의 Hz고 이 둘을 선형으로 이은 결과물이 나옴. 자세한건 [여기](https://github.com/Drawingpasu/VowelSynthesizer) 의 make_sound()의 f0 보셈ㅇㅇ
- duration: 지속시간(초)을 나타내는 실수임, 근데 주의할점!!! **이 지속시간은 모음 지속시간 기준임!** 합성에 참고하기...
- numpy.ndarray형을 반환함

- 10월 30일 (금) 기준으로 아직 종성 붙이는건 구현되지 않은 상태
