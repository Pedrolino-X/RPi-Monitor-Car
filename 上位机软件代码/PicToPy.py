import base64


def pictopy(picture_names, py_name):
    """
    将图像文件转换为py文件
    :param picture_name:
    :return:
    """
    write_data = []
    for picture_name in picture_names:
        filename = picture_name.replace('.', '_')
        open_pic = open("%s" % picture_name, 'rb')
        b64str = base64.b64encode(open_pic.read())
        open_pic.close()
        # 注意这边b64str一定要加上.decode()
        write_data.append('%s = "%s"\n' % (filename, b64str.decode()))

    f = open('%s.py' % py_name, 'w+')
    for data in write_data:
        f.write(data)
    f.close()


# pics = ["logo_2.png", "logo.ico"] 中的图片存放在PicToPy.py同一目录中，运行完成后，
# 会在当前路径看到一个memory_pic.py文件
pics = [r'./images/gongsi.png', r'./images/saishi.png', r'./images/logo.ico']
pictopy(pics, 'memory_pic')  # 将pics里面的图片写到 memory_pic.py 中
print("ok")