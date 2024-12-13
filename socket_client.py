import socket
import os
import threading
import sys
import tkinter as tk
from tkinter.messagebox import askyesno
from tkinter import filedialog, ttk
from tkinter import scrolledtext
from tkinter import *
from tkinter import messagebox
from PIL import Image,ImageTk

###########################################################################################
#Set up Client
HOST        = "127.0.0.1"
PORT        = 65432
FORMAT      = "utf8"
DISCONNECT  = "exit"

socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
###########################################################################################
# User
LOGIN       = "login"
SIGNUP      = "signup"
LOGOUT      = "logout"
UPLOAD      = "upload"
DOWNLOAD    = "download"

#########################################################################
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Hàm tạo kết nối đến server
def connectServer():
    client_socket.connect((HOST, PORT))

#########################################################################
#Hàm đăng nhập
def logInAccount(username, password):
    try:
        client_socket.sendall(username.encode(FORMAT))

        buffer = client_socket.recv(1)
        print(f"Server received Username: {username}")

        client_socket.sendall(password.encode(FORMAT))

        client_socket.recv(1)
        print(f"Server received Password: {password}")

        buffer = client_socket.recv(2).decode(FORMAT)
        if buffer == "fa":
            print("Username or password is not correct! Please try again [!]")
            return buffer
        elif buffer == "du":
            print("User is log in another client")
            return buffer
        elif buffer == "tr":
            print("Login as MEMBER successfully!")
            return buffer

    except Exception as e:
        print(f"An error occured: {e}")

#Hàm đăng ký
def signUpAccount(username, password):
    try:
        client_socket.sendall(username.encode(FORMAT))

        client_socket.recv(1)
        print(f"Server received Username: {username}")

        client_socket.sendall(password.encode(FORMAT))

        client_socket.recv(1)
        print(f"Server received Password: {password}")

        buffer = client_socket.recv(2).decode(FORMAT)
        client_socket.send("y".encode(FORMAT))

        if buffer == "tr":
            print("Sign up successfully")
            return buffer
    except Exception as e:
        print(f"An error occured: {e}")


#########################################################################
CLIENT_FOLDER = r"client_folder" #Đường dẫn chứa file khi muốn tải file
##################################################################
#Hàm upload file
def uploadFile(sck, file_path):
    # gui file_name cho server
    print("------------------------------------")
    file_name = os.path.basename(file_path)
    msg = f"FILENAME:{file_name}"
    print(msg)
    print(f"Sending file name: {file_name}")
    sck.sendall(msg.encode(FORMAT))

    """ Nhận phản hồi từ sever """
    msg = sck.recv(1).decode(FORMAT)

    with open(file_path, "rb") as file:
        file_size = os.path.getsize(file_path)
        sck.sendall(f"DATA: {file_size}".encode(FORMAT))
        print(f"File size: {file_size}")
        ack = sck.recv(1024).decode(FORMAT)
        if ack != "READY":
            print(f"Server has not READY yet !!")
        else:
            # Hiển thị thanh progress_bar
            file_name = os.path.basename(file_path)
            window, progress, percentage_label, stop_flag = progress_bar(file_name, file_size)
            while True:
                if stop_flag[0]:
                    print("User stop uploading file!")
                    return
                file_data = file.read(1024)
                if not file_data:
                    break
                sck.sendall(file_data)
                updating(window, progress, percentage_label , len(file_data), file_name, file_size)

            # Nhận phản hồi từ sever
            msg = sck.recv(1024).decode(FORMAT)
            if msg == "ACK":
                print(f"Upload complete: {file_name}")
            else:
                print(f"Server has not responsed yet!")

        # Gửi lệnh FINISH
        sck.send("FINISH:oke".encode(FORMAT))
        sck.recv(1024).decode(FORMAT)
    window.mainloop()

