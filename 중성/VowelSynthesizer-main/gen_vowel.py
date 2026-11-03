from VowelSynthesizer import generator, dBFilter
import numpy as np


#이중모음 변수 설정 (둘 다 단위는 초), 근데 안바꾸는걸 권장함
SemivowelOverlapSec = 0.1   #얘는 반모음 -> 모음 전환시간
SemivowelDurationSec = 0.024   #얘는 only 반모음 지속시간(전환시간 제외한)


#이중모음 각 경우별 반모음 모음 매핑 딕셔너리

vowelseps = { #하향 포함, [0]은 반모음이고 [1]은 모음이도록 딕셔너리를 짰음
    'ㅑ' : ['ㅣ', 'ㅏ'],
    '야' : ['ㅣ', 'ㅏ'],

    'ㅕ' : ['ㅣ', 'ㅓ'],
    '여' : ['ㅣ', 'ㅓ'],

    'ㅛ' : ['ㅣ', 'ㅗ'],
    '요' : ['ㅣ', 'ㅗ'],

    'ㅠ': ['ㅣ', 'ㅜ'],
    '유': ['ㅣ', 'ㅜ'],

    'ㅖ': ['ㅣ', 'ㅔ'],
    '예': ['ㅣ', 'ㅔ'],
    'ㅒ': ['ㅣ', 'ㅔ'],
    '얘': ['ㅣ', 'ㅔ'],

    'ㅘ' : ['ㅗ', 'ㅏ'],
    '와' : ['ㅗ', 'ㅏ'],

    'ㅙ' : ['ㅗ', 'ㅐ'],
    '왜' : ['ㅗ', 'ㅐ'],
    'ㅞ' : ['ㅜ', 'ㅔ'],
    '웨' : ['ㅜ', 'ㅔ'],
    'ㅚ' : ['ㅗ', 'ㅔ'],
    '외' : ['ㅗ', 'ㅔ'],

    'ㅝ' : ['ㅜ', 'ㅓ'],
    '워' : ['ㅜ', 'ㅓ'],

    'ㅟ' : ['ㅜ', 'ㅣ'],
    '위' : ['ㅜ', 'ㅣ'],

    'ㅢ' : ['ㅡ', 'ㅣ'],
    '의' : ['ㅡ', 'ㅣ']
}

