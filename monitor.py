import subprocess  
import smtplib  
from email.message import EmailMessage  
import sys  
import os  
import mail
import env
import time

# 配置区  
PROCESS_LIST = "/home/wanghaoxiao/shy/daemon/process_name.txt"

def load_process_list(path):  
    if not os.path.isfile(path):  
        print(f"[ERROR] 进程列表文件不存在: {path}", file=sys.stderr)  
        sys.exit(1)  
    procs = []  
    with open(path, encoding="utf-8") as f:  
        for line in f:  
            s = line.strip()  
            if not s or s.startswith("#"):  
                continue  
            procs.append(s)  
    return procs  

def is_running(pattern):  
    # 等同于 pgrep -f pattern  
    res = subprocess.run(  
        ["pgrep", "-f", pattern],  
        stdout=subprocess.DEVNULL,  
        stderr=subprocess.DEVNULL  
    )  
    return res.returncode == 0  

def add_exclude_list(missing_list):
    with open(f"{os.path.dirname(PROCESS_LIST)}/exclude_list.txt", "a") as f:
        for p in missing_list:
            f.write(p + "\n")
        

def send_alert(missing):  
    detail_server_information = subprocess.check_output(["uname", "-a"]).decode("utf-8")
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    body = "检测到以下关键进程未在服务器上运行，请及时查看：\n\n" + "\n".join(missing)  
    body += "\n\n服务器信息：\n\n" + detail_server_information
    body += "\n\n当前时间：\n\n" + time_str
    mail.send_email(
        "⚠️  进程意外终止警告", 
        body, 
        env.FROM_MAIL_ADDR,
        env.TO_MAIL_ADDR,
        env.STMP_SERVER,
        env.FROM_MAIL_PASSWORD
    )
    add_exclude_list(missing)
    print(f"[INFO] 已发送告警邮件：{missing}")  

def main():  
    if not os.path.isfile(f"{os.path.dirname(PROCESS_LIST)}/exclude_list.txt"):
        with open(f"{os.path.dirname(PROCESS_LIST)}/exclude_list.txt", "w") as f:
            f.write("")
    with open(f"{os.path.dirname(PROCESS_LIST)}/exclude_list.txt", "r") as f:
        exclude_list = f.read().split("\n")
    
    procs = load_process_list(PROCESS_LIST)
    missing = []
    for p in procs:  
        if is_running(p):  
            continue
        else:
            missing.append(p)
    missing = [p for p in missing if p not in exclude_list]

    if missing:
        send_alert(missing)  
    else:  
        print(f"[INFO {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] 所有进程均在运行。")  

if __name__ == "__main__":  
    main()