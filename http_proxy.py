import socket
import sys
import re
import os
import threading
import errno
import time
import json
import uuid

LOG_FLAG=False
BUFFER_SIZE = 2048

def modify_headers(client_data):
    ''' modify header as specified in the spec''' 
    client_data = re.sub("keep-alive","close", client_data)
    client_data = re.sub("HTTP/1..","HTTP/1.0", client_data)
    return client_data # return the new data with the updated header

def parse_server_info(client_data):
    ''' parse server info from client data and
    returns 4 tuples of (server_ip, server_port, hostname, isCONNECT) '''
    status_line = client_data.split("\n")[0]
    URL = status_line.split(" ")[1]

    if "http://" in URL or ":80" in URL:
        server_port = 80

    if "https://" in URL or ":443" in URL:
        server_port = 443

        if "CONNECT" in status_line: # This is a CONNECT request
            hostname = URL.split(":")[0]
            server_ip = socket.gethostbyname(hostname)
            return (server_ip, 443, hostname, True)

    hostname = URL.split(":")[1][2:].split("/")[0]
    server_ip = socket.gethostbyname(hostname)

    return (server_ip, server_port, hostname, False) # NOT a CONNECT request


def tunneling(from_socket, to_socket):
    ''' Whatever received from from_socket forward to to_socket'''
    ''' to be used for CONNECT command '''
    while 1:
        try:
            to_socket.sendall(from_socket.recv(BUFFER_SIZE))
        except socket.error as e:
            if isinstance(e.args, tuple):
                if list(e.args)[0]==errno.EPIPE:
                    pass # disconnected

            # since disconnected close the tunnel
            to_socket.close()
            from_socket.close()
            return

# TODO: IMPLEMENT THIS METHOD 
def proxy(client_socket,client_IP):
    '''
    Modify this comment and add your code here
    '''
    global LOG_FLAG
    pass


def main():
    # check arguments
    if(len(sys.argv)!=3 and len(sys.argv)!=4):
        print("Incorrect number of arguments. \nUsage python3 http_proxy.py PORT")
        print("Incorrect number of arguments. \nUsage python3 http_proxy.py PORT Log")
        sys.exit()

    # enable logging
    if(len(sys.argv)==4 and sys.argv[3]=="Log"):
        global LOG_FLAG
        LOG_FLAG = True
        DIR_NAME = "./Log"
        if not (os.path.isdir(DIR_NAME)):
            os.system("mkdir Log")


    # create the socket for this proxy
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print ("HTTP proxy listening on port ",sys.argv[2])
    proxy_socket.bind(("127.0.0.1", int(sys.argv[2])))
    proxy_socket.listen(50) #allow connections  

    try: 
        while True:
            client_socket, client_IP = proxy_socket.accept()
            t = threading.Thread(target=proxy, args=(client_socket,client_IP,))
            t.start()
    except KeyboardInterrupt:
        proxy_socket.close()
        os._exit(1)

if __name__ == "__main__":
    main()