'''
Created on 12 Nis 2014

@author: Burak Tutanlar
'''
from urllib import localhost
from thread import start_new_thread
from socket import *
from select import select
from re import search
from httplib import HTTPResponse

PROXY_PORT = 8080
BUFFER_LENGTH = 8192
TIMEOUT = 60
BACKLOG = 5
PROXY_AGENT = "Tutanlar's HTTP Proxy"
HTTP_VERSION = 'HTTP/1.1'

BLOCKS = ['(.*\.)?youtube\.com.*', '(.*\.)?vimeo\.com.*', 'lms\.ozyegin\.edu\.tr.*']

def parseURL(url):
    port = 80
    path = ''
    host = url
    portIndex = url.find(':')
    pathIndex = url.find('/')
    if (portIndex != -1 and pathIndex != -1):
        port = url[portIndex + 1:pathIndex]
        path = url[pathIndex:]
        host = url[:portIndex]
    elif (portIndex != -1):
        port = url[portIndex + 1:]
        host = url[:portIndex]
    elif (pathIndex != -1):
        host = url[:pathIndex]
        path = url[pathIndex:]
    return (host, port, path)

def parseFirstMessageFrom(clientSocket):
    clientBuffer = ''
    end = -1
    while end == -1:
        clientBuffer += clientSocket.recv(BUFFER_LENGTH)
        end = clientBuffer.find('\r\n\r\n')
    print clientBuffer
    header = clientBuffer[:clientBuffer.find('\r')].split()
    remaining = clientBuffer[clientBuffer.find('\r'):]
    return header, remaining

def forwardMessagesBetween(clientSocket, serverSocket):
    sockets = [clientSocket, serverSocket]
    count = 0
    while count < TIMEOUT:
        count += 1
        (availables, _, exception) = select(sockets, [], sockets, TIMEOUT)
        if exception:
            break
        for available in availables:
            data = available.recv(BUFFER_LENGTH)
            if data:
                if available is clientSocket:
                    out = serverSocket
                else:
                    out = clientSocket
                out.send(data)
                count = 0

def getServerSocket(host, port):
    soc_family, _, _, _, address = getaddrinfo(host, port)[0]
    serverSocket = socket(soc_family)
    serverSocket.connect(address)
    return serverSocket

def isBlocked(host):
    result = search('((.*\.)?youtube\.com.*)|((.*\.)?vimeo\.com.*)|(lms\.ozyegin\.edu\.tr.*)', host, 0)
    if result == None:
        return False
    else:
        return result.group(0) == host

def handleConnection(clientSocket):
    [method, url, protocol], remaining = parseFirstMessageFrom(clientSocket)
    if method == 'CONNECT':
        host, port, path = parseURL(url)
        if (isBlocked(host)):
            clientSocket.send(HTTP_VERSION + ' 403 Forbidden\r\n\r\n')
            clientSocket.close()
            return
        else:    
            serverSocket = getServerSocket(host, port)
            clientSocket.send(HTTP_VERSION + ' 200 Connection established\n' + 'Proxy-agent: %s\r\n\r\n' % (PROXY_AGENT))
        
    elif method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE'):
        host, port, path = parseURL(url[7:])
        serverSocket = getServerSocket(host, port)
        serverSocket.send('%s %s %s' % (method, path, protocol) + remaining)
    
    forwardMessagesBetween(clientSocket, serverSocket)
    
    clientSocket.close()
    serverSocket.close()

if __name__ == '__main__':
    proxySocket = socket(AF_INET, SOCK_STREAM)
    proxySocket.bind((localhost(), PROXY_PORT))
    print "Tutanlar's HTTP Proxy Server is listening on %s:%d." % (localhost(), PROXY_PORT)
    proxySocket.listen(BACKLOG)
    while 1:
        start_new_thread(handleConnection, (proxySocket.accept()[0],))
