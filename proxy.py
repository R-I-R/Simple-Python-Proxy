from socket import *
import threading
import select


def splitRequest(request):
	rs = request.decode().split('\r\n\r\n')
	head, body = rs if len(rs) > 1 else (rs[0],'')
	
	head = head.split('\r\n')
	headd = {'request':head[0].split(' ')}
	for h in range(1,len(head)):
		tmp = head[h].split(': ')
		headd[tmp[0]] = tmp[1]

	return headd,body

def getHostbyHeader(head):
	if 'Host' in head:
		host = head['Host'].split(':')
		if len(host) > 1:
			host[1] = int(host[1])
		else:
			host.append(80)
	else:
		host = head['request'][1].split(':')
		httpos = host[0].find('://')
		slashpos = host[0].find('/',0 if httpos == -1 else httpos+3)
		host[0] = host[0][:slashpos] if httpos == -1 else host[0][httpos+3:slashpos]

		if len(host) > 1:
			host[1] = int(host[1])
		else:
			host.append(80)

	return tuple(host)


def connectionHandler(clientSocket:socket, clientAddress):
	request = clientSocket.recv(4096)

	head, body = splitRequest(request)
	host = getHostbyHeader(head)

	print(f"conexion desde {clientAddress} hacia {host}")

	serverSocket = socket(AF_INET, SOCK_STREAM)
	try:
		serverSocket.connect(host)
	except TimeoutError:
		clientSocket.send(f"{head['request'][2]} 408 Request Timeout\r\n\r\n".encode())
	except gaierror:
		clientSocket.send(f"{head['request'][2]} 404 Not Found\r\n\r\n".encode())
	else:
		if head['request'][0] == 'CONNECT':
			clientSocket.send(f"{head['request'][2]} 200 Connection Established\r\n\r\n".encode())
		else:
			serverSocket.sendall(request)


		conns = [clientSocket,serverSocket]
		while True:
			rlist,wlist,xlist = select.select(conns, [], conns, 3)
			if xlist or not rlist:
				break

			for r in rlist:
				data = r.recv(4096)
				if not data: break

				if r is clientSocket: serverSocket.sendall(data)
				else: clientSocket.sendall(data)

	
	serverSocket.close()
	clientSocket.close()

	
IP = '192.168.100.22'
PORT = 8000

proxySock = socket(AF_INET, SOCK_STREAM)
proxySock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
proxySock.bind((IP,PORT))
proxySock.listen(10)

def server():

	while True:
		clientS, address = proxySock.accept()
		threading.Thread(name=f"{address[0]}::{str(address[1])}",target=connectionHandler,args=(clientS,address),daemon=True).start()


threading.Thread(target=server, daemon=True).start()
input("Presiona enter para finalizar la ejecucion")