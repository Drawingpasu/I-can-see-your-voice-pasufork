#여기다가 dB 넘파이 배열 만드는 함수 다 해놓고, 그 함수들을 gen_vowel에서 쓰자!

#주석은 복붙 탓에 남은 거니 무시해주세요

import numpy as np


def dBfilterA():
    lin1 = np.linspace(-100, -30, 260) #-0
    lin2 = np.linspace(-30, -15, 260) #0-1
    lin3 = np.linspace(-15, -13, 260) #1-2
    lin4 = np.linspace(-13, -1, 260) #2-3
    lin5 = np.linspace(-1, -2, 260)  #3-4
    lin6 = np.linspace(-2, -3, 260) #4-5
    lin7 = np.linspace(-3, -500, 1300) #5-   # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin8 = np.linspace(-500, -500, 24000) # 얜 무조건 num 24000으로 고정
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7)
    output = np.append(output, lin8) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output

def dBfilterE():
    lin1 = np.linspace(-100, -27, 260) #-0
    lin2 = np.linspace(-27, -15, 260) #0-1
    lin3 = np.linspace(-15, -7, 260) #1-2
    lin4 = np.linspace(-7, -25, 260) #2-3
    lin5 = np.linspace(-25, -27, 260)  #3-4
    lin6 = np.linspace(-27, -28, 260) #4-5
    lin7 = np.linspace(-28, -25, 260) #5-   # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin8 = np.linspace(-25, -19, 260)
    lin9 = np.linspace(-19, -30, 260)
    lin10 = np.linspace(-30, -31, 260)
    lin11 = np.linspace(-31, -500, 260)
    lin12 = np.linspace(-500, -500, 24000)
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7)
    output = np.append(output, lin8)
    output = np.append(output, lin9)
    output = np.append(output, lin10)
    output = np.append(output, lin11)
    output = np.append(output, lin12) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output

def dBfilterI():
    lin1 = np.linspace(-100, -24, 260) #-0
    lin2 = np.linspace(-24, -5, 260) #0-1
    lin3 = np.linspace(-5, -27, 260) #1-2
    lin4 = np.linspace(-27, -29, 260) #2-3
    lin5 = np.linspace(-29, -30, 260)  #3-4
    lin6 = np.linspace(-30, -28, 260) #4-5
    lin7 = np.linspace(-28, -26, 260)
    lin8 = np.linspace(-26, -18, 260)
    lin9 = np.linspace(-18, -12, 260)
    lin10 = np.linspace(-12, -500, 520) #5-   # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin11 = np.linspace(-500, -500, 24000) # 얜 무조건 num 24000으로 고정
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7)
    output = np.append(output, lin8)
    output = np.append(output, lin9)
    output = np.append(output, lin10)
    output = np.append(output, lin11) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output

def dBfilterO():
    lin1 = np.linspace(-100, -38, 260) #-0
    lin2 = np.linspace(-38, -4, 260) #0-1
    lin3 = np.linspace(-4, -6, 260) #1-2
    lin4 = np.linspace(-6, -50, 260) #2-3
    lin5 = np.linspace(-50, -51, 260)  #3-4
    lin6 = np.linspace(-51, -500, 1560) #4-5 # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin7 = np.linspace(-500, -500, 24000) # 얜 무조건 num 24000으로 고정
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output

def dBfilterU():
    lin1 = np.linspace(-100, -28, 260) #-0
    lin2 = np.linspace(-28, -7, 260) #0-1
    lin3 = np.linspace(-7, -30, 260) #1-2
    lin4 = np.linspace(-30, -15, 260) #2-3
    lin5 = np.linspace(-15, -32, 260)  #3-4
    lin6 = np.linspace(-32, -500, 1560) #4-5 # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin7 = np.linspace(-500, -500, 24000) # 얜 무조건 num 24000으로 고정
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output

def dBfilterEU():
    lin1 = np.linspace(-100, -24, 260) #-0
    lin2 = np.linspace(-24, -5, 260) #0-1
    lin3 = np.linspace(-5, -30, 260) #1-2
    lin4 = np.linspace(-30, -23, 260) #2-3
    lin5 = np.linspace(-23, -22, 260)  #3-4
    lin6 = np.linspace(-22, -25, 260)
    lin7 = np.linspace(-25, -500, 1300) #4-5 # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin8 = np.linspace(-500, -500, 24000) # 얜 무조건 num 24000으로 고정
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7)
    output = np.append(output, lin8) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output

def dBfilterEO():
    lin1 = np.linspace(-100, -24, 260) #-0
    lin2 = np.linspace(-24, -14, 260) #0-1
    lin3 = np.linspace(-14, 0, 260) #1-2
    lin4 = np.linspace(0, -8, 260) #2-3
    lin5 = np.linspace(-8, -30, 260)  #3-4
    lin6 = np.linspace(-30, -500, 1300) #4-5 # 이친구 num은, 얘까지 num 다 더했을때 2860 되도록 정함
    lin7 = np.linspace(-500, -500, 24000) # 얜 무조건 num 24000으로 고정
    #이렇게 왼끝은 -100에서 끌고오고, 오른끝은 -500으로 보내버리기

    output = np.append(lin1, lin2)
    output = np.append(output, lin3)
    output = np.append(output, lin4)
    output = np.append(output, lin5)
    output = np.append(output, lin6)
    output = np.append(output, lin7) # 이러케 다 합쳐! (append 인자는 두개고, 적은 순서대로 붙음)

    return output