def make_sound(vowel, f0, duration1, sample_rate = 48000): #vowel은 char, f0은 튜플, duration은 float
    if vowel == 'ㅏ' or vowel == '아':
        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])

        #배음 몇개 만들어야 할지 계산
        min = f0[0] if f0[0] < f0[1] else f0[1]
        count = round(1560/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)


        #배음 생성
        output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
        for i in range(1, count + 1):
            curfreq = i * f0[0]
            nextfreq = i * f0[1]

            #dBFilter에서 주파수 dB 필터 가져와서
            if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                filternp = dBFilter.dBfilterA()[curfreq-1 : nextfreq]
            else: #음 내려갈때
                filternp = dBFilter.dBfilterA()[nextfreq-1 : curfreq]
                filternp = np.flip(filternp)

            #맞게 보간한 다음에
            x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
            y = filternp
            new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)

            # 페이드 인 페이드 아웃
            a = np.linspace(-30, 0, 500)
            ac = np.zeros(int(sample_rate * duration1) - 500)
            fadein = np.append(a, ac)
            b = np.linspace(0, -30, 500)
            bc = np.zeros(int(sample_rate * duration1) - 500)
            fadeout = np.append(bc, b)

            # 씌우기
            audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
            output = output + audio


        return output



    elif vowel == 'ㅐ' or vowel == '애' or vowel == 'ㅔ' or vowel == '에':
        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])
    
        #배음 몇개 만들어야 할지 계산
        min = f0[0] if f0[0] < f0[1] else f0[1]
        count = round(2600/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)


        #배음 생성
        output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
        for i in range(1, count + 1):
            curfreq = i * f0[0]
            nextfreq = i * f0[1]
    
            #dBFilter에서 주파수 dB 필터 가져와서
            if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                 filternp = dBFilter.dBfilterE()[curfreq-1 : nextfreq]
            else: #음 내려갈때
                 filternp = dBFilter.dBfilterE()[nextfreq-1 : curfreq]
                 filternp = np.flip(filternp)
        
             #맞게 보간한 다음에
            x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
            y = filternp
            new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)
    
            # 페이드 인 페이드 아웃
            a = np.linspace(-30, 0, 500)
            ac = np.zeros(int(sample_rate * duration1) - 500)
            fadein = np.append(a, ac)
            b = np.linspace(0, -30, 500)
            bc = np.zeros(int(sample_rate * duration1) - 500)
            fadeout = np.append(bc, b)

            # 씌우기
            audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
            output = output + audio
        
        
        return output



    elif vowel == 'ㅣ' or vowel == '이':
        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])
        
        #배음 몇개 만들어야 할지 계산
        min = f0[0] if f0[0] < f0[1] else f0[1]
        count = round(2340/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)
    
    
        #배음 생성
        output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
        for i in range(1, count + 1):
            curfreq = i * f0[0]
            nextfreq = i * f0[1]
        
            #dBFilter에서 주파수 dB 필터 가져와서
            if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                 filternp = dBFilter.dBfilterI()[curfreq-1 : nextfreq]
            else: #음 내려갈때
                 filternp = dBFilter.dBfilterI()[nextfreq-1 : curfreq]
                 filternp = np.flip(filternp)
        
             #맞게 보간한 다음에
            x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
            y = filternp
            new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)
    
            # 페이드 인 페이드 아웃
            a = np.linspace(-30, 0, 500)
            ac = np.zeros(int(sample_rate * duration1) - 500)
            fadein = np.append(a, ac)
            b = np.linspace(0, -30, 500)
            bc = np.zeros(int(sample_rate * duration1) - 500)
            fadeout = np.append(bc, b)

            # 씌우기
            audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
            output = output + audio
        
        
        return output


    elif vowel == 'ㅗ' or vowel == '오':
            f0 = list(f0)
            f0[0] = int(f0[0])
            f0[1] = int(f0[1])
        
            #배음 몇개 만들어야 할지 계산
            min = f0[0] if f0[0] < f0[1] else f0[1]
            count = round(1300/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)
    
    
            #배음 생성
            output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
            for i in range(1, count + 1):
                curfreq = i * f0[0]
                nextfreq = i * f0[1]
        
                #dBFilter에서 주파수 dB 필터 가져와서
                if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                     filternp = dBFilter.dBfilterO()[curfreq-1 : nextfreq]
                else: #음 내려갈때
                     filternp = dBFilter.dBfilterO()[nextfreq-1 : curfreq]
                     filternp = np.flip(filternp)
            
                 #맞게 보간한 다음에
                x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
                y = filternp
                new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)
        
                # 페이드 인 페이드 아웃
                a = np.linspace(-30, 0, 500)
                ac = np.zeros(int(sample_rate * duration1) - 500)
                fadein = np.append(a, ac)
                b = np.linspace(0, -30, 500)
                bc = np.zeros(int(sample_rate * duration1) - 500)
                fadeout = np.append(bc, b)
    
                # 씌우기
                audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
                output = output + audio
            
            
            return output
    
    
    
    elif vowel == 'ㅜ' or vowel == '우':
        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])
        
        #배음 몇개 만들어야 할지 계산
        min = f0[0] if f0[0] < f0[1] else f0[1]
        count = round(1300/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)
    
    
        #배음 생성
        output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
        for i in range(1, count + 1):
            curfreq = i * f0[0]
            nextfreq = i * f0[1]
        
            #dBFilter에서 주파수 dB 필터 가져와서
            if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                 filternp = dBFilter.dBfilterU()[curfreq-1 : nextfreq]
            else: #음 내려갈때
                 filternp = dBFilter.dBfilterU()[nextfreq-1 : curfreq]
                 filternp = np.flip(filternp)
        
             #맞게 보간한 다음에
            x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
            y = filternp
            new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)
    
            # 페이드 인 페이드 아웃
            a = np.linspace(-30, 0, 500)
            ac = np.zeros(int(sample_rate * duration1) - 500)
            fadein = np.append(a, ac)
            b = np.linspace(0, -30, 500)
            bc = np.zeros(int(sample_rate * duration1) - 500)
            fadeout = np.append(bc, b)

            # 씌우기
            audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
            output = output + audio
        
        
        return output


    elif vowel == 'ㅡ' or vowel == '으':
            f0 = list(f0)
            f0[0] = int(f0[0])
            f0[1] = int(f0[1])
        
            #배음 몇개 만들어야 할지 계산
            min = f0[0] if f0[0] < f0[1] else f0[1]
            count = round(1560/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)
    
    
            #배음 생성
            output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
            for i in range(1, count + 1):
                curfreq = i * f0[0]
                nextfreq = i * f0[1]
        
                #dBFilter에서 주파수 dB 필터 가져와서
                if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                     filternp = dBFilter.dBfilterEU()[curfreq-1 : nextfreq]
                else: #음 내려갈때
                     filternp = dBFilter.dBfilterEU()[nextfreq-1 : curfreq]
                     filternp = np.flip(filternp)
            
                 #맞게 보간한 다음에
                x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
                y = filternp
                new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)
        
                # 페이드 인 페이드 아웃
                a = np.linspace(-30, 0, 500)
                ac = np.zeros(int(sample_rate * duration1) - 500)
                fadein = np.append(a, ac)
                b = np.linspace(0, -30, 500)
                bc = np.zeros(int(sample_rate * duration1) - 500)
                fadeout = np.append(bc, b)
    
                # 씌우기
                audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
                output = output + audio
            
            
            return output
    
    
    
    elif vowel == 'ㅓ' or vowel == '어':
        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])
            
         #배음 몇개 만들어야 할지 계산
        min = f0[0] if f0[0] < f0[1] else f0[1]
        count = round(1300/min) # round(a / min)의 a에는 그 모음 배음의 최대 주파수를 적음 ('아'는 5배음이 끝이라 1560)
    
    
        #배음 생성
        output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)
        for i in range(1, count + 1):
            curfreq = i * f0[0]
            nextfreq = i * f0[1]
        
            #dBFilter에서 주파수 dB 필터 가져와서
            if f0[0] <= f0[1]: #음 상승할때 or 일정할때
                 filternp = dBFilter.dBfilterEO()[curfreq-1 : nextfreq]
            else: #음 내려갈때
                 filternp = dBFilter.dBfilterEO()[nextfreq-1 : curfreq]
                 filternp = np.flip(filternp)
        
             #맞게 보간한 다음에
            x = np.linspace(0, 1, abs(curfreq - nextfreq) + 1)
            y = filternp
            new_filter = np.interp(np.linspace(0, 1, int(sample_rate*duration1)), x, y)
    
            # 페이드 인 페이드 아웃
            a = np.linspace(-30, 0, 500)
            ac = np.zeros(int(sample_rate * duration1) - 500)
            fadein = np.append(a, ac)
            b = np.linspace(0, -30, 500)
            bc = np.zeros(int(sample_rate * duration1) - 500)
            fadeout = np.append(bc, b)

            # 씌우기
            audio = generator.generate_sin(duration = duration1, freqL=curfreq, freqR=nextfreq, dB=new_filter+fadein+fadeout, sample_rate=sample_rate)
            output = output + audio
        
        
        return output

    ##################  이중모음  ###################

    elif vowel != 'ㅢ' and vowel != '의': #'ㅢ'를 제외한 모든 이중모음 생성에 대하여...
        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])

        if (duration1 <= SemivowelOverlapSec + SemivowelDurationSec): #혹시모를 오류처리
            raise ValueError(f"반모음 시간(초)이 {SemivowelOverlapSec + SemivowelDurationSec}이지만 전체 지속시간이 너무 짧습니다!")

        #반모음부, 모음부 만들기
        semi = make_sound(vowelseps[vowel][0], (f0[0]-8, f0[0]), duration1 = SemivowelDurationSec + SemivowelOverlapSec, sample_rate=sample_rate)
        vow = make_sound(vowelseps[vowel][1], (f0[0], f0[1]), duration1 = duration1 - SemivowelDurationSec, sample_rate=sample_rate)

        n_semi = int(sample_rate * (SemivowelDurationSec + SemivowelOverlapSec)) #얘네는 모노일때 기준 샘플수
        n_vow = int(sample_rate * (duration1 - SemivowelDurationSec)) #얘도 모노일때 기준 샘플수
        #fadein fadeout 만들어야해서...

        #반모음 사라지는 부분이랑 모음 등장하는 부분 데시벨 그래프 생성
        fadeout = np.append(np.zeros(int(SemivowelDurationSec * sample_rate)),  np.linspace(0, -15, n_semi - int(SemivowelDurationSec * sample_rate))) - 8
        fadein = np.append(np.linspace(-13, 0, int(SemivowelOverlapSec * sample_rate)), np.zeros(n_vow - int(SemivowelOverlapSec * sample_rate))) - 24

        #데시벨 그래프 적용
        max_val = 2 ** (5 - 1)  # 16-bit 최대치 32767
        amplitude1 = 2 * 10 ** ((fadeout) / 20)
        amplitude1 = np.column_stack((amplitude1, amplitude1)).flatten()
        semi = amplitude1 * semi
        semi = semi.astype(np.int16)

        amplitude2 = max_val * 10 ** ((fadein) / 20)
        amplitude2 = np.column_stack((amplitude2, amplitude2)).flatten()
        vow = amplitude2 * vow
        vow = vow.astype(np.int16)

        #출력물 담을 그릇 만들기
        output = generator.generate_sin(duration = duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)

        #반모음부 정리
        R = np.zeros(len(output) - len(semi), dtype=output.dtype)
        output = output + np.append(semi, R)

        #모음부 정리
        L = np.zeros(len(output) - len(vow), dtype=output.dtype)
        output = output + np.append(L, vow)

        return output

    elif vowel == 'ㅢ' or vowel == '의': # 'ㅢ'소리일때
        loc_SemivowelOverlapSec = duration1 * 0.6
        loc_SemivowelDurationSec = duration1 * 0.2

        f0 = list(f0)
        f0[0] = int(f0[0])
        f0[1] = int(f0[1])

        if (duration1 <= loc_SemivowelOverlapSec + loc_SemivowelDurationSec):  # 혹시모를 오류처리
            raise ValueError(f"반모음 시간(초)이 {loc_SemivowelOverlapSec + loc_SemivowelDurationSec}이지만 전체 지속시간이 너무 짧습니다!")

        # 반모음부, 모음부 만들기
        semi = make_sound(vowelseps[vowel][0], (f0[0], f0[0]), duration1=loc_SemivowelDurationSec + loc_SemivowelOverlapSec, sample_rate=sample_rate)
        vow = make_sound(vowelseps[vowel][1], (f0[0], f0[1]), duration1=duration1 - loc_SemivowelDurationSec, sample_rate=sample_rate)

        n_semi = int(sample_rate * (loc_SemivowelDurationSec + loc_SemivowelOverlapSec))
        n_vow = int(sample_rate * (duration1 - loc_SemivowelDurationSec))

        # 반모음 사라지는 부분이랑 모음 등장하는 부분 데시벨 그래프 생성
        fadeout = np.append(np.zeros(int(loc_SemivowelDurationSec * sample_rate)),
                            np.linspace(0, -18, n_semi - int(loc_SemivowelDurationSec * sample_rate))) - 8
        fadein = np.append(np.linspace(-18, 0, int(loc_SemivowelOverlapSec * sample_rate)),
                           np.zeros(n_vow - int(loc_SemivowelOverlapSec * sample_rate))) - 24

        # 데시벨 그래프 적용
        max_val = 2 ** (5 - 1)  # 16-bit 최대치 32767
        amplitude1 = 2 * 10 ** ((fadeout) / 20)
        amplitude1 = np.column_stack((amplitude1, amplitude1)).flatten()
        semi = amplitude1 * semi
        semi = semi.astype(np.int16)

        amplitude2 = max_val * 10 ** ((fadein) / 20)
        amplitude2 = np.column_stack((amplitude2, amplitude2)).flatten()
        vow = amplitude2 * vow
        vow = vow.astype(np.int16)

        # 출력물 담을 그릇 만들기
        output = generator.generate_sin(duration=duration1, freqL=0, freqR=0, dB=-100, sample_rate=sample_rate)

        # 반모음부 정리
        R = np.zeros(len(output) - len(semi), dtype=output.dtype)
        output = output + np.append(semi, R)

        # 모음부 정리
        L = np.zeros(len(output) - len(vow), dtype=output.dtype)
        output = output + np.append(L, vow)

        return output


    return None
