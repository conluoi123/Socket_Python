import logging
import socket
import os
import threading
import sys
import tkinter as tk
from tkinter.messagebox import askyesno
from tkinter import scrolledtext
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
from time import sleep
from datetime import datetime

#####################################################################################################
# Quan ly tai khoan
live_account = []
user_account = []
file_path = r"database\account_data.txt"


# Ket noi toi database tai khoan
def getAccountList():
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(';')
            username = parts[0]
            password = parts[1]
            user_account.append([username, password])

# Tạo tài khoản mới
def createNewAccount(username, password):
    with open(file_path, 'a') as f:
        f.write('\n')
        f.write(f"{username};{password}")
    getAccountList()

# Kiểm tra tài khoản có đang hoạt động
def checkLiveAccount(username):
    for row in live_account:
        if username == row[0]:
            return True
    return False
#Lấy tên username đăng nhập ở address
def getAddrUsername(addr):
    for row in live_account:
        if row[1] == addr:
            return row[0]

#####################################################################################################
#Viết log cho server
SERVER_LOG = r"server_log"
def LogFolder():
    """
    Tạo thư mục con theo ngày hiện tại trong SERVER_LOG nếu chưa tồn tại.
    """
    now = datetime.now()
    curr_date = now.strftime("%d_%m_%Y")
    log_path = os.path.join(SERVER_LOG, curr_date).replace("/", "\\")

    os.makedirs(log_path, exist_ok=True)  # Đảm bảo thư mục tồn tại
    return log_path

def setup_logging(username):
    """
    Thiết lập logging cho một user cụ thể.
    - Mỗi user có file log riêng.
    - Đảm bảo không bị trùng handler khi gọi nhiều lần.
    """
    log_path = os.path.join(LogFolder(), f"{username}.log").replace("/", "\\")

    # Tạo một logger mới cho mỗi `username`
    logger = logging.getLogger(username)

    if not logger.hasHandlers():  # Tránh thêm nhiều handler trùng lặp
        handler_file = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        handler_console = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s')
        handler_file.setFormatter(formatter)
        handler_console.setFormatter(formatter)

        logger.addHandler(handler_file)
        logger.addHandler(handler_console)

        logger.setLevel(logging.INFO)

    return logger
#####################################################################################################
# Set up server
HOST = "127.0.0.1"
PORT = 65432
FORMAT = "utf8"
DISCONNECT = "x"
Thread = 0
SERVER_FOLDER = r"server_data"
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Mở server và chờ kết nối
def openServer():
    try:
        print(f"Server [{HOST}][{PORT}]")
        server_socket.bind((HOST, PORT))
        print("Waiting for client to connect...")
        server_socket.listen()
        while True:
            try:
                conn, addr = server_socket.accept()
                print(f"Client {addr} is connected")
                thr = threading.Thread(target=handle_client, args=(conn, addr))
                thr.daemon = True
                thr.start()
            except Exception as e:
                print(f"An error occured: {e}")
    except Exception as e:
        print(f"An error occured: {e}")
        closeServer()
#Đóng server
def closeServer():
    print("SERVER IS CLOSING IN 3 SECONDS")
    sleep(3)
    print("CLOSED")
    server_socket.close()

#####################################################################################################
# SIGN UP AND LOGIN INTO THE SERVER
#Đăng nhập tài khoản
def Login(sub_socket, addr):
    username = sub_socket.recv(1024).decode(FORMAT)
    # Bao lai cho client rang server da nhan duoc username
    sub_socket.sendall("1".encode(FORMAT))

    password = sub_socket.recv(1024).decode(FORMAT)
    # Bao lai cho client rang server da nhan duoc password
    sub_socket.sendall("1".encode(FORMAT))

    # fa     : Dang nhap that bai
    # tr      : Dang nhap thanh cong
    # du : Dang nhap bi trung lap (Tai khoan dang hoat dong o may khac)

    if checkLiveAccount(username):
        buffer = "du"
        sub_socket.sendall(buffer.encode(FORMAT))
        return buffer

    check = False
    try:
        for row in user_account:
            check_user = row[0].strip()
            if username == check_user:
                check = True
                check_pass = row[1].strip()
                if check_pass == password:
                    # print("Login successfully!")
                    live_account.append([username, addr])
                    buffer = "tr"
                    sub_socket.sendall(buffer.encode(FORMAT))
                    return buffer
                else:
                    # print("Invalid password [!]")
                    buffer = "fa"
                    sub_socket.sendall(buffer.encode(FORMAT))
                    return buffer
        if not check:
            buffer = "fa"
            sub_socket.sendall(buffer.encode(FORMAT))
            return buffer
    except Exception as e:
        print(f"An error occured: {e}")
        buffer = "fa"
        sub_socket.sendall(buffer.encode(FORMAT))
        return buffer

