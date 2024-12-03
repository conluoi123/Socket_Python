import socket 
import os


IP = "127.0.0.1"  # Có thể dễ dàng thay bằng địa chỉ IP mạng của máy tính 
PORT = 4455
SIZE =1024
FORMAT ="utf-8"
SEVER_FOLDER = "sever_folder"


def main(): 
    print("[STARTING] Sever is starting . \n")
    sever = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    sever.bind((IP,PORT))  # gán IP vào cổng port -> điều này cho sever lắng nghe kết nối từ client 
    sever.listen()
    print("[LISTENING], Sever is waiting for client . \n")


    while True: 
       conn, addr = sever.accept()
       print("[NEW CONNECTIONS], {adr} connected . \n")


       msg = conn.recv(SIZE).decode(FORMAT)
       print(msg)
       
        











if __name__ == "__main__":
    main