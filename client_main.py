import socket
import os
import logging
import io
import time
import threading
from logging import basicConfig
from tqdm import tqdm

# Tao thanh tien trinh



IP = "127.0.0.1"
PORT = 4455
SIZE = 1024
PORT1 = 65432

FORMAT = "utf-8"
CLIENT_FOLDER = "client_folder"

# Mở file log với mã hóa UTF-8
log_file = io.open("client.log", "a", encoding="utf-8")

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,                # Mức log
    format="%(asctime)s - %(levelname)s - %(message)s",  # Định dạng log
    handlers=[                         #Ghi log qua handler
        logging.FileHandler("client.log", mode="a", encoding="utf-8")  # Đảm bảo mã hóa UTF-8
    ]
)

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
    logging.info(f"Bắt đầu quá trình tải file xuôống")
    client.send(f"DOWNLOAD:{file_name}".encode(FORMAT))
    logging.debug(f"Đã gửi yêu cầu tới sever".encode(FORMAT))

    # Nhan phan hoi tu sever
    msg = client.recv(SIZE).decode(FORMAT)

    if msg.startswith("ERROR"):
        print(f"[CLIENT] Lỗi từ server: {msg}")
        logging.error(f"Sever errror")
        return
    elif msg == "OK":
        print("[CLIENT] Server xác nhận: Bắt đầu tải file.")
        logging.info("Đã nhận được request của sever")
    else:
        print(f"[CLIENT] Phản hồi không xác định: {msg}")
        return
    # Nhan kich thuoc file 
    try:
        file_size = int(client.recv(SIZE).decode(FORMAT))
        print(f"[CLIENT] Kích thước file: {file_size} bytes")  # DEBUG
        logging.info(f"Client đã gửi kích thước file cho sever".encode(FORMAT))

        client.send("READY".encode(FORMAT))
    except ValueError:
        print("[CLIENT] Lỗi: Không thể chuyển đổi kích thước file.")
        logging.error("Lỗi trong việc chuyển đổi kích thuoớc file từ sever gửi về")


        return

    # Bat dau nhan du lieu  va hien thi tien trinh tai 
    progress_bar = tqdm(total=file_size,desc=f"Tai file {file_name}", unit="B",unit_scale=True)

    received_data = b""
    # Khoi tao thanh tien trinh 
    while len(received_data) < file_size:
        chunk = client.recv(SIZE)
        if not chunk:
            break
        received_data += chunk
        progress_bar.update(len(chunk))
        print(f"[CLIENT] Đã nhận {len(received_data)} / {file_size} bytes")  # DEBUG
        logging.debug(f"Client đã nhận được {len(received_data)} / {file_size} bytes ")

    progress_bar.close()


    # Lưu file
    file_path = os.path.join(CLIENT_FOLDER, file_name)
    with open(file_path, "wb") as file:
        file.write(received_data)
    print(f"[CLIENT] File '{file_name}' đã được tải về tại '{file_path}'.")
    logging.info(f"File '{file_name}' đã được tải về tại '{file_path}")



def upFile(client, file_name):
    logging.info("Bat dau qua trinh tai xuong ")

    if os.path.exists(file_name):
        # Gửi tên file
        client.send(f"UP:{file_name}".encode(FORMAT))
        logging.debug("Da gui yeu cau toi sever")

        # Chờ ACK từ server
        ack = client.recv(SIZE).decode(FORMAT)
        logging.debug("Da nhan duoc request cua Sever")
        if ack != "[SERVER] Đã nhận tên file.":
            print("Lỗi: Không nhận được ACK từ server.")
            logging.error("Lỗi không nhận được request từ sever")

            return
        with open(file_name, "rb") as f:
            while chunk := f.read(SIZE):
                client.sendall(chunk)
                # Chờ ACK từ server sau mỗi lần gửi dữ liệu
                ack = client.recv(SIZE).decode(FORMAT)
                logging.info("Gửi ACK sau mỗi lần gửi dữ liệu")
                if ack != "ACK":
                    print("Lỗi: Không nhận được ACK từ server.")
                    return

        # Gửi tín hiệu kết thúc
        client.send(b"OK")
        logging.debug("Nhận được tín hiệu kết thúc của sever")

        # Nhận phản hồi từ server
        msg = client.recv(SIZE).decode(FORMAT)
        print(f"{msg}")
        logging.info(f"Thông báo đã up load xong file {file_name}")

    else:
        print("File không tồn tại.")

def main():
    # Khởi chạy client
    client= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((IP,8008))
    print(f"[CLIENT] Đã kết nối với sever thành công !!")



    try:
        while True:
            print("\n-----MENU-----\n")
            print("1. Tải file từ sever ")
            print("2. UpFile từ client lên Sever")
            print("3. Thoát")

            choice = input("Nhập lựa chọn: " )


            if choice =="1":
                file_name = input("Nhâpj tên file cần tải về: ")
                downloadFile(file_name,client)
            elif choice =="3":
                print(f"[CLIENT] Đóng kết nối !!")
                client.send("CLOSE".encode(FORMAT))
                break
            elif choice =="2":
                file_name = input("Nhập tên file cần upload: ")
                if file_name:
                    upFile(client,file_name)
                else:
                    print(f"[CLIENT] Tên file không được để trống")



            else:
                print("Lựa chọn không hợp lệ vui lòng nhập lại \n")
    except Exception as e:
        print("Lỗi")
    finally:
        client.close()
        print("Kết nối đã đóng")


if __name__ == "__main__":
    main()


