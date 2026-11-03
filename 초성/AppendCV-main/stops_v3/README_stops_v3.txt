한국어 파열음 합성 최종본 (v3)
==============================

1_syllables  완성된 음절
  v3_all.wav   전체 이어 듣기: 가 카 까 / 다 타 따 / 바 파 빠 / 아가 / 아다 / 아바 / 아마
  v3_ga.wav    가      v3_ka.wav   카      v3_kka.wav  까
  v3_da.wav    다      v3_ta.wav   타      v3_tta.wav  따
  v3_ba.wav    바      v3_pa.wav   파      v3_ppa.wav  빠
  v3_aga.wav   아가    v3_ada.wav  아다    v3_aba.wav  아바    v3_ama.wav  아마

2_consonants  자음 부분만 (버스트 또는 모인 바람 소리 + 기식), 음절과 같은 크기
  파일              길이     '아'를 놓을 위치
  g_consonant.wav   102ms    80ms
  k_consonant.wav    70ms    48ms
  kk_consonant.wav   10ms    10ms
  d_consonant.wav    88ms    66ms
  t_consonant.wav    52ms    30ms
  tt_consonant.wav    7ms    14ms
  b_consonant.wav    66ms    44ms
  p_consonant.wav    62ms    40ms
  pp_consonant.wav    5ms     8ms
  * 평음·격음은 기식이 모음 시작 뒤 20ms까지 이어지므로 위치에 맞춰 겹쳐 놓을 것
  * 받은 '아'(260Hz 고정)에 붙이면 평음/격음/경음 구분이 약해짐 -> 모음 F0를 바꿀 수 있을 때 사용

3_noises  노이즈 원본 1초씩 (지금 설정과 같은 필터, 다른 모음 앞에 쓰거나 직접 다듬을 때)
  g_hump.wav       ㄱ 시작: 1,500-2,200Hz에 모인 거친 바람 소리 (버스트 대신)
  g_asp.wav        ㄱ 기식: 참고 음원 '카' 분포 (1,500-2,000Hz 꼭짓점), 거친 요동 포함
  d_burst.wav      ㄷ 버스트: 참고 분포 40% + 2,500-9,000Hz 60%
  d_asp.wav        ㄷ 기식: 500Hz 아래를 줄이고 3,000-6,000Hz를 키운 분포
  b_burst.wav      ㅂ 버스트: 1,100Hz 이하 + 넓은대역 10%
  voiceless_a.wav  무성 ㅏ: 기식이 모음으로 넘어가는 부분, ㅂ 기식

4_code
  stops_v3.py          합성기 전체 (실행하면 1_syllables 파일이 다시 만들어짐)
  export_consonants.py 2_consonants 파일 만들기
  export_noises.py     3_noises 파일 만들기
  * 세 파일을 같은 폴더에 두고 실행. 필요: Python, numpy, scipy

주요 설정 (stops_v3.py 위쪽)
  F0         평음 252->232->215Hz, 격음 318->326->300Hz, 경음 326->310->285Hz
  VOT        가80 다66 바44 / 카48 타30 파40 / 까10 따14 빠8 ms (설정값, 측정하면 약 10ms 길게 나옴)
  G_SET      ㄱ = K2: 충격음 없음, 모인 바람 소리 15ms, '카' 분포 기식, 1ms 요동 3.5dB
  D_SET      ㄷ = L2: 높은 주파수 섞은 날카로운 버스트(+4dB), 높은 기식 분포
  VCV_BURST  모음 사이 개방 소리 크기 (ㄱ -10, ㄷ -9, ㅂ -18dB)
  VCV_VOT    모음 사이 개방 뒤 VOT 구간 (ㄱ 16, ㄷ 10, ㅂ 10ms)

근거
  참고 음성: Typecast '지안'(젊은 여성)이 읽은 가카까/다타따/바파빠/아가/아다/아바 측정값
  박선영·성철재(2022) 표 4·5, 김진우(2021) 지각 실험
  조정값(청취로 정한 값)은 코드 주석에 표시
