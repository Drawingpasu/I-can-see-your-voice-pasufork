from hangul import *

첨가모음 = ['ㅣ', 'ㅑ', 'ㅕ', 'ㅛ', 'ㅠ']

def 니은첨가대상(앞, 뒤):
    """제29항: 합성어·파생어에서 앞 단어가 자음으로 끝나고 뒤 실질형태소가 이/야/여/요/유로 시작할 때"""
    if 앞['한글아님'] is not None or 뒤['한글아님'] is not None:
        return False
    if 앞['어절끝']:                    # 하나의 어절 내에서만 적용
        return False
    if 앞['종'] == '':                  # 앞이 모음으로 끝나면 ㄴ이 붙지 않음 (아이, 여기)
        return False
    if not 앞['형태소끝'] or 앞['다음형식']:  # 뒤가 조사·어미·접미사(이 등)이면 적용하지 않음
        return False
    if 뒤['초'] != 'ㅇ' or 뒤['중'] not in 첨가모음:
        return False
    if 뒤['중'] == 'ㅣ' and 뒤['종'] == 'ㅆ':   # 맛있다·멋있다 (제15항 다만)
        return False
    return True


def 니은첨가(음절들):
    for i in range(len(음절들) - 1):
        if 니은첨가대상(음절들[i], 음절들[i + 1]):
            음절들[i + 1]['초'] = 'ㄴ'

    return 음절들
