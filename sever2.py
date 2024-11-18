import socket 


HOST = "192.168.10.5"

SEVER_PORT = 65432
FORMAT ="utf-8"


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((HOST, SEVER_PORT))
s.listen()


print("SEVER SIDE ")
print("sever: ", HOST,SEVER_PORT)
print("Waiting for Client")

conn, addr = s.accept()
print("client address: ",addr)
print("conn: ", conn.getsockname())

msg = None
while(msg!="x"):
    msg = conn.recv(1024).decode(FORMAT)
    print("client ", addr,"says", msg)

