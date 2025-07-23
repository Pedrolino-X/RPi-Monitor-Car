import sys
sys.path.append('/home/user0000/Desktop/server/Python-WitProtocol/chs')
from JY901S import Gyroscope

def get_gyro_data():
    gyro = Gyroscope()
    datasets = gyro.get_datasets()
    return f"angleX:{datasets['angleX']},angleY:{datasets['angleY']},angleZ:{datasets['angleZ']},temperature:{datasets['temperature']},magX:{datasets['magX']},magY:{datasets['magY']},magZ:{datasets['magZ']}"
