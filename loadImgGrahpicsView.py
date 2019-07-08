'''一个大坑：opencv处理的图片都会将原图宽高反向；因此图片处理时应该进行相应变换以原图为基准进行变换'''

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from BigIMGOpen_move_zoom.tileItem import TileItem
from BigIMGOpen_move_zoom.pyrimgitem import PyrIMGItem
from BigIMGOpen_move_zoom.util import *
from BigIMGOpen_move_zoom.slide_helper import SlideHelper
from BigIMGOpen_move_zoom.img_from_rect import ImgFromRect

class LoadIMGraphicsView(QGraphicsView):
    '''装载大图片和金字塔压缩图的view'''
    scale_factor = 1.0  # 缩放因子，当scene放置的是大图时，将原始图像的scale_factor置为1；缩放时记录缩放因子

    def __init__(self, img_path, parent=None):
        super(LoadIMGraphicsView, self).__init__(parent)
        self.scene_pyr=QGraphicsScene()  #放置pyr的场景
        self.setBackgroundBrush(QColor(147,147,147))
        self.scene_big=QGraphicsScene()


        self.pyr_item = PyrIMGItem(img_path)  # 压缩金字塔item
        self.is_big = self.pyr_item.is_big  # 判定是否是大图片
        self.slide_helper = SlideHelper(img_path)  # 获取sldie对象
        self.scene_big.setSceneRect(0,0,self.slide_helper.slide_dimension[0],self.slide_helper.slide_dimension[1])
        self.cur_scene_img = True  # 当前场景图片，True表示放的是金字塔缩略图，False表示放的tilesgroup
        self.pyr_factor = self.pyr_item.pyr_factor  # 原图与金字塔图压缩比

        self.x_dimension_change=self.slide_helper.slide_dimension[0]/self.slide_helper.slide_dimension[1]   #表示opencv计算后导致改变的图片宽的维度伸缩比
        self.y_dimension_change=self.slide_helper.slide_dimension[1]/self.slide_helper.slide_dimension[0]

        self.scene_pyr.addItem(self.pyr_item)  # 初始化首先加载金字塔缩略图
        self.tile_items_group = self.get_tiles_group()    #装载原图itemgroup
        self.scene_big.addItem(self.tile_items_group)
        self.pyr_put_in_scene()


    def wheelEvent(self, event: QWheelEvent) -> None:
        """鼠标滑轮事件"""
        d_value = event.angleDelta().y() / 120
        d_value = -4 * d_value
        des_pos = self.mapToScene(event.pos())
        if self.is_big:     #若是大图片
            if event.modifiers() & Qt.ControlModifier:  # 按下ctrl键和滑动滚轮
                factor = 1.09 if d_value < 0 else 0.91
                if factor > 1:  # 放大操作
                    if self.cur_scene_img:  # 表示当前secen中为金字塔缩略图
                        self.tilesgroup_put_in_scene()  # 切换scene为对应坐标的原始大图片
                        self.cur_scene_img = False  # 表示当前scene中为原始大图片
                        # print(des_pos.x(),des_pos.y())
                        # print(self.pyr_factor)
                        self.centerOn(self.mapToScene(QPoint(des_pos.x()*self.pyr_factor * self.x_dimension_change,des_pos.y()*self.pyr_factor * self.y_dimension_change)))


                    else:
                        self.scale(factor, factor)
                        self.scale_factor = self.transform().m11()
                else:  # 缩小操作
                    if not self.cur_scene_img:  #若当前处于大图片场景
                        if factor * self.scale_factor <= 1:  # 表示将缩小到比原图还小,切换未金字塔总览图
                            self.scale_factor = 1.0
                            self.pyr_put_in_scene()  # 场景设置回金字塔缩略图
                            self.cur_scene_img = True
                        else:
                            self.scale(factor, factor)
                            self.scale_factor = self.transform().m11()

    def tilesgroup_put_in_scene(self):
        '''移除金字塔缩略图scene，将大图片的全部切片tiles加载到scene中'''
        self.setScene(self.scene_big)



    def pyr_put_in_scene(self):
        '''移除当前scene中的tiles_group,切换scene图片为金字塔缩略图'''
        self.setScene(self.scene_pyr)

    def get_tiles_group(self)->QGraphicsItemGroup:
        '''获得tiles_group对象'''
        tiles_group = QGraphicsItemGroup()
        tiles_rects = slice_rect(self.slide_helper.slide_dimension[0], self.slide_helper.slide_dimension[1], self.slide_helper.tile_size)
        downsample = self.slide_helper.slide.level_downsamples[0]
        for tile_rect in tiles_rects:  # 画出需要画出的所有tile
            item = TileItem(tile_rect, self.slide_helper, 0, downsample)
            item.moveBy(tile_rect[0], tile_rect[1])  # 移动到对应坐标
            tiles_group.addToGroup(item)
        return tiles_group