#Đăng kí tài khoản
def SignUp(sub_socket):
    username = sub_socket.recv(1024).decode(FORMAT)
    #Xác nhận lại cho client
    sub_socket.sendall("1".encode(FORMAT))

    password = sub_socket.recv(1024).decode(FORMAT)
    #Xác nhận lại cho client
    sub_socket.sendall("1".encode(FORMAT))

    # true  : Tao tai khoan thanh cong
    # false : Tao tai khoan that bai

    buffer = True
    if username == "admin":
        sub_socket.sendall("fa".encode(FORMAT))
        sub_socket.recv(1)
        buffer = False
    else:
        for row in user_account:
            if row[0].strip() == username:
                sub_socket.sendall("fa".encode(FORMAT))
                sub_socket.recv(1)
                buffer = False
    if buffer:
        sub_socket.sendall("tr".encode(FORMAT))
        sub_socket.recv(1)
        createNewAccount(username, password)
        print("Sign up successfully!")

#Menu nhận yêu cầu đăng nhập hoặc đăng kí từ client
def LogInOrSignUp(sub_socket, addr):
    """
        Hàm xử lý đăng nhập và đăng ký của client.
        Mỗi client có một file log riêng biệt.
        """
    # Tạo logger riêng cho client dựa trên địa chỉ IP và cổng của client
    logger = setup_logging(f"client_{addr[0]}_{addr[1]}")

    logger.info(f"Fetching account list for login/signup process.")
    getAccountList()
    logger.info(f"Connected to client at {addr}")

    try:
        # Nhận lựa chọn của client
        option = sub_socket.recv(1024).decode(FORMAT)
        logger.debug(f"Option received from client at {addr}: {option}")

        if option == "login":
            logger.info(f"Client at {addr} selected login.")
            buffer = Login(sub_socket, addr)

            if buffer == "tr":
                logger.info(f"Client at {addr} logged in successfully with username: {getAddrUsername(addr)}. Terminating session.")
                return
            else:
                logger.warning(f"Client at {addr} failed to log in. Retrying...")
                LogInOrSignUp(sub_socket, addr)

        elif option == "signup":
            logger.info(f"Client at {addr} selected signup.")
            SignUp(sub_socket)
            logger.info(f"Client at {addr} completed signup. Returning to main menu.")
            LogInOrSignUp(sub_socket, addr)  # Quay lại menu chính

        else:
            logger.error(f"Invalid option received from client at {addr}: {option}")
            logger.info(f"Asking client at {addr} to retry.")
            # Có thể gửi lại yêu cầu chọn đúng option cho client tại đây

    except Exception as e:
        logger.exception(f"An error occurred with client at {addr}: {e}")
        # Exception cụ thể sẽ được ghi vào log nhờ logger.exception

#####################################################################################################
#UPLOAD FUNCTIONS
#Hàm kiểm tra có file trùng tên trên server hay không tránh lặp file
def ifExist(file_name):
    name, ext = os.path.splitext(file_name)
    files = sorted(os.listdir(SERVER_FOLDER))
    stamp = 1
    file_name = f"{name}{ext}"
    for file in files:
        if file_name == file:
            file_name = f"{name}({stamp}){ext}"
            stamp += 1

    return file_name

#Hàm tạo đường dẫn cho file mới
def createFolderPath(folder_name, root):
    folder_name = ifExist(folder_name)
    folder_path = os.path.join(root, folder_name).replace("/", "\\")
    os.makedirs(folder_path)
    return folder_path

