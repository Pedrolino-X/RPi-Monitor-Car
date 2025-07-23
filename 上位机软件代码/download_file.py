import paramiko
from scp import SCPClient

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
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    try:
        ssh_client.connect(host, port, username, password)
        scpclient = SCPClient(ssh_client.get_transport(), socket_timeout=15.0)
        scpclient.get(remote_file_path, local_file_path)
        print("文件下载成功")
    except Exception as e:
        print(f"下载文件失败: {e}")
    finally:
        ssh_client.close()

# 示例使用
host = "192.168.137.24"  # 服务器IP地址
port = 22  # 端口号
username = "qiu"  # SSH用户名
password = "20040615"  # 密码
remote_file_path = "/home/qiu/Desktop/New/sxt.py"
local_file_path = "C:\\VirtualMachineShared\\sxt.py"

download_file(remote_file_path, local_file_path, host, port, username, password)