#Hàm upload folder tuần tự
def uploadFolderSyn(folder_path):
    for root, dirs, files in os.walk(folder_path):
        print("************************************")
        folder_name = os.path.basename(root)
        msg = f"{folder_name}"
        print(f"Sending folder name: {folder_name}")
        client_socket.send(msg.encode(FORMAT))
        client_socket.recv(1)

        client_socket.sendall(str(len(dirs)).encode(FORMAT))
        client_socket.recv(1)

        if dirs:
            for dir in dirs:
                path = os.path.join(root, dir).replace("/", "\\")
                uploadFolderSyn(path)

        client_socket.sendall("no".encode(FORMAT))
        client_socket.recv(1)

        for file_name in files:
            file_path = os.path.join(root, file_name).replace("/", "\\")
            uploadFile(client_socket, file_path)
            if file_name == files[len(files) - 1]:
                client_socket.sendall("ye".encode(FORMAT))
                client_socket.recv(1)
            else:
                client_socket.sendall("no".encode(FORMAT))
                client_socket.recv(1)
        break
    msg = client_socket.recv(1024).decode(FORMAT)
    client_socket.send("y".encode(FORMAT))
    print(msg)
#########################################################################
#DOWNLOAD FILE TO SERVER
#hàm tải file
def downloadFile(file_name):
    client_socket.sendall(f"DOWNLOAD:{file_name}".encode(FORMAT))
    # Nhận phản hồi từ server
    msg = client_socket.recv(2).decode(FORMAT)
    if msg == "OK":
        # Nhận kích thước file
        try:
            file_size = int(client_socket.recv(1024).decode(FORMAT))
            print(f"[CLIENT] Kích thước file: {file_size} bytes")  # DEBUG
            client_socket.send("READY".encode(FORMAT))
            client_socket.recv(1)
        except ValueError:
            print("[CLIENT] Lỗi: Không thể chuyển đổi kích thước file.")
            return

        # Hiển thị thanh tiến trình
        window, progress, percentage_label, stop_flag = progress_bar(file_name, file_size)

        # Bắt đầu nhận dữ liệu file
        received_data = b""
        while len(received_data) < file_size:
            if stop_flag[0]:
                print("User stop downloading file!")
                return
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            received_data += chunk
            updating(window, progress, percentage_label, len(chunk), file_name, file_size)

        # Lưu file
        file_path = os.path.join(CLIENT_FOLDER, file_name)
        with open(file_path, "wb") as file:
            file.write(received_data)
        print(f"[CLIENT] File '{file_name}' đã được tải về tại '{file_path}'.")
    else:
        print(f"An error occured, stop downloading!")
    window.mainloop()
#Hàm lấy danh sách dữ liệu file mà server đang có
def getFileListOnServer():
    file_list = []
    count = int(client_socket.recv(1024).decode(FORMAT))
    client_socket.sendall("y".encode(FORMAT))

    for i in range(count):
        file_list.append(client_socket.recv(1024).decode(FORMAT))
        client_socket.sendall("y".encode(FORMAT))

    return file_list
###########################################################################################
#Hàm đóng kết nối
def closeConnect():
    client_socket.sendall("exit".encode(FORMAT))
    client_socket.recv(1)
    client_socket.close()

###########################################################################################
#Tạo thanh progress bar
def progress_bar(file_name, maxval):
    window = tk.Tk()
    window.title("Progress")
    window.geometry("400x100")  # Điều chỉnh kích thước cửa sổ
    window.resizable(False, False)

    progress = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=20)
    progress["maximum"] = maxval

    # Tạo Label để hiển thị phần trăm
    percentage_label = tk.Label(window, text=f"{file_name} : 0%", font=("Arial", 14))
    percentage_label.pack()

    stop_flag = [False]

    def on_close():
        stop_flag[0] = True
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)

    return window, progress, percentage_label, stop_flag

# Hàm cập nhật thanh tiến trình
def updating(window, progress, percentage_label, value, file_name, maxval):
    if not window.winfo_exists() or not str(progress):
        return
    try:
        progress["value"] += value
        if progress["value"] % 10240 == 0 or progress["value"] >= maxval:  # Cập nhật sau mỗi 10 KB
            percent = (progress["value"] / maxval) * 100
            percentage_label.config(text=f"{file_name} : {int(percent)}%")
            window.update()  # Cập nhật giao diện
        if progress["value"] >= progress["maximum"]:
            window.destroy()
    except:
        return