#Hàm xử lí yêu cầu upload file
def uploadFileRequest(sub_socket, folder_path, addr):
    """
        Hàm xử lý việc nhận và lưu tệp từ client, với logging cho mỗi client.
        """
    # Tạo logger riêng cho client dựa trên địa chỉ IP và cổng của client
    logger = setup_logging(f"client_{addr[0]}_{addr[1]}")

    file_path = ""
    file = None
    while True:
        try:
            msg = sub_socket.recv(1024).decode(FORMAT)
            if msg:
                logger.info(f"[CLIENT] {msg}")
                cmd, data = msg.split(":")  # lấy dữ liệu từ file gửi

                if cmd == "FILENAME":
                    """Xử lý khi nhận tên tệp"""
                    logger.info(f"Received file name : {data}")
                    file_name = ifExist(data)
                    file_path = os.path.join(folder_path, file_name).replace("/", "\\")
                    logger.info(f"Received file {data} in folder {folder_path} !!")
                    sub_socket.send("y".encode(FORMAT))

                elif cmd == "DATA":
                    """Xử lý khi nhận dữ liệu tệp"""
                    file = open(file_path, "wb")  # ghi dữ liệu dưới dạng nhị phân
                    logger.info(f"Send file data of {os.path.basename(file_path)}")
                    # Đọc kích thước dữ liệu
                    data_size = int(data)
                    sub_socket.send("READY".encode(FORMAT))

                    # Nhận toàn bộ dữ liệu
                    sub_socket.settimeout(5.0)
                    received_data = b""
                    while len(received_data) < data_size:
                        try:
                            chunk = sub_socket.recv(1024)
                            if not chunk:
                                break
                            received_data += chunk
                        except socket.timeout:
                            sub_socket.settimeout(None)
                            logger.error("Client stop uploading file!")
                            file.close()
                            os.remove(file_path)
                            return
                    sub_socket.settimeout(None)
                    file.write(received_data)
                    sub_socket.send("ACK".encode(FORMAT))  # Gửi phản hồi ACK
                    logger.info(f"Upload success: {os.path.basename(file_path)}")

                elif cmd == "FINISH":
                    """Hoàn thành nhận tệp"""
                    logger.info(f"File transfer completed for: {os.path.basename(file_path)}")
                    file.close()
                    sub_socket.send("File transfer completed.".encode(FORMAT))
                    break

        except Exception as e:
            logger.error(f"An error occurred while processing file transfer: {e}")
            break

#Hàm upload folder tuần tự
def uploadFolderSyn(sub_socket, root, addr):
    try:
        logger = setup_logging(f"client_{addr[0]}_{addr[1]}")
        #Nhận tên folder từ client
        folder_name = sub_socket.recv(1024).decode(FORMAT)
        logger.debug(f"Received folder name: {folder_name}")
        #Tạo folder để chứa
        folder_path = createFolderPath(folder_name, root)
        logger.info(f"Created folder path: {folder_path}")
        # Xác nhận lại với client
        sub_socket.sendall("y".encode(FORMAT))
        logger.debug(f"Sent acknowledgment to client for folder creation.")
        #Nhận số lượng folder con
        count = int(sub_socket.recv(1024).decode(FORMAT))
        logger.debug(f"Number of subfolders to upload: {count}")
        #Xác nhận lại với client
        sub_socket.send("y".encode(FORMAT))
        logger.debug(f"Sent acknowledgment to client for folder creation.")
        #Ưu tiên upload các folder con
        for i in range(count):
            logger.info(f"Uploading subfolder {i+1} of {count}.")
            uploadFolderSyn(sub_socket, folder_path, addr)
        #Đặt trạng thái upload các file con
        buffer = sub_socket.recv(2).decode(FORMAT)
        logger.debug(f"Received file upload buffer: {buffer}")
        sub_socket.send("y".encode(FORMAT))
        #Lặp while kiểm tra trạng thái để upload các file con
        while buffer == "no":
            logger.warning(f"Client indicates file upload pending in folder: {folder_path}")
            uploadFileRequest(sub_socket, folder_path, addr)
            buffer = sub_socket.recv(2).decode(FORMAT)
            logger.debug(f"Received file upload buffer after retry: {buffer}")
            sub_socket.send("y".encode(FORMAT))

        sub_socket.sendall(f"FOLDER {folder_name} UPLOAD SUCCESS".encode(FORMAT))
        sub_socket.recv(1)
        logger.info(f"Folder upload successful for path: {folder_path}")

    except Exception as e:
        logger.exception(f"An error occurred during folder upload synchronization for root path {root}: {e}")

##################################################################
#DOWNLOAD FUNCTIONS
server_files = []
#Hàm tìm file
def findFile(file_name):
    file_path = ""
    for root, dirs, files in os.walk(SERVER_FOLDER):
        for file in files:
            if file_name == file:
                file_path = os.path.join(root, file_name).replace("/", "\\")

    return file_path

