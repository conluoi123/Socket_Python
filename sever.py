import socket 
import threading

HOST ="127.0.0.1"  #loopback

SEVER_PORT=65432  # lay port nao cung duoc mien la lon hon 5000
FORMAT ="utf-8"

server_socket= socket.socket(socket.AF_INET,socket.SOCK_STREAM)

try:
  s.bind((HOST,SEVER_PORT))
except socket.error as e:
  print(str(e))
  
s.listen(10)
thread_count = 0

print("SEVER SIDE")
print("sever: ",HOST,SEVER_PORT)
print("Waiting for CLient")

def upload_file(conn, addr):
  

def handle_client(conn, addr):
  
while True:
  try:
    conn, addr =s.accept()
    print("client address: ",addr)
    print("conn: ",conn.getsockname())
    username = conn.recv(1024).decode(FORMAT)
    # kiểm tra để nhận rồi hay chưa 
    conn.sendall(username.encode(FORMAT)
    psw = conn.recv(1024).decode(FORMAT)
    print("username: ",username)
    print("password: ", psw)
  except socket.error as e:
    print(str(e))

