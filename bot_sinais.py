from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
import time
import sys
import threading
import requests
from login import logar

email, senha, conta, lista = logar()

# TELEGRAM
tlgm = open("telegram.txt", "r")
telegram = ["", ""]
for i, linha in enumerate(tlgm):
	linha = linha.rstrip()
	telegram[i] = linha
tlgm.close()
bot_token = telegram[0]
bot_chatID = telegram[1]

def telegram_bot_sendtext(bot_message):

	global bot_token, bot_chatID

	send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
	#main_msg = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
	#if prio == 1:# or prio == 0:
	response = requests.get(send_text)
	return response.json()

semaphore = threading.Semaphore(len(lista))
lock = threading.Lock()

API = IQ_Option(email, senha)
API.connect()

API.change_balance(conta)  # PRACTICE / REAL

if API.check_connect():
    print(' Conectado com sucesso!')
else:
    print(' Erro ao conectar')
    input('\n\n Aperte enter para sair')
    sys.exit()

saldo_inicial = API.get_balance()
wins = 0
losses = 0

def verifica_gale(vela, direcao, par, entrada, gales, subData, alt):
    lock.acquire()
    subData = subData + timedelta(minutes=vela)
    dataCerta = subData.strftime('%H:%M:%S')
    lock.release()

    mult = 2

    while True:
        dataAtual = ((datetime.now()).strftime('%H:%M:%S'))[:]
        seconds = float(dataAtual[6:])

        entrar = True if dataAtual[:-6] == dataCerta[:-6] and dataAtual[3:-3] == dataCerta[3:-3] and seconds >= 58 and seconds <= 59 else False
        lock.acquire()
        vel = API.get_candles(par, vela*60, 1, time.time())
        altura = vel[0]['close']
        lock.release()
        
        if entrar:
            if (direcao == 'put' and altura < alt) or (direcao == 'call' and altura > alt):
                print("Deu win!!!")
                break
            elif altura == alt:
                print('Empate!!!')
                break
            else: #Loss!!!
                lock.acquire()
                gales = gales - 1
                lock.release()
                realiza_entrada(par, direcao, vela, gales, entrada*mult, subData)


def realiza_entrada(par, direcao, vela, gales, entrada, subData):
    global wins, losses, saldo_inicial
    #gales = int(gales[:-1])
    showData = subData + timedelta(seconds=2)
    showData = showData.strftime('%H:%M:%S')
    status, id = API.buy(entrada, par, direcao, vela)

    lock.acquire()
    vel = API.get_candles(par, vela*60, 1, time.time())
    alt = vel[0]['close']
    lock.release()

    if gales > 0:
        #print('cheguei aqui')
        verifica_gale(vela, direcao, par, entrada, gales, subData, alt)


    if status:
        while True:
            try:
                status, valor = API.check_win_v3(id)
            except:
                status = True
                valor = 0

            if status:
                valor += API.check_win_v3(id)
                print("Resultado em", par, "=", valor)
                if valor > 0:
                    saldo_atual = saldo_inicial - API.get_balance()
                    wins = wins + 1
                    telegram_bot_sendtext("Win em " + par + " às " + showData + "\nWIN " + str(wins) + " x " + str(losses) + " LOSS\n" + "Saldo *parcial*: R$ " + str(saldo_atual*-1))
                elif valor < 0:
                    saldo_atual = saldo_inicial - API.get_balance()
                    losses = losses + 1
                    telegram_bot_sendtext("Loss em " + par + " às " + showData + "\nWIN " + str(wins) + " x " + str(losses) + " LOSS\n" + "Saldo *parcial*: R$ " + str(saldo_atual*-1))
                else:
                    saldo_atual = saldo_inicial - API.get_balance()
                    telegram_bot_sendtext("Empate em " + par + " às " + showData + "\nSaldo *parcial*: R$ " + str(saldo_inicial*-1))
                break
        
        return valor

def hora_de_entrar(hora, par, direcao, vela):
    global wins, losses
    #print(int(vela[1:]))
    with semaphore:
        with lock:
            vela = int(vela[1:])
            entrada = 100
            gales = 2
            direc = direcao[:-1].lower()
            newData = datetime.strptime(hora, '%H:%M:%S')
            subData = newData - timedelta(seconds=2)
            dataCerta = subData.strftime('%H:%M:%S')
        while True:
            dataAtual = ((datetime.now()).strftime('%H:%M:%S'))[:]
            seconds = float(dataAtual[6:])
            #print("São",dataAtual[:-6],"horas,",dataAtual[3:-3],"minutos e",seconds,"segundos!")
            entrar = True if dataAtual[:-6] == dataCerta[:-6] and dataAtual[3:-3] == dataCerta[3:-3] and seconds >= 58 and seconds <= 59 else False
            if entrar:
                realiza_entrada(par, direc, vela, gales, entrada, subData)

def encontra_sinal():
    #telegram_bot_sendtext("$ Robô para entrar em Listas de sinais ativado $\n")
    threads = list()
    #dados = []
    for i, k in enumerate(lista):
        vela, par, hora, direcao = lista[i].split(';')
        
        thread = threading.Thread(target=hora_de_entrar, args=(hora, par, direcao, vela))
        threads.append(thread)
        thread.start()
    
    for t in threads:
        t.join()

encontra_sinal()