#Hàm xử lí yêu cầu tải file
def downloadFile(sub_socket, addr):
    logger = setup_logging(f"client_{addr[0]}_{addr[1]}")
    msg = sub_socket.recv(1024).decode(FORMAT)

    if not msg:  # Nếu msg rỗng hoặc None
        sub_socket.send("NO".encode(FORMAT))
        logger.error(f"[{addr}] Received empty message.")
        return
    cmd, file_name = msg.split(":")
    logger.info(f"[{addr}] Command received: {cmd}, File requested: {file_name}")
    if cmd != "DOWNLOAD":
        logger.error(f"[{addr}] Invalid command: {cmd}")
        sub_socket.send("NO.".encode(FORMAT))
        return

    file_path = findFile(file_name)
    logger.info(f"[{addr}] Searching for file: {file_name}. Found path: {file_path}")
    print(f"{addr} is downloading: {file_path}")

    if os.path.exists(file_path):
        logger.info(f"[{addr}] File exists: {file_path}. Preparing to send.")
        sub_socket.send("OK".encode(FORMAT))  # Gửi phản hồi OK
        file_size = os.path.getsize(file_path)
        sub_socket.send(str(file_size).encode(FORMAT))
        ack = sub_socket.recv(1024).decode(FORMAT)
        sub_socket.send("y".encode(FORMAT))
        if ack != "READY":
            print(f"Error: {addr} is not ready.")
            logger.error(f"[{addr}] Client not ready for file transfer: {file_name}")
            return

        # Gửi nội dung file
        with open(file_path, "rb") as file:
            data = file.read()
            sub_socket.sendall(data)
            print(f"Sending file size: {len(data)}.")  # DEBUG
            logger.info(f"[{addr}] Sent file: {file_name} ({len(data)} bytes)")

    else:
        error_message = f"ERROR: File '{file_name}' is not exist."
        sub_socket.send("NO".encode(FORMAT))
        print(f"[SERVER] {error_message}")
        logger.error(f"[{addr}] {error_message}")

#Hàm gửi danh sách dữ liệu mà server đang có
def server_data(sub_socket, addr):
    for root, dirs, files in os.walk(SERVER_FOLDER):
        for file in files:
            server_files.append(file)

    sub_socket.sendall(str(len(server_files)).encode(FORMAT))
    sub_socket.recv(1)

    for i in range(len(server_files)):
        sub_socket.sendall(str(server_files[i]).encode(FORMAT))
        sub_socket.recv(1)
    server_files.clear()

##################################################################
#Hàm nhận yêu cầu upload file hoặc folder
def upload_request(sub_socket, addr):
    print("Waiting for upload option!")
    try:
        up_req = sub_socket.recv(1024).decode(FORMAT)

        sub_socket.send("y".encode(FORMAT))

        print(up_req)

        try:
            if up_req == "file":
                msg = sub_socket.recv(1).decode(FORMAT)
                sub_socket.send("y".encode(FORMAT))
                if msg == "y":
                    uploadFileRequest(sub_socket, SERVER_FOLDER, addr)
                else:
                    print("No file upload!")

            elif up_req == "folder":
                option = sub_socket.recv(1024).decode(FORMAT)
                sub_socket.send("y".encode(FORMAT))
                if option == "1":
                    uploadFolderSyn(sub_socket, SERVER_FOLDER, addr)
                else:
                    print("No folder upload!")
            else:
                print("Invalid option")
        except Exception as e:
            print(f"An error occured: {e}")
    except Exception as e:
        print(f"An error occured: {e}")
#####################################################################################################
#Hàm nhận yêu cầu tải file của client
def download_request(sub_socket, addr):
    server_data(sub_socket, addr)
    msg = sub_socket.recv(1).decode(FORMAT)
    sub_socket.send("y".encode(FORMAT))
    if msg == "y":
        downloadFile(sub_socket, addr)
    else:
        print("Client is not ready for downloading!")

#####################################################################################################
#hàm đợi yêu cầu tải hoặc download
def upload_download_waiting(sub_socket, addr):
    while True:
        msg = sub_socket.recv(1024).decode(FORMAT)
        sub_socket.send("y".encode(FORMAT))

        if msg == "upload":
            upload_request(sub_socket, addr)
        elif msg == "download":
            download_request(sub_socket, addr)
        elif msg == "logout":
            index = 0
            for acc in live_account:
                if acc[1] == addr:
                    live_account.pop(index)
                index += 1
            handle_client(sub_socket, addr)
            break
        else:
            break


