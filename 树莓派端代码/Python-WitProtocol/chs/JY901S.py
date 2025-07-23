# coding: UTF-8

import time
import datetime
import platform
import struct
import lib.device_model as deviceModel
from lib.data_processor.roles.jy901s_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.wit_protocol_resolver import WitProtocolResolver

class Gyroscope:
    def __init__(self, port="/dev/ttyAMA0", baud=9600):
    # def __init__(self, port='/dev/serial0', baudrate=9600):
        self.device = deviceModel.DeviceModel(
            "我的JY901",
            WitProtocolResolver(),
            JY901SDataProcessor(),
            "51_0"
        )
        self.device.serialConfig.portName = port
        self.device.serialConfig.baud = baud
        self.device.dataProcessor.onVarChanged.append(self.on_update)
        self._writeF = None
        self._is_writeF = False
        self.datasets = {"angleX": 0, "angleY": 0, "angleZ": 0, "temperature": 0, "magX": 0, "magY": 0, "magZ": 0}
        
    def open_device(self):
        self.device.openDevice()

    def close_device(self):
        self.device.closeDevice()

    def read_config(self):
        tVals = self.device.readReg(0x02, 3)
        print("返回结果：" + str(tVals) if tVals else "无返回")
        tVals = self.device.readReg(0x23, 2)
        # print("返回结果：" + str(tVals) if tVals else "无返回")

    def set_config(self):
        self.device.unlock()
        time.sleep(0.1)
        self.device.writeReg(0x03, 6)
        time.sleep(0.1)
        self.device.writeReg(0x23, 0)
        time.sleep(0.1)
        self.device.writeReg(0x24, 0)
        time.sleep(0.1)
        self.device.save()

    def acceleration_calibration(self):
        self.device.AccelerationCalibration()
        print("加计校准结束")

    def field_calibration(self):
        self.device.BeginFiledCalibration()
        if input("请分别绕XYZ轴慢速转动一圈，三轴转圈完成后，结束校准（Y/N)？").lower() == "y":
            self.device.EndFiledCalibration()
            print("结束磁场校准")

    def on_update(self, deviceModel):
        self.datasets["angleX"] = deviceModel.getDeviceData("angleX")
        self.datasets["angleY"] = deviceModel.getDeviceData("angleY")
        self.datasets["angleZ"] = deviceModel.getDeviceData("angleZ")
        self.datasets["temperature"] = deviceModel.getDeviceData("temperature")
        self.datasets["magX"] = deviceModel.getDeviceData("magX")
        self.datasets["magY"] = deviceModel.getDeviceData("magY")
        self.datasets["magZ"] = deviceModel.getDeviceData("magZ")        

        if self._is_writeF:
            Tempstr = " " + str(deviceModel.getDeviceData("Chiptime"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("accX")) + "\t" + str(deviceModel.getDeviceData("accY")) + "\t" + str(deviceModel.getDeviceData("accZ"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("gyroX")) + "\t" + str(deviceModel.getDeviceData("gyroY")) + "\t" + str(deviceModel.getDeviceData("gyroZ"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("angleX")) + "\t" + str(deviceModel.getDeviceData("angleY")) + "\t" + str(deviceModel.getDeviceData("angleZ"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("temperature"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("magX")) + "\t" + str(deviceModel.getDeviceData("magY")) + "\t" + str(deviceModel.getDeviceData("magZ"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("lon")) + "\t" + str(deviceModel.getDeviceData("lat"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("Yaw")) + "\t" + str(deviceModel.getDeviceData("Speed"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("q1")) + "\t" + str(deviceModel.getDeviceData("q2"))
            Tempstr += "\t" + str(deviceModel.getDeviceData("q3")) + "\t" + str(deviceModel.getDeviceData("q4"))
            Tempstr += "\r\n"
            self._writeF.write(Tempstr)

    def start_record(self):
        self._writeF = open(str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + ".txt", "w")
        self._is_writeF = True
        header = "Chiptime\tax(g)\tay(g)\taz(g)\twx(deg/s)\twy(deg/s)\twz(deg/s)\tAngleX(deg)\tAngleY(deg)\tAngleZ(deg)\tT(°)\tmagx\tmagy\tmagz\tlon\tlat\tYaw\tSpeed\tq1\tq2\tq3\tq4\r\n"
        self._writeF.write(header)
        print("开始记录数据")

    def end_record(self):
        self._is_writeF = False
        self._writeF.close()
        print("结束记录数据")

    def get_datasets(self):
        return self.datasets

# Example usage:
if __name__ == "__main__":
    gyro = Gyroscope()
    gyro.open_device()
    gyro.read_config()
    gyro.start_record()
    input("Press Enter to stop...")
    gyro.end_record()
    gyro.close_device()
    print(gyro.get_datasets())

