from hangul import *

def 구개음화(음절들):
    for i in range(len(음절들)-1):
        앞=음절들[i]
        뒤=음절들[i+1]


        if 앞['한글아님'] is not None:
            continue
        if 앞['어절끝'] is True:
            continue    

        if not(앞['형태소끝']and 앞['다음형식']):
            continue


        #제17항구개음화
        if 뒤['초']=='ㅇ' and 뒤['중']=='ㅣ' : 

            if 앞['종']=='ㄷ' :  
                앞['종']=''
                뒤['초']='ㅈ'

            if 앞['종']=='ㅌ' :
                앞['종']=''
                뒤['초']='ㅊ'
                

#미완 조정중
#예외사항 구현 필요
    return 음절들 
         
