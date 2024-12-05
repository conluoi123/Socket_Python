import socket
import os
import threading

IP = "127.0.0.1"  # Có thể dễ dàng thay bằng địa chỉ IP mạng của máy tính
PORT = 4455
PORT1 = 65432
SIZE = 1024
FORMAT = "utf-8"
SEVER_FOLDER = "sever_folder"


def nhanFolder():
    print("[STARTING] Sever is starting . \n")
    sever = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sever.bind((IP, PORT))  #gán IP vào cổng port -> điều này cho sever lắng nghe kết nối từ client
    sever.listen()
    print("[LISTENING], Sever is waiting for client . \n")

    while True:
        conn, addr = sever.accept()
        print("[NEW CONNECTIONS], {addr} connected . \n")

        """  Receive name folder """
        folder_name = conn.recv(SIZE).decode(FORMAT)

        """Creating the folder"""
        # sau khi nhận được tên ta đi tạo thư mục
        folder_path= os.path.join(SEVER_FOLDER,folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            conn.send(f"Folder({folder_name}) created.".encode(FORMAT))
        else:
            conn.send(f"Folder({folder_name}) already exists .".encode(FORMAT))


        """Nhận các tệp từ client"""
        while True:
            try:
                msg = conn.recv(SIZE).decode(FORMAT)
                print(f"[CLIENT] {msg}")

                cmd, data = msg.split(":") # lấy dữ liệu từ file gửi

                if cmd == "FILENAME":
                    """Xử lý khi nhận tên tệp"""
                    print(f"[CLIENT] Nhận tên file : {data}")
                    file_path = os.path.join(folder_path, data)
                    file = open(file_path, "wb")   # ghi dữ liệu dưới dạng nhị phân
                    conn.send("Nhận tên file thành công .".encode(FORMAT))

                elif cmd == "DATA":
                    """Xử lý khi nhận dữ liệu tệp"""
                    print(f"[CLIENT] Gửi dữ liệu tệp: {file_path}")
                    # ĐỌc kích thước dữ liệu
                    data_size = int(data)
                    conn.send("READY".encode(FORMAT))


                    # Nhận toàn bộ dữ liệu
                    received_data = b""
                    while len(received_data) < data_size:
                        chunk = conn.recv(SIZE)
                        if not chunk:
                            break
                        received_data += chunk

                    file.write(received_data)
                    conn.send("ACK".encode(FORMAT))  # Gửi phản hồi ACK
                    print(f"[SERVER] Đã nhận xong dữ liệu tệp: {file_path}")

                elif cmd == "FINISH":
                    """Hoan thanh ten tep"""
                    print(f"[CLIENT] File transfer completed for: {file_path}")
                    file.close()
                    conn.send("File transfer complete.".encode(FORMAT))

                elif cmd == "CLOSE":
                    """Dong ket noi"""
                    print("[CLIENT] Connection close request received.")
                    conn.send("Connection closed.".encode(FORMAT))
                    break

            except Exception as e:
                print(f"[ERROR] {e}")
                break

        conn.close()
        print(f"[CONNECTION CLOSED] {addr} \n")


def downloadFile_request(conn, msg):
    try:
        if not msg:  # Nếu msg rỗng hoặc None
            conn.send("ERROR: msg rỗng.".encode(FORMAT))
            return
        cmd, file_name = msg.split(":")
        if cmd != "DOWNLOAD":
            conn.send("ERROR: Lỗi .".encode(FORMAT))
            return
    except ValueError:
        conn.send("ERROR: Lỗi format của msg.".encode(FORMAT))
        return

    file_path = os.path.join(SEVER_FOLDER, file_name)
    print(f"[SERVER] Tải file: {file_path}")
    conn.send(f"OK".encode(FORMAT))
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        conn.send(str(file_size).encode(FORMAT))
        ack = conn.recv(SIZE).decode(FORMAT)

        if ack != "READY":
            print("[SERVER] Lỗi: Client không sẵn sàng.")
            return

        # Gửi nội dung file
        with open(file_path, "rb") as file:
            data = file.read()
            conn.sendall(data)
            print(f"[SERVER] Đã gửi {len(data)} bytes dữ liệu.")  # DEBUG

    else:
        error_message = f"ERROR: File '{file_name}' không tồn tại."
        conn.send(error_message.encode(FORMAT))
        print(f"[SERVER] {error_message}")


def upFile_request(conn, msg):
    # Nhận tin nhắn đầu tiên từ client
    try:
        # msg = conn.recv(SIZE).decode(FORMAT)
        # print(msg)

        # if not msg:
        #     print("[SERVER] Không nhận được tin nhắn từ client.")
        #     return

        # Xử lý lệnh upload
        file_name = msg.split(":")[1].strip()
        file_name = "msg.txt"

        print(f"[SERVER] Đã nhận được tên file: {file_name}")

        # Gửi ACK đầu tiên
        conn.send("[SERVER] Đã nhận tên file.".encode(FORMAT))

        with open(file_name, "wb") as f:
            while True:
                data = conn.recv(SIZE)
                print(f"data: {data}")
                if data == b"OK":  # Kiểm tra tín hiệu kết thúc
                    print("[SERVER] Nhận tín hiệu kết thúc upload.")
                    break
                elif data:  # Nếu có dữ liệu, ghi vào file
                    f.write(data)
                    conn.send(b"ACK")  # Gửi ACK
                    print(f"[SERVER] Ghi {len(data)} bytes vào file.")

        print(f"[SERVER] Đã nhận xong file: {file_name}\n")
        conn.send("[SERVER] Upload thành công.\n".encode(FORMAT))
    except Exception as e:
        print(f"[SERVER] Lỗi trong quá trình upload: {e}")
        conn.send("[SERVER] Lỗi trong quá trình upload.\n".encode(FORMAT))


def main():
    sever = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sever.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #fix  address in use
    sever.bind((IP, 8008))
    sever.listen()

    # Chỗ này chừa cho trường hợp đa luồng
    while True:
        conn, addr = sever.accept()
        try:
            print("Đã kết nối với Client.")
            while True:
                try:
                    msg = conn.recv(SIZE).decode(FORMAT)
                    if not msg:  # Kiểm tra khi không nhận được dữ liệu
                        print("[SERVER] Không nhận được tin nhắn từ client.")
                        break
                    print(f"[SERVER] Nhận được tin nhắn: {msg}")

                    if msg.startswith("UP:"):
                        upFile_request(conn, msg)
                    elif msg.startswith("DOWNLOAD:"):
                        downloadFile_request(conn, msg)
                    else:
                        print("[SERVER] Tin nhắn không hợp lệ.")
                except socket.timeout:
                    print("[SERVER] Đã hết thời gian chờ, không nhận được dữ liệu.")
                    break
                except Exception as e:
                    print(f"[SERVER] Lỗi khi nhận dữ liệu: {e}")
                    break

        except Exception as e:
            print(f"Lỗi kết nối: {e}")
        finally:
            conn.close()
            print("[SERVER] Connection closed.")



if __name__ == "__main__":
    main()

