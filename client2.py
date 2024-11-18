import socket 


HOST = "192.168.10.5"
SEVER_PORT = 65432
FORMAT = "utf-8"


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("CLIENT SIDE")
client.connect( (HOST,SEVER_PORT) )
print("client address: ",client.getsockname())



msg = None 
while(msg!="x"):
    msg = input("talk: " )
    client.sendall(msg.encode(FORMAT))


input()
client.close()

    