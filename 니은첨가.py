from hangul import *

def 니은첨가(음절들):
    for i in range(len(음절들)-1):
        앞=음절들[i]
        뒤=음절들[i+1]


        if 앞['한글아님']is not None:
            continue
        if 앞['어절끝']is True:
            continue

        #한 실질형태소 내에서 작동하지 않음
        #하나의 어절 내에서 적용하지 않음
        #접미사 이 에 대해서는 적용하지 않음
        #두 단어를 합친 단어,한자어 적용되지 않음
        
        #제29
        if 뒤['중']in['ㅣ','ㅑ','ㅕ','ㅛ','ㅠ'] and 뒤['초']=='ㅇ':
            뒤['초']='ㄴ'

    return 음절들    