###########################################################################################
org_stdout = sys.stdout
org_stderr = sys.stderr
# GUI Design
class LoginAndSignUp(tk.Tk):
    connectServer()
    def __init__(self):
        super().__init__()

        self.title("A Transfer File Application")
        self.geometry("640x480")
        self.configure(bg="#fff")
        self.resizable(False,False)
        self.img = Image.open(r"Images\login.png")
        self.img = self.img.resize((400, 480))
        self.img = ImageTk.PhotoImage(self.img)
        self.label = Label(self, image = self.img, bg="white")
        self.label.place(x=0,y=0)

        self.LogInGUI()

    def LogInGUI(self):
        #GUI login
        self.logFrame = Frame(self,width=300,height=300,bg='white')
        self.logFrame.place(relx=0.5,rely=0.5,anchor=W)

        heading = Label(self.logFrame,text="LOGIN",fg='#57a1f8',font=("Neuva Std Cond",23,"bold"),bg='white')
        heading.place(relx=0.4,rely=0.05,anchor=N)
            ######################################################

        def click_in_user(event):
            if self.logFrame.usernameEntry.get() == "Username":
                self.logFrame.usernameEntry.delete(0,'end')

        self.logFrame.usernameEntry = Entry(self.logFrame, width= 20,fg='black',border=0,font=("Microsoft Yahei UI Light",14))
        self.logFrame.usernameEntry.place(relx=0.4,rely=0.3,anchor=N)
        self.logFrame.usernameEntry.insert(0,'Username')
        Frame(self.logFrame,width=150,height=2,bg="black").place(relx=0.28,rely=0.39,anchor=N)
        self.logFrame.usernameEntry.bind("<FocusIn>"  ,click_in_user)

            ######################################################
        def click_in_pass(event):
            if self.logFrame.passwordEntry.get() == "Password":
                self.logFrame.passwordEntry.delete(0,'end')
            self.logFrame.passwordEntry.config(show="*")

        self.logFrame.passwordEntry = Entry(self.logFrame, width=20, fg='black', border=0, font=("Microsoft Yahei UI Light", 14))
        self.logFrame.passwordEntry.place(relx=0.4, rely=0.45, anchor=N)
        self.logFrame.passwordEntry.insert(0, 'Password')
        Frame(self.logFrame, width=150, height=2, bg="black").place(relx=0.28, rely=0.54, anchor=N)
        self.logFrame.passwordEntry.bind("<FocusIn>", click_in_pass)

            ######################################################
        self.logFrame.LoginButton = Button(self.logFrame,height=2,text="Login",fg='black',font=("Microsoft Yahei UI Bold",14),bg='lightblue',cursor='hand2', command= self.Login)
        self.logFrame.LoginButton.place(relx=0.6,rely=0.45,anchor=W)
        Label(self.logFrame,text="Don't have an account?",fg='black',bg='white',font=("Microsoft Yahei UI Light", 11)).place(relx=0.28,rely=0.7,anchor=N)
        self.logFrame.SignUpButton = Button(self.logFrame,width=6,text="Sign up",fg='#57a1f8',bg="white",font=("Microsoft Yahei UI Light", 11),border=0,cursor='hand2',command=self.SignUpGUI)
        self.logFrame.SignUpButton.place(relx=0.65,rely=0.695,anchor=N)

    def SignUpGUI(self):
        self.img = Image.open(r"Images\login.png")
        self.img = self.img.resize((400, 480))
        self.img = ImageTk.PhotoImage(self.img)
        Label(self, image=self.img, bg="white").place(x=0, y=0)

        self.signFrame = Frame(self, width=300, height=300, bg='white')
        self.signFrame.place(relx=0.5, rely=0.5, anchor=W)

        heading = Label(self.signFrame, text="SIGN UP", fg='#57a1f8', font=("Neuva Std Cond", 23, "bold"), bg='white')
        heading.place(relx=0.4, rely=0.05, anchor=N)

        ######################################################
        def click_in_user(event):
            if (self.signFrame.usernameEntry.get() == "Username"):
                self.signFrame.usernameEntry.delete(0, 'end')

        self.signFrame.usernameEntry = Entry(self.signFrame, width=20, fg='black', border=0, font=("Microsoft Yahei UI Light", 14))
        self.signFrame.usernameEntry.place(relx=0.4, rely=0.3, anchor=N)
        self.signFrame.usernameEntry.insert(0, 'Username')
        Frame(self.signFrame, width=150, height=2, bg="black").place(relx=0.28, rely=0.39, anchor=N)
        self.signFrame.usernameEntry.bind("<FocusIn>", click_in_user)

        ######################################################
        def click_in_pass(event):
            if (self.signFrame.passwordEntry.get() == "Password"):
                self.signFrame.passwordEntry.delete(0, 'end')
            self.signFrame.passwordEntry.config(show="*")

        self.signFrame.passwordEntry = Entry(self.signFrame, width=20, fg='black', border=0, font=("Microsoft Yahei UI Light", 14))
        self.signFrame.passwordEntry.place(relx=0.4, rely=0.45, anchor=N)
        self.signFrame.passwordEntry.insert(0, 'Password')
        Frame(self.signFrame, width=150, height=2, bg="black").place(relx=0.28, rely=0.54, anchor=N)
        self.signFrame.passwordEntry.bind("<FocusIn>", click_in_pass)

        ######################################################
        self.signFrame.SignUpButton = Button(self.signFrame, height=2, text="Sign Up", fg='black', font=("Microsoft Yahei UI Bold", 14), bg='lightblue',
               cursor='hand2', command=self.SignUp)
        self.signFrame.SignUpButton.place(relx=0.6, rely=0.45, anchor=W)
        Label(self.signFrame, text="Have an account?", fg='black', bg='white',
              font=("Microsoft Yahei UI Light", 11)).place(relx=0.28, rely=0.7, anchor=N)
        self.signFrame.LogInButton = Button(self.signFrame, width=6, text="Go login", fg='#57a1f8', bg="white", font=("Microsoft Yahei UI Light", 11),
               border=0, cursor='hand2',command=self.LogInGUI)
        self.signFrame.LogInButton.place(relx=0.65, rely=0.695, anchor=N)

    def openMenu(self, username):
        self.destroy()
        Menu(username).mainloop()

    def Login(self):
        username, password = (self.logFrame.usernameEntry.get(), self.logFrame.passwordEntry.get())
        try:
            # send login message
            client_socket.sendall(LOGIN.encode(FORMAT))
            buffer = logInAccount(username, password)

            if buffer == "tr":
                messagebox.showinfo("NOTIFICATION", "Login successfully!")
                self.openMenu(username)
            else:
                messagebox.showinfo("WARNING", "Username or password is not correct! Please try again [!]")
                self.LogInGUI()
        except Exception as e:
            messagebox.showinfo("ERROR", f"{e}")

    def SignUp(self):
        username, password = (self.signFrame.usernameEntry.get(), self.signFrame.passwordEntry.get())
        try:
            #send signup message
            client_socket.sendall(SIGNUP.encode(FORMAT))
            buffer = signUpAccount(username, password)
            if buffer == "tr":
                messagebox.showinfo("NOTIFICATION","Sign up successfully! Please login your account ^^")
                self.LogInGUI()
            else:
                messagebox.showinfo("WARNING","Sign up failed! Please try again!")
                self.SignUpGUI()
        except Exception as e:
            messagebox.showinfo("ERROR", f"{e}")

