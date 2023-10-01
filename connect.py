### connection between frontend and backend
import sys
import numpy as np

import cv2
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic



class MAINAPP(QMainWindow):
    def __init__(self):
        super(MAINAPP, self).__init__()

        uic.loadUi("signatureui.ui", self)

        self.logic = 0
        self.value = 1
        self.SHOW.clicked.connect(self.onClicked)
        self.TEXT.setText("Press 'Show' to connect with webcam.")
        self.CHECK.clicked.connect(self.CaptureClicked)

    @pyqtSlot()
    def onClicked(self):
        self.TEXT.setText('Press "Check" to Scan image')
        cap = cv2.VideoCapture(0)
        # while (True):
        # print(cap.read())
        while (cap.isOpened()):
            ret, frame = cap.read()

            if ret == True:
                print('here')
                self.displayImage(frame, 1)
                cv2.waitKey()
                if (self.logic == 2):
                    self.value = self.value + 1
                    cv2.imwrite('/images/%s.png' % (self.value), frame)
                    self.logic = 1
                    self.TEXT.setText('your Image have been Saved')
            else:
                print('not found')
        cap.release()
        cv2.destroyAllWindows()

    def CaptureClicked(self):
        self.logic = 2

    def displayImage(self, img, window=1):
        qformat = QImage.Format_Indexed8
        if len(img.shape) == 3:
            if (img.shape[2]) == 4:
                qformat = QImage.Format_RGBA888
            else:
                qformat = QImage.Format_RGB888
        img = QImage(img, img.shape[1], img.shape[0], qformat)
        img = img.rgbSwapped()
        self.imglabel.setPixmap(QPixmap.fromImage(img))
        self.imglabel.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)


app = QApplication(sys.argv)
window = MAINAPP()
window.show()
try:
    sys.exit(app.exec_())
except:
    print('exiting')
