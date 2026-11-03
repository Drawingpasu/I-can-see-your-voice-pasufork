import numpy as np
import wave
import os

# === 파형 종류 선택 ===
def generate_sin(sample_rate = 48000, duration = 10.0, freqL = 260, freqR = 260, bit_depth = 16, dB = np.zeros(4800)):
    # "sine", "square", "triangle", "sawtooth"
    WAVE_TYPE = "sine"

    # WAV 파일 파라미터
    #sample_rate = 48000   # 48 kHz
    #duration = 10.0       # 11초
    #freq = 1000           # 1000 Hz
    #bit_depth = 16        # 비트 깊이 (샘플당 비트 수)

    # === 진폭을 dBFS 단위로 지정 ===
    # 예: "0dB", "-6dB", "-12dB"
    #amp_db = "0dB" #0이 안깨지는 최대인듯...
    # 2) 시간축 생성
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # 1) dB → 실제 amplitude 값 변환
    max_val = 2**(bit_depth - 1) - 1  # 16-bit 최대치 32767
    #db_value = float(dB) - 10.0
    db_value = dB -12
    #db_value = np.linspace(-12, 0, num_samples, endpoint=False)
    amplitude = max_val * 10**(db_value / 20)
    #print(db_value)



    # 3) 파형 생성
    freq = np.linspace(freqL, freqR, num_samples, endpoint=False)

    if WAVE_TYPE == "sine":
        wave_data = amplitude * np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
    elif WAVE_TYPE == "square":
        wave_data = amplitude * np.sign(np.sin(2 * np.pi * freq * t))
    elif WAVE_TYPE == "triangle":
        wave_data = (2 * amplitude / np.pi) * np.arcsin(np.sin(2 * np.pi * freq * t))
    elif WAVE_TYPE == "sawtooth":
        wave_data = (2 * amplitude / np.pi) * np.arctan(np.tan(np.pi * freq * t))
    else:
        raise ValueError("지원하지 않는 파형 타입입니다!")

    wave_data = wave_data.astype(np.int16)

    # 4) 스테레오 신호 변환
    stereo_data = np.column_stack((wave_data, wave_data)).flatten()
    return stereo_data

# 5) 파일 이름 자동 생성
"""
script_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(
    script_dir,
    f"{WAVE_TYPE}_{freq}Hz_{sample_rate}Hz_{bit_depth}bit_{amp_db}_{int(duration)}sec.wav"
)
"""


def write_wav(filename, stereo_data, sample_rate = 48000, bit_depth = 16):
    with wave.open(filename + ".wav", 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(bit_depth // 8)
        wf.setframerate(sample_rate)
        wf.writeframes(stereo_data.tobytes())

    print("WAV 파일 저장 완료")

# 6) WAV 파일 저장


#print(f"WAV 파일 생성 완료: ")
#출처: https://wowon.tistory.com/368 [원원이의 블로그:티스토리]