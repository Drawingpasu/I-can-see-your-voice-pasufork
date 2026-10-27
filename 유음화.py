from hangul import *

def  유음화(음절들):
    for i in range(len(음절들) - 1):
        앞=음절들[i]
        뒤=음절들[i + 1]

        if 앞['한글아님'] is not None:
            continue
        if 앞['어절끝'] is True:
            continue
        
        #한자어 구분하여 한자어일떄는 작동 안한다는 내용


        #순행동화
        if 앞['종']=='ㄹ' and 뒤['초']=='ㄴ':
            뒤['초']='ㄹ'

        #역행동화
        if 앞['종']=='ㄴ' and 뒤['초']=='ㄹ':
            앞['종']='ㄹ'

        