class Menu(tk.Tk):
    def __init__(self, username):
        super().__init__()

        self.title("A Transfer File Application")
        self.geometry("640x480")
        self.configure(bg="#fff")
        self.resizable(False,False)
        self.img = Image.open(r"Images\menu.jpeg")
        self.img = self.img.resize((640, 480))
        self.img = ImageTk.PhotoImage(self.img)
        self.label = Label(self, image = self.img, bg="white")
        self.label.place(x=0,y=0)

        #bool check working
        self.isWorking = False

        # BACKGROUND
        heading = Label(self.label, text=f"Hello, {username}", fg='#57a1f8', font=("Neuva Std Cond", 16, "bold"), bg='white')
        heading.place(relx=0.15, rely=0.02, anchor=N)
        # LOGOUT BUTTON
        self.logOutButton = Button(self, text="Log out", fg='black', bg="pink", font=("Microsoft Yahei UI Bold", 12),
            cursor='hand2', command=self.click_logout)
        self.logOutButton.place(relx=0.92, rely=0.02, anchor=N)

        #UPLOAD BUTTON
        self.upLabel = Label(self.label, text=f"UPLOAD", fg='#57a1f8', font=("Neuva Std Cond", 21, "bold"),
              bg='white', bd=3, relief='ridge')
        self.upLabel.place(relx = 0.15, rely = 0.7, anchor=S)


        #DOWNLOAD BUTTON
        self.downLabel = Label(self.label, text=f"DOWNLOAD", fg='#57a1f8', font=("Neuva Std Cond", 21, "bold"),
              bg='white', bd=3, relief='ridge', width=10)
        self.downLabel.place(relx=0.8, rely=0.7, anchor=S)

        #CLOSE APP
        self.closeButton = Button(self, text="QUIT", fg='green', bg="yellow", font=("Microsoft Yahei UI Bold", 14),
                                     cursor='hand2', bd=3, relief='ridge', width=6, command=self.closeConnectAsk)
        self.closeButton.place(relx=0.5, rely=0.9, anchor=CENTER)

        self.THREAD = []

        self.Bulletin()
        self.UploadGUI()
        self.DownloadGUI()

    def closeConnectAsk(self):
        if not self.isWorking:
            result = askyesno("CLOSE CONNECTION","Stop connecting to server?")
            if result:
                closeConnect()
                self.destroy()
        else:
            messagebox.showinfo("WARNING", "Application is still proccessing!")

    def Bulletin(self):
        self.bulletinFrame = Frame(self,width=600,height=200,bg='white', bd=5, relief="ridge")
        self.bulletinFrame.place(relx=0.5,rely=0.35,anchor=CENTER)
        self.bulletinFrame.img = Image.open(r"Images\frame.png")
        self.bulletinFrame.img = self.bulletinFrame.img.resize((590, 190))
        self.bulletinFrame.img = ImageTk.PhotoImage(self.bulletinFrame.img)
        self.bulletinFrame.label = Label(self, image=self.bulletinFrame.img, bg="white")
        self.bulletinFrame.label.place(relx=0.5, rely=0.35, anchor=CENTER)

    def UploadGUI(self):
        #UPLOAD FILE
        self.upFileButton = Button(self, text="FILE", fg='black', bg="pink", font=("Microsoft Yahei UI Bold", 11),
                                   cursor='hand2', bd=3, relief='ridge', command=self.uploadFileGUI)
        self.upFileButton.place(relx=0.09, rely=0.787, anchor=S)
        #UPLOAD FOLDER
        self.upFolderButton = Button(self, text="FOLDER", fg='black', bg="pink", font=("Microsoft Yahei UI Bold", 11),
                                     cursor='hand2', bd=3, relief='ridge', command=self.uploadFolderGUI)
        self.upFolderButton.place(relx=0.19, rely=0.787, anchor=S)


    def DownloadGUI(self):

        self.downFileButton = Button(self, text="FILE", fg='black', bg="pink", font=("Microsoft Yahei UI Bold", 11),
               cursor='hand2', bd=3, relief='ridge', width=6, command=self.downloadFileGUI)
        self.downFileButton.place(relx=0.72, rely=0.787, anchor=S)

        self.downFolderButton = Button(self, text="FOLDER", fg='black', bg="pink", font=("Microsoft Yahei UI Bold", 11),
               cursor='hand2', bd=3, relief='ridge', width = 9, command=self.click_down_folder)
        self.downFolderButton.place(relx=0.86, rely=0.787, anchor=S)