#####################################################################################################
# Thao tác với Client
def handle_client(conn, addr):
    try:
        LogInOrSignUp(conn, addr)
        upload_download_waiting(conn, addr)
        index = 0
        for acc in live_account:
            if acc[1] == addr:
                live_account.pop(index)
            index += 1
        print(f"Client {addr} disconnected")
        conn.close()
    except:
        index = 0
        for acc in live_account:
            if acc[1] == addr:
                live_account.pop(index)
            index += 1
        print(f"Client {addr} disconnected")
        conn.close()

################################################################################################
#GUI cho admin đăng nhập và kiểm tra user và tài nguyên của server
#username: admin
#password: 123456
class LoginAndSignUp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("A Transfer File Application")
        self.geometry("640x480")
        self.configure(bg="#fff")
        self.resizable(False, False)
        self.img = Image.open(r"Images\login.png")
        self.img = self.img.resize((400, 480))
        self.img = ImageTk.PhotoImage(self.img)
        self.label = Label(self, image=self.img, bg="white")
        self.label.place(x=0, y=0)

        self.LogInGUI()

    def LogInGUI(self):
        # GUI login
        self.logFrame = Frame(self, width=300, height=300, bg='white')
        self.logFrame.place(relx=0.5, rely=0.5, anchor=W)

        heading = Label(self.logFrame, text="ADMIN", fg='#57a1f8', font=("Neuva Std Cond", 23, "bold"), bg='white')
        heading.place(relx=0.4, rely=0.05, anchor=N)

        ######################################################

        def click_in_user(event):
            if self.logFrame.usernameEntry.get() == "Username":
                self.logFrame.usernameEntry.delete(0, 'end')

        self.logFrame.usernameEntry = Entry(self.logFrame, width=20, fg='black', border=0,
                                            font=("Microsoft Yahei UI Light", 14))
        self.logFrame.usernameEntry.place(relx=0.4, rely=0.3, anchor=N)
        self.logFrame.usernameEntry.insert(0, 'Username')
        Frame(self.logFrame, width=150, height=2, bg="black").place(relx=0.28, rely=0.39, anchor=N)
        self.logFrame.usernameEntry.bind("<FocusIn>", click_in_user)

        ######################################################
        def click_in_pass(event):
            if self.logFrame.passwordEntry.get() == "Password":
                self.logFrame.passwordEntry.delete(0, 'end')
            self.logFrame.passwordEntry.config(show="*")

        self.logFrame.passwordEntry = Entry(self.logFrame, width=20, fg='black', border=0,
                                            font=("Microsoft Yahei UI Light", 14))
        self.logFrame.passwordEntry.place(relx=0.4, rely=0.45, anchor=N)
        self.logFrame.passwordEntry.insert(0, 'Password')
        Frame(self.logFrame, width=150, height=2, bg="black").place(relx=0.28, rely=0.54, anchor=N)
        self.logFrame.passwordEntry.bind("<FocusIn>", click_in_pass)

        ######################################################
        self.logFrame.LoginButton = Button(self.logFrame, height=2, text="Login", fg='black',
                                           font=("Microsoft Yahei UI Bold", 14), bg='lightblue', cursor='hand2',
                                           command=self.Login)
        self.logFrame.LoginButton.place(relx=0.6, rely=0.45, anchor=W)

    def Login(self):
        if self.logFrame.usernameEntry.get() == "admin" and self.logFrame.passwordEntry.get() == "123456":
            self.destroy()
            Menu("ADMIN").mainloop()
        else:
            messagebox.showinfo("WARNING", "ADMIN username or password incorrect!")


