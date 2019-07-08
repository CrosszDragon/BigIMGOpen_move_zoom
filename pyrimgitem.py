import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PyrIMGItem(QGraphicsItem):
    '''继承与QGraphicItem
    提供将路径图片压缩为适合屏幕分辨率的总览小图，并且将该小图放到item中
    '''
    def __init__(self, img_path):
        super(PyrIMGItem, self).__init__()
        self.img_path = img_path
        self.is_big = False  # 用于判定是否是大图片,默认为否
        self.pyr_factor=1.0    #表示pyr图片相对于原图的压缩因子，1.0表示未压缩
        self.img_shape=None
        self.pyr_img = self.pyr_image()

    def pyr_image(self):
        img = cv2.imread(self.img_path)
        self.img_shape=img.shape
        self.ori_img_w=self.img_shape[1]

        while len(img) > 2000 or len(img[0]) > 2000:
            self.is_big = True  # 表明是大图片
            '''当图片像素大于2000*2000时，属于大图片，进行金字塔压缩'''
            img = cv2.pyrDown(img)
        self.pyr_factor=self.ori_img_w/(img.shape[1])    #获得原图与压缩图比
        return img

    def boundingRect(self):
        return QRectF(0, 0, len(self.pyr_img), len(self.pyr_img[0]))

    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: QWidget = ...):
        img = cv2.resize(src=self.pyr_img, dsize=None, fx=0.2, fy=0.2)
        img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img3 = QImage(img2[:], img2.shape[1], img2.shape[0], img2.shape[1] * 3, QImage.Format_RGB888)  # item可用格式
        self._image=QPixmap.fromImage(img3)
        QPixmapCache.insert('pyr_img',self._image)
        painter.drawPixmap(self.boundingRect().toRect(),self._image)

