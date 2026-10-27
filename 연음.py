from hangul import *

def 연음(음절들):
    for i in range(len(음절들) - 1):
        앞=음절들[i]
        뒤=음절들[i + 1]
        if 앞['다음형식'] or 앞['형태소끝'] == True:
            continue
        elif 앞['형태소끝'] == True and 뒤['종']=='ㅏ'or'ㅓ'or'ㅗ'or'ㅜ'or'ㅟ':
            앞['종']=대표음 #15항

        if 앞['한글아님'] is not None:
            continue
        if 앞['어절끝'] is True:
            continue
        if 앞['종']=='' or 앞['종']=='ㅇ' or 뒤['초']!= 'ㅇ':
            continue

        if 앞['종'] == 'ㅎ':
            앞['종'] = ''
            뒤['초'] = 'ㅇ'
        elif 앞['종'] in ('ㄶ', 'ㅀ'):
            뒤['초'] = 겹받침[앞['종']][0]
            앞['종'] = ''
        elif 앞['종'] in 겹받침:
            뒤['초'] = 겹받침[앞['종']][1]
            앞['종'] = 겹받침[앞['종']][0]
        else:
            뒤['초'] = 앞['종'] #위아래 줄 바꾸면 큰일난디...
            앞['종'] = ''


    return 음절들