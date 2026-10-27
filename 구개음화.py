from hangul import *

def 구개음화(음절들):
    for i in range(len(음절들)-1):
        앞=음절들[i]
        뒤=음절들[i+1]


        if 앞['한글아님'] is not None:
            continue
        if 앞['어절끝'] is True:
            continue    

        #실질형태소랑 만나면 작동 안한다는 내용
            
        if 뒤['초']=='ㅇ' and 뒤['중']=='ㅣ' : 

            if 앞['종']=='ㄷ' :  #ㄷ이면 ㅈ, ㅌ이면 ㅊ을 뒤 초성에 추가
                앞['종']=''
                뒤['초']='ㅈ'

            if 앞['종']=='ㅌ' :
                앞['종']=''
                뒤['초']='ㅊ'


return 0:
         
