import numpy as np
import pandas as pd
import os

import torchvision
import torchvision.datasets as dset
import torchvision.transforms as transforms
from torch.utils.data import DataLoader,Dataset
import matplotlib.pyplot as plt
import torchvision.utils
import random
from PIL import Image
import torch
from torch.autograd import Variable
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
import glob

class SiameseNetwork(nn.Module):

    def __init__(self):
        super(SiameseNetwork, self).__init__()


        self.conv1=nn.Conv2d(1,50,kernel_size=5)
        self.pool1 = nn.MaxPool2d(kernel_size = 2, stride = 2, padding = 0)

        self.conv2 = nn.Conv2d(50,60, kernel_size = 5)
        self.pool2 = nn.MaxPool2d(kernel_size = 2, stride = 2, padding = 0)

        self.conv3 = nn.Conv2d(60, 80,  kernel_size = 3)

        self.batch_norm1 = nn.BatchNorm2d(50)
        self.batch_norm2 = nn.BatchNorm2d(60)

        self.fc1 = nn.Linear(32000, 128)
        self.fc2 = nn.Linear(128, 2)

    def forward1(self,x):
        x=self.conv1(x)
        x = self.batch_norm1(x)
        x=F.relu(x)
        x=self.pool1(x)

        x=self.conv2(x)
        x = self.batch_norm2(x)
        x=F.relu(x)
        x=self.pool2(x)

        x=self.conv3(x)
        x=F.relu(x)
        x = x.view(x.size()[0], -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)

        return x

    def forward(self, input1, input2):

        output1 = self.forward1(input1)
        output2 = self.forward1(input2)

        return output1, output2

class ContrastiveLoss(torch.nn.Module):

    def __init__(self, margin=1.5):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        euclidean_distance = F.pairwise_distance(output1, output2)
        loss_contrastive = torch.mean((1-label) * torch.pow(euclidean_distance, 2) +
                                    (label) * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2))


        return loss_contrastive

class Sign_Data(Dataset):
    def __init__(self,train_dir=None,train_csv=None,transform=None):
        self.train_dir=train_dir
        self.train_data=pd.read_csv(train_csv)
        self.train_data.columns=['image1','image2','class']
        self.transform=transform

    def __getitem__(self,idx): ## __getitem__ returns a sample data given index, idx=index

        img1_path=os.path.join(self.train_dir,self.train_data.iat[idx,0])
        img2_path=os.path.join(self.train_dir,self.train_data.iat[idx,1])

        img1=Image.open(img1_path)
        img2=Image.open(img2_path)

        img1=img1.convert('L') #L mode image, that means it is a single channel image - normally interpreted as greyscale.
        img2=img2.convert('L')

        img1=self.transform(img1)
        img2=self.transform(img2)

        return img1, img2, torch.from_numpy(np.array([int(self.train_data.iat[idx,2])],dtype=np.float32))


    def __len__(self): ## __len__ returns the size of the dataset..
        return len(self.train_data)
    
if __name__ == "__main__":
    print("test1")

    """# Defining Training Directories and CSV's:   -"""

    train_dir="signature-verification-dataset\\sign_data\\train"
    train_csv="C:\\Users\\orlan\\OneDrive\\Documents\\mais\\signature-verification-dataset\\sign_data\\sign_data\\train_data.csv"
    test_csv="signature-verification-dataset\\sign_data\\test_data.csv"
    test_dir="signature-verification-dataset\\sign_data\\test"


    col_name = ['image1','image2','label']
    df_train=pd.read_csv(train_csv,names = col_name)
    df_train.sample(10)

    """# Here we are seeing that 1 denotes for forged pair and 0 denotes for genuine pair of signatures.."""

    col_name1 =  ['Image_1','Image_2','label']
    df_test=pd.read_csv(test_csv, names = col_name1)
    df_test.sample(10)

    df_train.shape

    df_test.shape

    df_train[4:5]

    image1_path=os.path.join(train_dir,df_train.iat[4,0])
    image1_path


    """# Returns Image1, Image2 and the class label(whether 0 or 1)."""

    dataset = Sign_Data(train_dir,train_csv,transform=transforms.Compose([transforms.Resize((100,100)),transforms.ToTensor()]))


    """# Siamese Network:-"""

    train_dataloader = DataLoader(dataset,
                            shuffle=True,
                            num_workers=1,
                            batch_size=32)


    if torch.cuda.is_available():
        print('Yes cuda')

    device = torch.device("cuda")
    net = SiameseNetwork().to(device)

    criterion = ContrastiveLoss()

    optimizer = optim.RMSprop(net.parameters(), lr=1e-4, alpha=0.99)

    def train():
        loss= []

        for epoch in range(1,10):
            for i, data in enumerate(train_dataloader,0):
                img0, img1 , label = data
                img0, img1 , label = img0.cuda(), img1.cuda() , label.cuda()
                optimizer.zero_grad()
                output1,output2 = net(img0,img1)
                loss_contrastive = criterion(output1,output2,label)
                loss_contrastive.backward()
                optimizer.step()

            print("Epoch {}\n Current loss {}\n".format(epoch,loss_contrastive.item()))

            loss.append(loss_contrastive.item())

        return net

    model = train()
    torch.save(model.state_dict(), "model.pt")
    print("Model Saved Successfully")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = SiameseNetwork().to(device)
    model.load_state_dict(torch.load("model.pt"))