##################################################################################################################
#Hàm gửi yêu cầu upload file
    def uploadFileGUI(self):
        if not self.isWorking:
            # BULLETIN
            self.upload_screen = Toplevel(self)
            self.upload_screen.lift()
            self.upload_screen.focus_force()
            self.upload_screen.title("UPLOADING...")
            self.upload_screen.geometry("510x335")
            self.upload_screen.resizable(False, False)
            self.upload_screen.textConsole = scrolledtext.ScrolledText(self.upload_screen, wrap=tk.WORD, width=60, height=20)
            self.upload_screen.textConsole.place(relx=0.5, rely=0.5, anchor=CENTER)
            self.upload_screen.textConsole.config(state=tk.DISABLED)
            sys.stdout = writeConsole(self.upload_screen.textConsole)
            sys.stderr = writeConsole(self.upload_screen.textConsole)

            # SET FLAG
            self.isWorking = True
            try:
                client_socket.sendall("upload".encode(FORMAT))
                client_socket.recv(1)

                client_socket.sendall("file".encode(FORMAT))
                client_socket.recv(1)
                file_path = filedialog.askopenfilename().replace("/", "\\")
                if file_path:
                    client_socket.send('y'.encode(FORMAT))
                    client_socket.recv(1)
                    thr = threading.Thread(target=uploadFile, args=(client_socket,file_path))
                    thr.daemon = True
                    thr.start()

                    buffer = threading.Thread(target=self.isDoneUpload, args=(thr,))
                    buffer.daemon = True
                    buffer.start()
                else:
                    self.isWorking = False
                    client_socket.send("n".encode(FORMAT))
                    client_socket.recv(1)
            except Exception as e:
                messagebox.showinfo("ERROR", f"{e}")
        else:
            messagebox.showinfo("WARNING","Application is uploading or downloading! Please wait for it to complete!")

