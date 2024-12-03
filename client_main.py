import socket 
import os


IP = "127.0.0.1"
PORT = 4455
SIZE =1024
FORMAT ="utf-8"
CLIENT_FOLDER = "client_folder"


def main(): 
    print("[STARTING], Sever is starting . \n")
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)  # điều này đảm bảo client và sever cùng sử dụng chung một giao thức đó lả TCP - IP 
    client.connect((IP,PORT))
    

    msg = "Hello sever !"

    client.send(msg.encode(FORMAT))
     











if __name__ == "__main__":
    main