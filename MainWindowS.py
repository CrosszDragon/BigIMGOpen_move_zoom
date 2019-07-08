import openslide
from openslide.deepzoom import DeepZoomGenerator
from BigIMGOpen_move_zoom.loadImgGrahpicsView import LoadIMGraphicsView
from PyQt5.QtWidgets import *
import sys

class Mywindow(QMainWindow):
    def __init__(self):
        super(Mywindow,self).__init__()
        view=LoadIMGraphicsView('Level_17.tif')
        self.setCentralWidget(view)

if __name__ == '__main__':
    app=QApplication(sys.argv)
    win=Mywindow()
    win.show()
    sys.exit(app.exec_())