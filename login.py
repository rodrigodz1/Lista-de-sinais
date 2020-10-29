import os, getpass

def logar():
    if os.stat("user.txt").st_size == 0:
        email = input("Digite seu E-MAIL da IQ Option: ")
        senha = getpass.getpass("Digite sua SENHA da IQ Option: ")
        conta = input("Conta real ou demo: ")
        if conta == "real":
            conta1 = "REAL"
        else:
            conta1 = "PRACTICE"

        login = open('user.txt', 'w')
        login.write(email)
        login.write("\n")

        login.write(senha)
        login.write("\n")

        login.write(conta1)
        login.write("\n")
        login.close()

    else:
        login = open('user.txt', 'r')
        signin = ["", "", ""]
        for i, linha in enumerate(login):
            linha = linha.rstrip()
            signin[i] = linha
        login.close()
        email = signin[0]
        senha = signin[1]
        conta = signin[2]

        if conta == "real":
            conta1 = "REAL"
        else:
            conta1 = "PRACTICE"
    
    lista = list()
    sinais = open('sinais.txt', 'r')
    
    for i, linha in enumerate(sinais):
        if linha.find('#') != 0:
            lista.append(linha)
    sinais.close()

    return email, senha, conta1, lista