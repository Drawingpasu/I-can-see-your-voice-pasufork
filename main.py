from kiwipiepy import Kiwi
from hangul import First, Second, Third, 겹받침
from 연음 import 연음

kiwi = Kiwi()

문장= input() + ' '

형태소=kiwi.tokenize(문장) #나중에 음운변동처리할때 쓸꺼임

음절들 =[]

for i in range(len(문장)): #안녕 하세요면 문장[0]='안', 문장[1]='녕', 문장[2]=' ', 문장[3]='하', 문장[4]='세', 문장[5]='요'
    char=문장[i]
    음절 = {'초':'', '중':'', '종':'', '어절끝':False, '한글아님': None}

    if char==' ':
        if len(음절들)>0:
            음절들[-1]['어절끝'] = True
        continue

        #어캐 나누냐 -> ord라는 함수가 있는데 이게 유니코드값을 가져오는
        #유니코드 한글은 0xAC00 으로부터 
        #초성 19개, 중성21개, 종성28개로 이루어지고
	    #이들을 조합한 11,172개의 문자를 갖는다.
    	#한글코드의 값 = ((초성 * 21) + 중성) * 28 + 종성 + 0xAC00
	    #(0xAC00은 '가'의 코드값)

	    #따라서 다음과 같은 계산 식이 구해진다.
	    #유니코드 한글 문자 코드 값이 X일 때,

	    #초성 = ((X - 0xAC00) // 28) // 21
	    #중성 = ((X - 0xAC00) // 28) % 21
	    #종성 = (X - 0xAC00) % 28
        #https://github.com/neotune/python-korean-handler/blob/master/korean_handler.py

    초중성_uni_code = ord(char) - 0xAC00

    if 0 <= 초중성_uni_code < 11172:
        음절['초'] = First[초중성_uni_code // (21 * 28)] #한 초성의 경우의 수는 중성 21x종성 28임
        음절['중'] = Second[(초중성_uni_code // 28) % 21]
        음절['종'] = Third[초중성_uni_code % 28]
    else:
        음절['한글아님'] = char
    음절들.append(음절)

#규칙 입력
음절들=연음(음절들)





for i in 음절들:
    print(i['초'], i['중'], i['종'], i['어절끝'], i['한글아님'])