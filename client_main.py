import socket
import os
import threading
IP = "127.0.0.1"
PORT = 4455
SIZE = 1024
PORT1 = 65432

FORMAT = "utf-8"
CLIENT_FOLDER = "client_folder"


def guiFolder():
    """Starting a tcp socket """
    print("[STARTING], Sever is starting . \n")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # điều này đảm bảo client và sever cùng sử dụng chung một giao thức đó lả TCP - IP
    client.connect((IP, PORT))

    """Folder path"""
    path = os.path.join(CLIENT_FOLDER,"files")
    folder_name = path.split("\\")[1]

    # lyucs này folder_name là một mảng hai phần

    """Sending the folder"""
    msg = f"{folder_name}"
    print(f"[CLIENT] Sending folder name: {folder_name}")
    client.send(msg.encode(FORMAT))

    """Receiving the reply from the sever """
    msg = client.recv(SIZE)
    if msg:
        msg = msg.decode(FORMAT)
        print(f"[SERVER] {msg} \n")
    else:
        print("[SERVER] No message received or connection closed.")

    """ Sending files """
    files = sorted(os.listdir(path))

    for file_name in files:
        """ Send the file name """
        print(file_name)
        msg = f"FILENAME:{file_name}"
        print(msg)
        print(f"[CLIENT] Sending file name: {file_name}")
        client.send(msg.encode(FORMAT))

        """ Nhận phản hồi từ sever """
        msg = client.recv(SIZE).decode(FORMAT)
        print(f"[SERVER] {msg}")
        """Gửi data của file """
        with open(os.path.join(path, file_name), "rb") as file:
            print(f"[CLIENT] Đang gửi dữ liêu của file. ")
            # đọc toàn bộ dữ liệu tệp
            file_data = file.read()
            # Gửi lệnh bắt đầu truyền dữ liệu
            client.send(f"DATA:{len(file_data)}".encode(FORMAT)) # Gửi độ dài dữ lieuj trước
            print(len(file_data))

            # Tí nữa làm cái tiến trình tải luôn
            ack = client.recv(SIZE).decode(FORMAT)
            if ack!="READY":
                print(f"[CLIENT] Không nhận được READY từ sever !!")
            else:
                # Gửi toàn bộ dữ liệu qua sever
                client.sendall(file_data)


                # Nhận phản hồi từ sever
                msg = client.recv(SIZE).decode(FORMAT)
                if msg =="ACK":
                    print(f"[SEVER] Đã nhận xong file: {file_name}")
                else:
                    print(f"[CLIENT] Lỗi không nhận được ACK từ sever.")

            # Gửi lệnh FINISH
            client.send("FINISH:oke".encode(FORMAT))
            msg = client.recv(SIZE).decode(FORMAT)
            print(f"[SERVER] {msg}")



def downloadFile(file_name, client):
    client.send(f"DOWNLOAD:{file_name}".encode(FORMAT))
    print("Đã vào tới đây !!!")  # DEBUG

    # Nhận phản hồi từ server
    msg = client.recv(SIZE).decode(FORMAT)
    if msg.startswith("ERROR"):
        print(f"[CLIENT] Lỗi từ server: {msg}")
        return
    elif msg == "OK":
        print("[CLIENT] Server xác nhận: Bắt đầu tải file.")
    else:
        print(f"[CLIENT] Phản hồi không xác định: {msg}")
        return

    # Nhận kích thước file
    try:
        file_size = int(client.recv(SIZE).decode(FORMAT))
        print(f"[CLIENT] Kích thước file: {file_size} bytes")  # DEBUG
        client.send("Sẵn sàng".encode(FORMAT))
    except ValueError:
        print("[CLIENT] Lỗi: Không thể chuyển đổi kích thước file.")
        return

    # Bắt đầu nhận dữ liệu file
    received_data = b""
    while len(received_data) < file_size:
        chunk = client.recv(SIZE)
        if not chunk:
            break
        received_data += chunk
        print(f"[CLIENT] Đã nhận {len(received_data)} / {file_size} bytes")  # DEBUG

    # Lưu file
    file_path = os.path.join(CLIENT_FOLDER, file_name)
    with open(file_path, "wb") as file:
        file.write(received_data)
    print(f"[CLIENT] File '{file_name}' đã được tải về tại '{file_path}'.")
def downloadFileThread(file_name,client):
    threading.Thread(target=downloadFile,args =(file_name,client).start)


def main():
    # Khởi chạy client
    client= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((IP,PORT1))
    print(f"[CLIENT] Đã kết nối với sever thành công !!")



    try:
        while True:
            print("\n-----MENU-----\n")
            print("1. Tải file từ sever ")
            print("2. Thoát")
            choice = input("Nhập lựa chọn: " )


            if choice =="1":
                file_name = input("Nhâpj tên file cần tải về: ")
                downloadFile(file_name,client)
            elif choice =="2":
                print(f"[CLIENT] Đóng kết nối !!")
                client.send("CLOSE".encode(FORMAT))
                break

            else:
                print("Lựa chọn không hợp lệ vui lòng nhập lại \n")
    except Exception as e:
        print("Lỗi")
    finally:
        client.close()
        print("Kết nối đã đóng")


if __name__ == "__main__":
    main()














if __name__ == "__main__":
    main