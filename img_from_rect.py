from BigIMGOpen_move_zoom.loadImgGrahpicsView import *
import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from BigIMGOpen_move_zoom.slide_helper import SlideHelper
from matplotlib import pyplot as plt
from BigIMGOpen_move_zoom.util import *
import numpy as np
import cv2
class ImgFromRect:
    '''从指定rect区域中提取部分图片'''
    tile_size = 0

    def __init__(self, ori_rec: QRect, tile_size: int, slide_helper: SlideHelper):
        '''最终从根据rect获取到area_img'''
        self.tile_size = tile_size
        self.ori_rec = ori_rec          #传入的矩形框rec信息
        self.tiles_pilmap_group = []  # 放置区域所占据tile的图片
        self.slide_helper = slide_helper

        self.joint_img = None  # 保存tiles_pilmap_group中拼接的图片
        # 调用本类主要希望获得的成员
        self.area_img = None    #最终赋值为目标区域的numpy数组

        self.r_tile_width = slide_helper.slide_dimension[0] % tile_size  # 图像中最右边tile的宽度
        self.b_tile_height = slide_helper.slide_dimension[1] % tile_size  # 图像中最下边tile的宽度
        self.r_tile_xcoor = slide_helper.slide_dimension[0] - self.r_tile_width  # 最右边tile的横坐标
        self.b_tile_ycoor = slide_helper.slide_dimension[1] - self.b_tile_height  # 最下边tile的纵坐标

        self.get_tiles_pixmap()
        self.joint_tiles_to_img()
        self.get_area_img()

    def get_tiles_pixmap(self):
        '''获取在原大图中哪些tiles被包含在区域内，并将这些tile放到tiles_group中'''
        l_t_tile = [0, 0]  # 初始化左上角tile
        row_n = self.ori_rec.x() // self.tile_size  # 获得所涉及到的左上角tile横向是第几个tile
        l_t_tile[0] = row_n * self.tile_size
        col_n = self.ori_rec.y() // self.tile_size  # 获得所涉及的左上角tile列向是第几个tile
        l_t_tile[1] = col_n * self.tile_size
        '''左上角tile获取成功'''
        r_t_tile = [0, 0]
        row_n = (self.ori_rec.x() + self.ori_rec.width()) // self.tile_size  # 获得所涉及到的右上角tile横向是第几个tile
        r_t_tile[0] = row_n * self.tile_size
        r_t_tile[1] = l_t_tile[1]
        '''右上角tile获取成功'''
        n_tile_x = (r_t_tile[0] - l_t_tile[0]) // self.tile_size + 1  # 横向占据多少个tile
        '''横轴上占据到的tile数量获取成功'''

        l_b_tile = [0, 0]
        col_n = (self.ori_rec.y() + self.ori_rec.height()) // self.tile_size  # 获得所涉及的左上角tile列向是第几个tile
        l_b_tile[0] = l_t_tile[0]
        l_b_tile[1] = col_n * self.tile_size  # 获得左下角tile坐标
        '''左下角tile坐标获得成功'''
        n_tile_y = (l_b_tile[1] - l_t_tile[1]) // self.tile_size + 1
        '''y轴上tile个数获取成功'''

        cur_tile = l_t_tile.copy()  # 防止深拷贝
        for i in range(n_tile_y):  # 获取所占据的tile的pixmap，放到tiles_pixmap_group中
            x_pilmap_group = []  # 获取每一行的tile_img
            cur_tile[0] = l_t_tile[0]
            for j in range(n_tile_x):
                pilimg_rec = [cur_tile[0], cur_tile[1], 0, 0]

                '''对于要取图片的tile，先判断该tile所在坐标是否处于最右端'''
                if cur_tile[0] == self.r_tile_xcoor:  # 该tile处于最右边
                    pilimg_rec[2] = self.r_tile_width
                else:
                    pilimg_rec[2] = self.tile_size

                '''对于要取图片的tile，先判断该tile所在坐标是否处于最底部'''
                if cur_tile[1] == self.b_tile_ycoor:  # 该tile处于最底部
                    pilimg_rec[3] = self.b_tile_height
                else:
                    pilimg_rec[3] = self.tile_size

                # 从slide对象中获取tile图像
                pilimg = self.slide_helper.read_region_from_big(pilimg_rec[0], pilimg_rec[1], 0,
                                                                (pilimg_rec[2], pilimg_rec[3]))
                x_pilmap_group.append(pilimg)
                cur_tile[0] += self.tile_size
            cur_tile[1] += self.tile_size
            self.tiles_pilmap_group.append(x_pilmap_group)
        '''成功获取所占据tile区域的pixmap图片，并放到了tiles_pixmap_group中'''

    def joint_tiles_to_img(self):
        '''将tiles_pilmap_group中图片进行拼接,赋给joint_img'''
        # 先将同一横坐标的pil image进行拼接
        hori_joint_img_group = []
        for item in self.tiles_pilmap_group:
            if len(item) == 1:  # 若横向方向本来就只有一张图片，不做拼接
                hori_joint_img_group.append(item[0])
            else:  # 有两张以上，进行拼接
                joint_img = item[0]
                for i in range(len(item) - 1):
                    joint_img = joint_two_image(joint_img, item[i + 1], 'horizontal')
                hori_joint_img_group.append(joint_img)
        '''将横向拼接好的图片进行纵向拼接'''
        final_img = hori_joint_img_group[0]
        if len(hori_joint_img_group) == 1:
            self.joint_img=final_img
        else:
            for i in range(len(hori_joint_img_group)-1):
                final_img = joint_two_image(final_img, hori_joint_img_group[i+1], 'vertical')
            self.joint_img=final_img

    def get_area_img(self):
        '''从拼接图中获取目标rect区域中部分图片，赋给area_img'''
        #1.将原始矩形框转换为要截取部分的crop
        crop=[0,0,0,0]  #在拼接好的图像中要截取的区域，其中前俩参数为左上角坐标，后俩为右下角坐标
        crop[0]=self.ori_rec.x()%self.tile_size
        crop[1]=self.ori_rec.y()%self.tile_size
        crop[2]=crop[0]+self.ori_rec.width()
        crop[3]=crop[1]+self.ori_rec.height()

        #2.传入crop截取目标区域像素到area_img
        self.area_img=self.joint_img.crop(crop)     #.crop()是传入一个左上角和右下角左边，将这俩坐标围成的矩形区域图像截取出来
        self.area_img=np.array(self.area_img)


if __name__ == '__main__':
    slide_he = SlideHelper('Level_17.tif')
    i = ImgFromRect(QRect(20662, 15900, 2000, 2000), tile_size=1000, slide_helper=slide_he)
    cv2.imshow('sd',i.area_img)
    cv2.waitKey(0)