##################################################################################################################
    # Hàm gửi yêu cầu upload folder
    def uploadFolderGUI(self):
        if not self.isWorking:

            self.upload_screen = Toplevel(self)
            self.upload_screen.lift()
            self.upload_screen.focus_force()
            self.upload_screen.title("UPLOADING...")
            self.upload_screen.geometry("510x335")
            self.upload_screen.resizable(False, False)
            self.upload_screen.textConsole = scrolledtext.ScrolledText(self.upload_screen, wrap=tk.WORD, width=60, height=20)
            self.upload_screen.textConsole.place(relx=0.5, rely=0.5, anchor=CENTER)
            self.upload_screen.textConsole.config(state=tk.DISABLED)
            sys.stdout = writeConsole(self.upload_screen.textConsole)
            sys.stderr = writeConsole(self.upload_screen.textConsole)
            self.isWorking = True
            def on_close():
                try:
                    self.isWorking = False
                except Exception as e:
                    print(f"Error while sending cancellation message: {e}")
                self.upload_screen.destroy()

            self.upload_screen.protocol("WM_DELETE_WINDOW", on_close)
            try:
                #send upload message
                client_socket.sendall("upload".encode(FORMAT))
                client_socket.recv(1)

                client_socket.sendall("folder".encode(FORMAT))
                client_socket.recv(1)
                folder_path = filedialog.askdirectory().replace("/","\\")

                if folder_path:
                    option = 1 #input("Upload:\n#1 : By turn\n#2 : Parallel\nChoose: ")
                    client_socket.sendall(str(option).encode(FORMAT))
                    client_socket.recv(1)

                    thr = threading.Thread(target=uploadFolderSyn, args=(folder_path,))
                    thr.daemon = True
                    thr.start()

                    buffer = threading.Thread(target=self.isDoneUpload, args=(thr,))
                    buffer.daemon = True
                    buffer.start()
                else:
                    self.isWorking = False
                    client_socket.send("n".encode(FORMAT))
                    client_socket.recv(1)
            except Exception as e:
                messagebox.showinfo("ERROR", f"{e}")
        else:
            messagebox.showinfo("WARNING","Application is uploading or downloading! Please wait for it to complete!")

