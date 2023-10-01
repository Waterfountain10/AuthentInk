import sys
import numpy as np
import cv2
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QComboBox, QTextBrowser
from PyQt5.QtGui import QImage, QPixmap
import torch
from datatraining import SiameseNetwork
import torchvision.transforms as transforms
from PIL import Image
from torch.nn import functional as F

from better_signature import Ui_MainWindow  # Assuming bettersignature.py is in the same directory

class SignatureChecker(QMainWindow, Ui_MainWindow):
    
    def __init__(self):
        super(SignatureChecker, self).__init__()
        self.setupUi(self)

        # Connect the buttons to their corresponding methods
        self.SHOW.clicked.connect(self.showWebcam)
        self.CHECK.clicked.connect(self.checkSignature)
        
        # Initialize the QComboBox with your IDs
        for i in range(49, 70):  # Including 69
            self.idSelector.addItem(str(i))
            self.idSelector.activated.connect(self.current_text)

        # OpenCV initializations
        self.cap = None
        self.currentFrame = None
    
    
        
    def current_text(self):
        ctext = str(self.idSelector.currentText())
        return ctext


    def comparison(self, image1_path, image2_path):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = SiameseNetwork().to(device)
        model.load_state_dict(torch.load("model.pt"))
        model.eval()  # Set the model to evaluation mode (important for inference)

        # Load and preprocess the images
        transform = transforms.Compose([transforms.Resize((100, 100)), transforms.ToTensor()])
        img1 = Image.open(image1_path).convert('L')
        img2 = Image.open(image2_path).convert('L')
        img1 = transform(img1).to(device)
        img2 = transform(img2).to(device)
        # Forward pass to get the embeddings for the images

        with torch.no_grad():
            output1, output2 = model(img1.unsqueeze(0), img2.unsqueeze(0))
        # Calculate the similarity score
        
        similarity_score = F.pairwise_distance(output1, output2)
        return similarity_score
    
    
    def showWebcam(self):
        if not self.cap:
            self.cap = cv2.VideoCapture(0)
            timer = QtCore.QTimer(self)
            timer.timeout.connect(self.updateFrame)
            timer.start(5)

    def updateFrame(self):
        ret, self.currentFrame = self.cap.read()
        if ret:
            self.displayImage(self.currentFrame, self.imglabel)

    
    def checkSignature(self):

        if self.currentFrame is not None:
            cv2.imwrite('captured_image.png', self.currentFrame)
            
            pixmap = QtGui.QPixmap('captured_image.png')
            self.captured_img.setPixmap(pixmap.scaled(self.captured_img.width(), self.captured_img.height(), QtCore.Qt.KeepAspectRatio))
            self.captured_img.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            

        img_2_path = self.current_text()
        camera_image = 'captured_image.png'
        original_image = f'signature-verification-dataset/sign_data/test/0{str(img_2_path)}/01_0{str(img_2_path)}.png'
        
        #display top image of selected signature
        pixmap = QtGui.QPixmap(original_image)
        self.test_img.setPixmap(pixmap.scaled(self.test_img.width(), self.test_img.height(), QtCore.Qt.KeepAspectRatio))
        self.test_img.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        similarity = self.comparison(camera_image, original_image)
        if 0.6 < similarity <= 1:
           self.TEXT.setPlainText("FRAUD!")
        elif 0.5 < similarity <= 0.6:
           self.TEXT.setPlainText("Probably Fraud")
        elif 0.4 < similarity <= 0.5:
            self.TEXT.setPlainText("Inconclusive, please retry")
        elif 0.25 < similarity <= 0.4:
           self.TEXT.setPlainText("Probably Genuine")
        elif 0 < similarity <= 0.25:
           self.TEXT.setPlainText("GENUINE!")
    


    def displayImage(self, img, label):
        qformat = QImage.Format_RGB888
        img = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        img = img.rgbSwapped()
        label.setPixmap(QPixmap.fromImage(img))
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SignatureChecker()
    window.show()
    sys.exit(app.exec_())
