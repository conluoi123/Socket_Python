import socket 


# 192.168.1.106
HOST ="127.0.0.1"  #loopback

# IP="192.168.10.5"

SEVER_PORT=65432  # laays port nao cung duoc mien la lon hon 5000
FORMAT ="utf-8"


s= socket.socket(socket.AF_INET,socket.SOCK_STREAM)

s.bind((HOST,SEVER_PORT))
s.listen()

print("SEVER SIDE")
print("sever: ",HOST,SEVER_PORT)
print("Waiting for CLient")

conn, addr =s.accept()
print("client address: ",addr)
print("conn: ",conn.getsockname())

username = conn.recv(1024).decode(FORMAT)
# kiểm tra để nhận rồi hay chưa 
conn.sendall(username.encode(FORMAT))

psw = conn.recv(1024).decode(FORMAT)

print("username: ",username)
print("password: ", psw)


input()