##################################################################################################################
    # Hàm gửi yêu cầu download file
    def downloadFileGUI(self):
        if not self.isWorking:
            download_screen = Toplevel(self)
            download_screen.lift()
            download_screen.focus_force()
            download_screen.title("DOWNLOADING...")
            download_screen.geometry("510x335")
            download_screen.resizable(False, False)
            download_screen.textConsole = scrolledtext.ScrolledText(download_screen, wrap=tk.WORD, width=60,
                                                                       height=15)
            download_screen.textConsole.place(relx=0.5, rely=0.4, anchor=CENTER)
            download_screen.textConsole.config(state=tk.DISABLED)
            sys.stdout = writeConsole(download_screen.textConsole)
            sys.stderr = writeConsole(download_screen.textConsole)

            download_screen.optionEntry = Entry(download_screen, width=20, fg='black', border=0,
                                                font=("Microsoft Yahei UI Bold", 11))
            download_screen.optionEntry.insert(0, "Input file index here")
            download_screen.optionEntry.place(relx=0.5, rely=0.85, anchor=CENTER)

            def on_click(event):
                if download_screen.optionEntry.get() == "Input file index here":
                    download_screen.optionEntry.delete(0, "end")

            download_screen.optionEntry.bind("<FocusIn>", on_click)

            try:
                #send download message
                client_socket.sendall("download".encode(FORMAT))
                client_socket.recv(1)

                self.file_list = getFileListOnServer()
                for i in range(len(self.file_list)):
                    print(f"{i}.{self.file_list[i]}")

                def downloadFileWithIndex():
                    file_index = int(download_screen.optionEntry.get())
                    #set flag for no bug
                    if 0 <= int(file_index) < len(self.file_list):
                        client_socket.send("y".encode(FORMAT))
                        client_socket.recv(1)

                        download_screen.optionEntry.destroy()
                        download_screen.optionButton.destroy()
                        thr = threading.Thread(target = downloadFile, args=(self.file_list[file_index],))
                        thr.daemon = True
                        thr.start()

                        buffer = threading.Thread(target=self.isDoneDownload, args=(thr,))
                        buffer.daemon = True
                        buffer.start()

                    else:
                        client_socket.send("n".encode(FORMAT))
                        client_socket.recv(1)
                        messagebox.showinfo("WARNING", "Invalid file!")

                download_screen.optionButton = Button(download_screen, text="Choose", fg='black', bg="pink",
                                                           font=("Microsoft Yahei UI Bold", 9),
                                                           cursor='hand2', bd=3, relief='ridge', command=downloadFileWithIndex)

                download_screen.optionButton.place(relx=0.5, rely=0.95, anchor=CENTER)

            except Exception as e:
                messagebox.showinfo("ERROR", f"{e}")
        else:
            messagebox.showinfo("WARNING", "Application is uploading or downloading! Please wait for it to complete!")

##################################################################################################################

    def click_logout(self):
        if not self.isWorking:
            ask = messagebox.askyesno("LOG OUT","Change account?")
            if ask:
                client_socket.sendall("logout".encode(FORMAT))
                client_socket.recv(1)
                self.destroy()
                sys.stdout = org_stdout
                sys.stderr = org_stderr
                LoginAndSignUp().mainloop()
        else:
            messagebox.showinfo("WARNING","Process is still running!")

    def click_down_folder(self):
        messagebox.showinfo("WARNING", "Chức năng đang được phát triển ^^ Hãy quay lại sau!")

    def isDoneUpload(self, thread):
        while True:
            if not thread.is_alive():
                self.isWorking = False
                messagebox.showinfo("NOTIFICATION", "Upload process complete!")
                break


    def isDoneDownload(self, thread):
        while True:
            if not thread.is_alive():
                self.isWorking = False
                messagebox.showinfo("NOTIFICATION", "Download process complete!")
                break


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

def main():
    app = LoginAndSignUp()
    app.mainloop()

if __name__ == "__main__":
    main()