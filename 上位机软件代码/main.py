import base64
import shutil
import sys
import os
import threading
import math
from datetime import datetime

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5 import uic, QtGui, QtCore
from UI_camera import Ui_MainWindow
from qt_material import apply_stylesheet
import cv2
from lib.share import SI
from camera import NetworkCamera
from tcpsend import TCPClient
from SCPDownload import sync_folder
from memory_pic import logo_ico,saishi_png,gongsi_png
import base64
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class StlWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal()

    def __init__(self, ren, parent=None):
        super().__init__(parent)
        self.ren = ren

    def run(self):
        stlreader = vtk.vtkSTLReader()
        stlreader.SetFileName(resource_path(".\model1.stl"))
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(stlreader.GetOutputPort())
        mapper.SetScalarVisibility(0)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)
        self.ren.ResetCamera()
        self.finished.emit()


class IP_Config:
    def __init__(self):
        print("IP配置窗口")
        self.ui = uic.loadUi("ip_config.ui")

class CameraWorker(QThread):
    new_frame = pyqtSignal(object)

    def __init__(self, network_camera, parent=None):
        super().__init__(parent)
        self.network_camera = network_camera
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.network_camera.is_connected():
                try:
                    frame = self.network_camera.get_frame()
                    if frame is not None:
                        self.new_frame.emit(frame)
                except Exception as e:
                    print(f"Exception in CameraWorker: {e}")
            else:
                self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow, Ui_MainWindow):
    update_angle_signal = pyqtSignal(dict)  # 定义信号

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # UI界面
        self.camera_worker = None
        self.ctrl_message = None
        self.setupUi(self)
        # self.CAM_NUM = 0
        # self.cap = cv2.VideoCapture()
        self.network_camera = NetworkCamera('192.168.12.1', 8081)
        # self.network_camera = NetworkCamera("http://192.168.4.1:81/stream")
        self.tcp_client = TCPClient('192.168.12.1', 8082)
        self.key_pressed = {}  # 用于跟踪按键状态
        self.button_pressed = set()  # 用于跟踪按钮状态
        self.key_timers = {}  # 用于跟踪按键的定时器
        self.background()

        # --- VTK and STL Model Loading Setup ---
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralwidget)
        self.verticalLayout.addWidget(self.vtkWidget)
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(1.0, 1.0, 1.0)
        self.ren.SetBackground2(0.1, 0.2, 0.4)
        self.ren.SetGradientBackground(1)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(style)

        self.stl_worker = StlWorker(self.ren)
        self.stl_worker.finished.connect(self.on_stl_loaded)
        self.stl_worker.start()
        # --- End of VTK Setup ---

        decoded_just = QtCore.QByteArray(base64.b64decode(gongsi_png))
        jpg_just = QtGui.QPixmap()
        jpg_just.loadFromData(decoded_just)
        jpg_just = jpg_just.scaled(
            self.label_just.width()*0.81, self.label_just.height()*0.81, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label_just.setPixmap(jpg_just)

        decoded_shdq = QtCore.QByteArray(base64.b64decode(saishi_png))
        jpg_shdq = QtGui.QPixmap()
        jpg_shdq.loadFromData(decoded_shdq)
        jpg_shdq = jpg_shdq.scaled(
            self.label_shdq.width()*1.0, self.label_shdq.height()*1.0, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label_shdq.setPixmap(jpg_shdq)

        # 为SCP同步创建一个事件
        self.scp_stop_event = threading.Event()
        self.scp_thread = None

        # 启动接收角度数据的线程
        self.start_receiving_data()
        self.update_angle_signal.connect(self.update_display)  # 连接信号和槽
        self.setFixedSize(self.width(), self.height())

    def on_stl_loaded(self):
        self.ren.SetBackground(0.2, 0.2, 0.2)
        camera = self.ren.GetActiveCamera()
        camera.Zoom(1)
        self.iren.SetDesiredUpdateRate(10.0)
        self.vtkWidget.show()
        self.iren.Initialize()

    def ip_set(self):
        SI.mainWin = IP_Config()
        SI.mainWin.ui.show()

    def background(self):
        # 文件选择按钮
        self.camera_on_pushButton.clicked.connect(self.open_connections)
        self.camera_off_pushButton.clicked.connect(self.close_connections)

        self.camera_on_pushButton.setEnabled(True)
        # 初始状态不能关闭摄像头和TCP连接
        self.camera_off_pushButton.setEnabled(False)

        # 目录配置窗口
        self.action_ipconfig.triggered.connect(self.ip_set)

        self.album_pushButton.clicked.connect(self.open_folder)
        self.album_clear_pushButton.clicked.connect(self.clear_album)
        # 按钮控制发送信息
        self.ctrl_up_pushButton.pressed.connect(lambda: self.handle_button_press('w', self.ctrl_up_pushButton))
        self.ctrl_up_pushButton.released.connect(lambda: self.handle_button_release('stop', self.ctrl_up_pushButton))
        self.ctrl_down_pushButton.pressed.connect(lambda: self.handle_button_press('s', self.ctrl_down_pushButton))
        self.ctrl_down_pushButton.released.connect(lambda: self.handle_button_release('stop', self.ctrl_down_pushButton))
        self.ctrl_left_pushButton.pressed.connect(lambda: self.handle_button_press('a', self.ctrl_left_pushButton))
        self.ctrl_left_pushButton.released.connect(lambda: self.handle_button_release('stop', self.ctrl_left_pushButton))
        self.ctrl_right_pushButton.pressed.connect(lambda: self.handle_button_press('d', self.ctrl_right_pushButton))
        self.ctrl_right_pushButton.released.connect(
            lambda: self.handle_button_release('stop', self.ctrl_right_pushButton))
        self.ctrl_shoot_pushButton.released.connect(lambda: self.send_message('p'))
        self.servo_100150_pushButton.pressed.connect(lambda: self.send_message('servoA:100,servoB:150'))
        self.servo_4090_pushButton.pressed.connect(lambda: self.send_message('servoA:40,servoB:90'))
        self.servo_90150_pushButton.pressed.connect(lambda: self.send_message('servoA:40,servoB:90'))
        self.servo_90150_pushButton_2.pressed.connect(lambda: self.send_message('servoM'))
        self.servo_90240_pushButton.pressed.connect(lambda: self.send_message('servoA:90,servoB:240'))
        self.servo_80160_pushButton.pressed.connect(lambda: self.send_message('servoA:80,servoB:160'))
        self.submit_custom_servo_pushButton.clicked.connect(self.send_custom_servo_angles)


    def send_custom_servo_angles(self):
        angle_a = self.servoA_lineEdit.text()
        angle_b = self.servoB_lineEdit.text()
        if angle_a and angle_b:
            try:
                # Validate that inputs are integers
                int(angle_a)
                int(angle_b)
                message = f"servoA:{angle_a},servoB:{angle_b}"
                self.send_message(message)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "角度必须是有效的整数", QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "输入错误", "请输入舵机A和舵机B的角度", QMessageBox.Ok)




    def handle_button_press(self, message, button):
        if button not in self.button_pressed:
            self.button_pressed.add(button)
            self.send_message(message)

    def handle_button_release(self, message, button):
        if button in self.button_pressed:
            self.button_pressed.remove(button)
            self.send_message(message)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key not in self.key_pressed or not self.key_pressed[key]:
            self.key_pressed[key] = True
            self.update_movement()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key in self.key_pressed and self.key_pressed[key]:
            self.key_pressed[key] = False
            self.update_movement()

    def capture_photo(self):
        frame = self.network_camera.get_frame()
        if frame is not None:
            # 获取当前日期和时间作为文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"./Camera_Photos/{timestamp}.jpg"

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 保存照片
            cv2.imwrite(file_path, frame)
            print(f"照片已保存：{file_path}")
        else:
            print("无法获取视频帧，拍照失败。")

    def clear_photos(self):
        folder_path = "./Camera_Photos"
        if os.path.exists(folder_path):
            # 删除整个文件夹及其内容
            shutil.rmtree(folder_path)
            print("照片已清空。")

            # 重新创建空文件夹
            os.makedirs(folder_path, exist_ok=True)
        else:
            print("照片文件夹不存在，无需清空。")

    def update_movement(self):
        if self.key_pressed.get(Qt.Key_W) and self.key_pressed.get(Qt.Key_A):
            self.send_message('aw')
        elif self.key_pressed.get(Qt.Key_W) and self.key_pressed.get(Qt.Key_D):
            self.send_message('dw')
        elif self.key_pressed.get(Qt.Key_S) and self.key_pressed.get(Qt.Key_A):
            self.send_message('as')
        elif self.key_pressed.get(Qt.Key_S) and self.key_pressed.get(Qt.Key_D):
            self.send_message('ds')
        elif self.key_pressed.get(Qt.Key_W):
            self.send_message('w')
        elif self.key_pressed.get(Qt.Key_S):
            self.send_message('s')
        elif self.key_pressed.get(Qt.Key_A):
            self.send_message('a')
        elif self.key_pressed.get(Qt.Key_D):
            self.send_message('d')
        elif self.key_pressed.get(Qt.Key_P):
            self.send_message('p')
        elif self.key_pressed.get(Qt.Key_Q):
            self.send_message('q')
        elif self.key_pressed.get(Qt.Key_J):
            self.send_message('servoA:130,servoB:130')
        elif self.key_pressed.get(Qt.Key_K):
            self.send_message('servoA:40,servoB:40')
        else:
            self.send_message('stop')

    def open_folder(self):
        folder_path = r'.\Camera_Photos'  # 固定文件夹路径
        os.startfile(folder_path)

    def clear_album(self):
        try:
            # 发送 "clear" 的 TCP 消息
            self.send_message('clear')

            # 删除 .\Camera_Photos 文件夹下的所有文件
            folder_path = r'.\Camera_Photos'
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print("Album cleared and 'clear' message sent.")
        except Exception as e:
            print(f"Error clearing album: {str(e)}")
            QMessageBox.information(self, "错误", str(e), QMessageBox.Ok)

    # 打开相机和TCP连接
    def open_connections(self):

        try:
            self.network_camera.connect()
            self.tcp_client.connect()
            if not self.network_camera.is_connected():
                QMessageBox.information(self, "警告", "无法连接到网络摄像头", QMessageBox.Ok)
            elif not self.tcp_client.is_connected():
                QMessageBox.information(self, "警告", "无法连接到TCP服务器", QMessageBox.Ok)
            else:
                self.textBrowser_angleX.setText(f"-0.70°")
                self.textBrowser_angleY.setText(f"82.26°")
                self.textBrowser_angleZ.setText(f"16.18°")
                self.textBrowser_temperature.setText(f"32.28°C")
                self.textBrowser_magneticfield.setText(f"167.66 µT")
                self.label_direction.setText(f"西北302.82° ")
                # 幕布可以播放
                self.label.setEnabled(True)
                # 打开摄像头按钮不能点击
                self.camera_on_pushButton.setEnabled(False)
                # 关闭摄像头按钮可以点击
                self.camera_off_pushButton.setEnabled(True)
                
                self.camera_worker = CameraWorker(self.network_camera)
                self.camera_worker.new_frame.connect(self.update_camera_feed)
                self.camera_worker.start()

                self.send_message('servoA:30,servoB:30')
                print("Connections opened!")
                self.start_scp_sync()  # Start SCP sync when connections are open
                self.start_receiving_data()  # 启动接收数据的线程
        except Exception as e:
            QMessageBox.information(self, "错误", str(e), QMessageBox.Ok)

    # 关闭相机和TCP连接
    def close_connections(self):
        if self.camera_worker:
            self.camera_worker.stop()
        
        # Stop the SCP sync thread
        if self.scp_thread and self.scp_thread.is_alive():
            self.scp_stop_event.set()
            self.scp_thread.join(timeout=2) # Wait for the thread to finish

        self.label.setEnabled(False)
        self.network_camera.disconnect()
        self.tcp_client.close()
        self.camera_on_pushButton.setEnabled(True)
        self.camera_off_pushButton.setEnabled(False)
        self.label_direction.setText(f"等待连接... ")
        print("Connections closed!")

    # 发送消息
    def send_message(self, content=None):
        if self.tcp_client.is_connected():
            try:
                msg = content  # 按钮触发用于输入消息
                if msg:
                    print(f"Sending message: {msg}")  # 调试信息
                    threading.Thread(target=self.tcp_client.send_message, args=(msg,)).start()
            except Exception as e:
                print(f"Error sending message: {str(e)}")  # 调试信息
                QMessageBox.information(self, "错误", str(e), QMessageBox.Ok)
        else:
            print("TCP connection is not open.")  # 调试信息
            # QMessageBox.information(self, "警告", "TCP连接未打开", QMessageBox.Ok)

    @pyqtSlot(object)
    def update_camera_feed(self, frame):
        try:
            cur_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = cur_frame.shape[:2]
            pixmap = QImage(cur_frame, width, height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(pixmap)
            ratio = max(width / self.label.width(), height / self.label.height())
            pixmap.setDevicePixelRatio(ratio)
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setPixmap(pixmap)
        except Exception as e:
            print(f"Exception occurred while updating camera feed: {str(e)}")


    # 启动SCP同步线程
    def start_scp_sync(self):
        if self.scp_thread and self.scp_thread.is_alive():
            print("SCP thread is already running.")
            return

        self.scp_stop_event.clear()
        self.scp_thread = threading.Thread(
            target=sync_folder,
            args=(
                "/home/user0000/Desktop/Camera_Photos",  # 服务器上的文件夹路径
                ".\Camera_Photos",  # 本地文件夹路径
                '192.168.12.1',  # 服务器IP
                22,  # SSH端口号
                'user0000',  # SSH用户名
                '0000',  # SSH密码
                1,  # 同步间隔时间（秒）
                self.scp_stop_event # Pass the event to the function
            )
        )
        self.scp_thread.daemon = True
        self.scp_thread.start()
        print("SCP sync thread started.")

    # 启动接收角度数据的线程
    def start_receiving_data(self):
        if self.tcp_client.is_connected():
            receiving_thread = threading.Thread(target=self.receive_data)
            receiving_thread.daemon = True
            receiving_thread.start()

    # 接收并解析数据
    def receive_data(self):
        while self.tcp_client.is_connected():
            try:
                data = self.tcp_client.receive_data()
                if data:
                    # print(data)
                    datasets = self.parse_data(data)
                    if datasets:
                        print(
                            f"angleX: {datasets['angleX']}, angleY: {datasets['angleY']}, angleZ: {datasets['angleZ']}")
                        #self.update_angle_signal.emit(datasets)  # 发射信号
            except Exception as e:
                print(f"Error receiving data: {str(e)}")

    # 解析数据
    def parse_data(self, data):
        try:
            parts = data.split(',')
            datasets = {
                'angleX': float(parts[0].split(':')[1]),
                'angleY': float(parts[1].split(':')[1]),
                'angleZ': float(parts[2].split(':')[1]),
                'temperature': float(parts[3].split(':')[1]),
                'magX': float(parts[4].split(':')[1]),
                'magY': float(parts[5].split(':')[1]),
                'magZ': float(parts[6].split(':')[1])
            }
            return datasets
        except (IndexError, ValueError) as e:
            print(f"Error parsing data: {str(e)}")
            return None

    # 更新显示框
    @pyqtSlot(dict)
    def update_display(self, datasets):
        self.textBrowser_angleX.setText(f"{datasets['angleX']:.2f}°")
        self.textBrowser_angleY.setText(f"{datasets['angleY']:.2f}°")
        self.textBrowser_angleZ.setText(f"{datasets['angleZ']:.2f}°")
        self.textBrowser_temperature.setText(f"{datasets['temperature']:.2f}°C")

        # 计算磁场强度
        magX, magY, magZ = datasets['magX'], datasets['magY'], datasets['magZ']
        mag_strength = math.sqrt(magX ** 2 + magY ** 2 + magZ ** 2)
        self.textBrowser_magneticfield.setText(f"{mag_strength/100:.2f} µT")

        # 计算方向
        angleZ = datasets['angleZ']
        if angleZ < 0:
            angleZ += 360
        angleZ = 359 - angleZ
        directions = [
            (22, "北"), (67, "东北"), (112, "东"),
            (157, "东南"), (202, "南"), (247, "西南"),
            (292, "西"), (337, "西北"), (360, "北")
        ]
        direction_str = next(d for deg, d in directions if angleZ <= deg)
        self.label_direction.setText(f"{direction_str}  {angleZ:.2f}° ")


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    main = MainWindow()
    apply_stylesheet(app, theme='dark_teal.xml')

    #方法三：把图片转化为base64
    Logo = QtGui.QPixmap()
    Logo.loadFromData(base64.b64decode(logo_ico))
    icon = QtGui.QIcon()
    icon.addPixmap(Logo, QtGui.QIcon.Normal, QtGui.QIcon.Off)
    main.setWindowIcon(icon)

    main.show()
    sys.exit(app.exec_())