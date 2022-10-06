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
 
       if "CONNECT" in status_line: # CONNECT request found
           hostname = URL.split(":")[0]
           server_ip = socket.gethostbyname(hostname)
           return (server_ip, 443, hostname, True) # For a CONNECT request
 
   hostname = URL.split(":")[1][2:].split("/")[0]
   server_ip = socket.gethostbyname(hostname)
 
   return (server_ip, server_port, hostname, False) # NOT a CONNECT request
 
 
# Creates a subdirectory for the hostname and a new json file
def create_log(hostname, incoming_header, modified_header, server_response):
   pathname = "Log/" + hostname
   if not os.path.exists(pathname):
       os.makedirs(pathname, 0o777, exist_ok=True)
       os.chmod('Log', 0o777)
       os.chmod(pathname, 0o777)
  
   json_dict = {
       'Incoming header': incoming_header,
       'Modified header': modified_header,
       'Server reponse received' : server_response
   }
   #Dir/Subdir/hostnameuuid.json
   with open(pathname + "/" + hostname + str(uuid.uuid1()) + ".json", "w+") as outfile:
       json.dump(json_dict, outfile, indent=4)
 
# Creates a subdirectory for the hostname and a new json file (Use this for CONNECT requests)
def create_log2(hostname, incoming_header, response_sent):
   pathname = "Log/" + hostname
   if not os.path.exists(pathname):
       os.makedirs(pathname, 0o777, exist_ok=True)
       os.chmod('Log', 0o777)
       os.chmod(pathname, 0o777)
 
   json_dict = {
       'Incoming header': incoming_header,
       'Proxy response sent': response_sent,
   }
   #Dir/Subdir/hostnameuuid.json
   with open(pathname + "/" + hostname + str(uuid.uuid1()) + ".json", "w+") as outfile:
       json.dump(json_dict, outfile, indent=4)
 
# Tunneling method: whatever message received from "from_socket" send to "to_socket"
# should be used for CONNECT request
def tunnel(from_socket, to_socket):
   while True:
       try:
           to_socket.sendall(from_socket.recv(BUFFER_SIZE))
       except:
           # close sockets when done or when error
           from_socket.close()
           to_socket.close()
           return
      
 
# TODO: IMPLEMENT THIS METHOD
def proxy(client_socket,client_IP):
   global LOG_FLAG
   # receive client request
   client_data = client_socket.recv(BUFFER_SIZE)
   # parse server info
   server_info = parse_server_info(client_data.decode("utf-8", "backslashreplace"))
   # If HTTP CONNECT call foo, else if non-CONNECT request call
   if server_info[3]:
       foo(server_info)
   else:
       bar(client_socket, client_IP, server_info, client_data)
 
# For HTTP CONNECT request
def foo(server_info):
    
   proxy_socket.sendall(client_data.encode("utf-8"))
   data = proxy_socket.recv(BUFFER_SIZE)
   if data:
    create_log2(server_info[2], client_data ,"200 OK")
    tunnel()
   else:
    
    create_log2(server_info[2], client_data ,"502 Bad Gateway")
     client_socket.close()
     proxy_socket.close()
     return
   tunnel()
 
# For nonCONNECT requests
def bar(client_socket, client_IP, server_info, client_data):
   #create server side socket
   proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   #TCP connection request to server
   server_addr = (server_info[0], server_info[1])
   proxy_socket.connect(server_addr)

   while True:
       # send modified data (HTTP request) to server
       modified_data = modify_headers(client_data.decode("utf-8","backslashreplace"))
       proxy_socket.sendall(modified_data.encode("utf-8"))
       # send all each time you receive until there's nothing more to receive
       data = proxy_socket.recv(BUFFER_SIZE)
       print(data.decode("utf-8","backslashreplace"))
       if not data: break
       client_socket.sendall(data)
       response = data

   log once after all data sent
   create_log(server_info[2], client_data.decode("utf-8","backslashreplace"), modified_data, response.decode("utf-8","backslashreplace"))
 
def main():
   # check arguments
   if(len(sys.argv)!=2 and len(sys.argv)!=3):
       print("Incorrect number of arguments. \nUsage python3 http_proxy.py PORT")
       print("Incorrect number of arguments. \nUsage python3 http_proxy.py PORT Log")
       sys.exit()
 
   # enable logging
   if(len(sys.argv)==3 and sys.argv[2]=="Log"):
       global LOG_FLAG
       LOG_FLAG = True
       DIR_NAME = "./Log"
       if not (os.path.isdir(DIR_NAME)):
           os.system("mkdir Log")
 
 
   # create the socket for this proxy
   proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  
   # bind with the port number given and allow connections
   print ("HTTP proxy listening on port ",sys.argv[1])
   proxy_socket.bind(('', int(sys.argv[1])))
   proxy_socket.listen(50) #allow connections 
 
   try:
       while True:
           client_socket, client_IP = proxy_socket.accept()
           t = threading.Thread(target=proxy, args=(client_socket,client_IP,))
           t.start()
   except KeyboardInterrupt: # handle Ctrl+C
       print ("Keyboard Interrupt: Closing down proxy")
       proxy_socket.close()
       os._exit(1)
 
if __name__ == "__main__":
   main()
