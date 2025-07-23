import os
import paramiko
from scp import SCPClient
import time

def download_file(remote_file_path, local_file_path, host, port, username, password):
    """
    从Linux服务器下载文件到Windows客户端
    :param remote_file_path: 服务器上的文件路径
    :param local_file_path: 本地保存文件路径
    :param host: 服务器IP地址
    :param port: 服务器端口号
    :param username: SSH用户名
    :param password: SSH密码
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(host, port, username, password)
        scpclient = SCPClient(ssh_client.get_transport(), socket_timeout=15.0)
        scpclient.get(remote_file_path, local_file_path)
        print(f"文件下载成功: {local_file_path}")
    except Exception as e:
        print(f"下载文件失败: {e}")
    finally:
        ssh_client.close()

def sync_folder(remote_folder, local_folder, host, port, username, password, interval, stop_event):
    """
    同步文件夹
    :param remote_folder: 服务器上的文件夹路径
    :param local_folder: 本地文件夹路径
    :param host: 服务器IP地址
    :param port: 服务器端口号
    :param username: SSH用户名
    :param password: SSH密码
    :param interval: 同步间隔时间（秒）
    :param stop_event: 用于停止线程的 threading.Event
    """
    # 创建本地文件夹（如果不存在）
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    while not stop_event.is_set():
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(host, port, username, password, timeout=5)
            while not stop_event.is_set():
                try:
                    sftp = ssh_client.open_sftp()
                    # 列出远程文件夹中的文件
                    remote_files = sftp.listdir(remote_folder)
                    for file_name in remote_files:
                        if stop_event.is_set():
                            break
                        remote_file_path = os.path.join(remote_folder, file_name)
                        remote_file_path = remote_file_path.replace("\\", "/")
                        local_file_path = os.path.join(local_folder, file_name)  # Windows 风格路径
                        local_file_path = local_file_path.replace('/', '\\')

                        if not os.path.exists(local_file_path):
                            # print(f"下载新文件: {remote_file_path}")
                            download_file(remote_file_path, local_file_path, host, port, username, password)
                        # else:
                            # print(f"文件已存在: {local_file_path}")

                    # 关闭 SFTP 连接
                    sftp.close()
                except Exception as e:
                    print(f"同步文件夹失败: {e}")
                    break  # Inner loop break on error
                
                # Check stop event frequently
                if stop_event.wait(interval):
                    break
        except Exception as e:
            print(f"连接服务器失败: {e}")
        finally:
            if ssh_client.get_transport() and ssh_client.get_transport().is_active():
                ssh_client.close()
        
        if stop_event.is_set():
            break
        # Wait before retrying connection
        time.sleep(interval)
    print("SCP sync thread stopped.")

