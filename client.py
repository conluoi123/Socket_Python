import socket 




HOST = "127.0.0.1" 
SEVER_PORT = 65432
FORMAT = "utf-8"


client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

print("CLIENT SIDE")
client.connect( (HOST,SEVER_PORT) )
print("client address: ", client.getsockname())

username = input("Username: ")
psw = input("input password: ")

client.sendall(username.encode(FORMAT))

client.recv(1024)

client.sendall(psw.encode(FORMAT))