class Menu(tk.Tk):
    def __init__(self, username):
        super().__init__()

        self.title("A Transfer File Application")
        self.geometry("640x480")
        self.configure(bg="#fff")
        self.resizable(False, False)
        self.img = Image.open(r"Images\menu.jpeg")
        self.img = self.img.resize((640, 480))
        self.img = ImageTk.PhotoImage(self.img)
        self.label = Label(self, image=self.img, bg="white")
        self.label.place(x=0, y=0)

        heading = Label(self.label, text=f"Hello, {username}", fg='#57a1f8', font=("Neuva Std Cond", 16, "bold"),
                        bg='white')
        heading.place(relx=0.15, rely=0.02, anchor=N)

        self.text = scrolledtext.ScrolledText(self, width=75, height=18, bg='white', bd=5, relief="ridge")
        self.text.place(relx=0.5, rely=0.43, anchor=CENTER)
        self.text.config(state=tk.DISABLED)

        sys.stdout = writeConsole(self.text)
        sys.stderr = writeConsole(self.text)

        self.viewUser = Button(self, text=f"VIEW CLIENT", fg='#57a1f8', font=("Neuva Std Cond", 21, "bold"),
                               bg='grey', bd=3, relief='ridge', command=self.viewLiveUser)
        self.viewUser.place(relx=0.4, rely=0.85, anchor=E)

        self.viewResource = Button(self, text=f"VIEW RESOURCE", fg='#57a1f8', font=("Neuva Std Cond", 21, "bold"),
                                   bg='grey', bd=3, relief='ridge', command=self.viewResource)
        self.viewResource.place(relx=0.5, rely=0.85, anchor=W)

        self.closeButton = Button(self, text="QUIT", fg='green', bg="yellow", font=("Microsoft Yahei UI Bold", 14),
                                  cursor='hand2', bd=3, relief='ridge', width=6, command=self.closeAll)
        self.closeButton.place(relx=0.85, rely=0.06, anchor=CENTER)

    def closeAll(self):
        result = askyesno("CLOSE SERVER", "Stop all and quit?")
        if result:
            closeServer()
            self.quit()
            sys.exit()

    def viewLiveUser(self):
        self.user_screen = Toplevel(self)
        self.user_screen.lift()
        self.user_screen.focus_force()
        self.user_screen.title("LIVE USER")
        self.user_screen.geometry("510x335")
        self.user_screen.resizable(False, False)
        self.user_screen.textConsole = scrolledtext.ScrolledText(self.user_screen, wrap=tk.WORD, width=60,
                                                                 height=20)
        self.user_screen.textConsole.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.user_screen.textConsole.config(state=tk.DISABLED)
        self.update_live_user()

    def update_live_user(self):
        self.user_screen.textConsole.config(state=tk.NORMAL)
        self.user_screen.textConsole.delete("1.0", tk.END)  # Xóa thông tin cũ
        for acc in live_account:
            self.user_screen.textConsole.insert('end', f"Username: {acc[0]} is activate at address {acc[1]}\n")
        self.user_screen.textConsole.config(state=tk.DISABLED)

        self.user_screen.after(5000, self.update_live_user)

    def viewResource(self):
        self.resource_screen = Toplevel(self)
        self.resource_screen.lift()
        self.resource_screen.focus_force()
        self.resource_screen.title("SERVER RESOURCE")
        self.resource_screen.geometry("510x335")
        self.resource_screen.resizable(False, False)
        self.resource_screen.textConsole = scrolledtext.ScrolledText(self.resource_screen, wrap=tk.WORD, width=60,
                                                                     height=20)
        self.resource_screen.textConsole.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.resource_screen.textConsole.config(state=tk.DISABLED)
        self.update_server_resource()

    def update_server_resource(self):
        self.resource_screen.textConsole.config(state=tk.NORMAL)
        self.resource_screen.textConsole.delete("1.0", tk.END)  # Xóa thông tin cũ
        index = 0
        for root, dirs, files in os.walk(SERVER_FOLDER):
            for file in files:
                self.resource_screen.textConsole.insert('end', f"{index}.{file}\n")
                index += 1
        self.resource_screen.textConsole.config(state=tk.DISABLED)
        self.resource_screen.after(10000, self.update_server_resource)


class writeConsole:
    def __init__(self, text):
        self.text = text

    def write(self, message):
        self.text.config(state=tk.NORMAL)  # Chuyển trạng thái về NORMAL để có thể ghi
        self.text.insert(tk.END, message)  # Ghi nội dung
        self.text.see(tk.END)  # Cuộn xuống cuối vùng văn bản
        self.text.config(state=tk.DISABLED)  # Chuyển trạng thái về DISABLED để ngăn chặn nhập liệu
        self.text.update_idletasks()

    def flush(self):
        pass
#################################################################################
def main():
    #Tạo luồng server
    server_thr = threading.Thread(target=openServer)
    server_thr.daemon = True
    server_thr.start()
    #Mở GUI
    app = LoginAndSignUp()
    app.mainloop()

if __name__ == "__main__":
    main()