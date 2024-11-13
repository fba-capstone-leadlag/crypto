import torch    #A
USE_CUDA = False    #A
DEVICE_TYPE = torch.device("cuda" if USE_CUDA else "cpu")    #A
#A Use CUDA if it is available.

from torch.utils.data import Dataset

import numpy as np
import pandas as pd
from torchvision import transforms

class CombinedDataset(Dataset):    #A
    def __init__(self, csv_file):
        self.dataset = pd.read_csv(csv_file)
        
    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        images = self.dataset.iloc[idx, 3:]    #B
        images = np.array(images, dtype='float32')/255.  #B
        images = images.reshape(28, 28)    #B
        transform = transforms.ToTensor()    #B
        images = transform(images)    #B
        digits = self.dataset.iloc[idx, 2]    #C
        digits = np.array([digits], dtype='int')    #C
        is_handwritten = self.dataset.iloc[idx, 1]    #D
        is_handwritten = np.array([is_handwritten], dtype='float32')    #D
        return images, digits, is_handwritten    #E
    
    
from torch.utils.data import DataLoader
from torch.utils.data import random_split

def setup_dataloaders(batch_size=64, use_cuda=USE_CUDA):    #A
    combined_dataset = CombinedDataset(
"https://raw.githubusercontent.com/altdeep/causalML/master/datasets/combined_mnist_tmnist_data.csv"
    )
    n = len(combined_dataset)    #B
    train_size = int(0.8 * n)    #B
    test_size = n - train_size    #B
    train_dataset, test_dataset = random_split(    #B
        combined_dataset,    #B
        [train_size, test_size],    #B
        generator=torch.Generator().manual_seed(42)    #B
    )    #B
    kwargs = {'num_workers': 1, 'pin_memory': use_cuda}
    train_loader = DataLoader(    #C
        train_dataset,    #C
        batch_size=batch_size,    #C
        shuffle=True,    #C
        **kwargs    #C
    )    #C
    test_loader = DataLoader(    #C
        test_dataset,    #C
        batch_size=batch_size,    #C
        shuffle=True,    #C
        **kwargs    #C
    )    #C
    return train_loader, test_loader

from torch import nn

class Decoder(nn.Module):    #A
    def __init__(self, z_dim, hidden_dim):
        super().__init__()
        img_dim = 28 * 28    #B
        digit_dim = 10    #C
        is_handwritten_dim = 1    #D
        self.softplus = nn.Softplus()    #E
        self.sigmoid = nn.Sigmoid()    #E
        encoding_dim = z_dim + digit_dim + is_handwritten_dim    #F
        self.fc1 = nn.Linear(encoding_dim, hidden_dim)    #F
        self.fc2 = nn.Linear(hidden_dim, img_dim)    #G

    def forward(self, z, digit, is_handwritten):    #H
        input = torch.cat([z, digit, is_handwritten], dim=1)   #I
        hidden = self.softplus(self.fc1(input))    #J
        img_param = self.sigmoid(self.fc2(hidden))    #K
        return img_param
    
import pyro
import pyro.distributions as dist

dist.enable_validation(False)    #A
def model(self, data_size=1):    # 생성 모델의 메인 함수 정의
    pyro.module("decoder", self.decoder)    # 디코더 모듈을 Pyro에 등록
    options = dict(dtype=torch.float32, device=DEVICE_TYPE)
    z_loc = torch.zeros(data_size, self.z_dim, **options)    # 잠재 변수의 평균값 초기화
    z_scale = torch.ones(data_size, self.z_dim, **options)    # 잠재 변수의 스케일 초기화
    z = pyro.sample("Z", dist.Normal(z_loc, z_scale).to_event(1))    # 잠재 변수 Z를 정규 분포에서 샘플링
    p_digit = torch.ones(data_size, 10, **options)/10    # 숫자 클래스의 사전 확률 (균등 분포)
    digit = pyro.sample("digit", dist.OneHotCategorical(p_digit))    # 숫자 클래스를 카테고리 분포에서 샘플링
    p_is_handwritten = torch.ones(data_size, 1, **options)/2    # 손글씨 여부의 사전 확률 (50%)
    is_handwritten = pyro.sample("is_handwritten", dist.Bernoulli(p_is_handwritten).to_event(1))    # 손글씨 여부를 베르누이 분포에서 샘플링
    img_param = self.decoder(z, digit, is_handwritten)    # 디코더를 통해 이미지 파라미터 생성
    img = pyro.sample("img", dist.Bernoulli(img_param).to_event(1))  # 최종 이미지를 베르누이 분포에서 샘플링
    return img, digit, is_handwritten

def training_model(self, img, digit, is_handwritten, batch_size):    #A
    conditioned_on_data = pyro.condition(    #B
        self.model,
        data={
            "digit": digit,
            "is_handwritten": is_handwritten,
            "img": img
        }
    )
    with pyro.plate("data", batch_size):    #C
        img, digit, is_handwritten = conditioned_on_data(batch_size)
    return img, digit, is_handwritten


class Encoder(nn.Module):    #A
    def __init__(self, z_dim, hidden_dim):
        super().__init__()
        img_dim = 28 * 28    #B
        digit_dim = 10    #C
        is_handwritten_dim = 1
        self.softplus = nn.Softplus()    #D
        input_dim = img_dim + digit_dim + is_handwritten_dim    #E
        self.fc1 = nn.Linear(input_dim, hidden_dim)    #E
        self.fc21 = nn.Linear(hidden_dim, z_dim)    #F
        self.fc22 = nn.Linear(hidden_dim, z_dim)    #F

    def forward(self, img, digit, is_handwritten):    #G
        input = torch.cat([img, digit, is_handwritten], dim=1)    #H
        hidden = self.softplus(self.fc1(input))    #I
        z_loc = self.fc21(hidden)    #J
        z_scale = torch.exp(self.fc22(hidden))    #J
        return z_loc, z_scale
    
    

def training_guide(self, img, digit, is_handwritten, batch_size):    #A
    pyro.module("encoder", self.encoder)    #B
    options = dict(dtype=torch.float32, device=DEVICE_TYPE)
    with pyro.plate("data", batch_size):    #C
        z_loc, z_scale = self.encoder(img, digit, is_handwritten)    #D
        normal_dist = dist.Normal(z_loc, z_scale).to_event(1)    #D
        z = pyro.sample("Z", normal_dist)    #E
        
        
class VAE(nn.Module):
    def __init__(
        self,
        z_dim=50,    #A
        hidden_dim=400,    #B
        use_cuda=USE_CUDA,
    ):
        super().__init__()
        self.use_cuda = use_cuda
        self.z_dim = z_dim
        self.hidden_dim = hidden_dim
        self.setup_networks()

    def setup_networks(self):    #C
        self.encoder = Encoder(self.z_dim, self.hidden_dim)
        self.decoder = Decoder(self.z_dim, self.hidden_dim)
        if self.use_cuda:
            self.cuda()

    model = model    #D
    training_model = training_model    #D
    training_guide = training_guide    #D
    

def plot_image(img, title=None):    #A
    fig = plt.figure()
    plt.imshow(img.cpu(), cmap='Greys_r', interpolation='nearest')
    if title is not None:
        plt.title(title)
    plt.show()
#A Helper function for plotting an image

import matplotlib.pyplot as plt

def reconstruct_img(vae, img, digit, is_hw, use_cuda=USE_CUDA):    #A
    img = img.reshape(-1, 28 * 28)
    digit = F.one_hot(torch.tensor(digit), 10)
    is_hw = torch.tensor(is_hw).unsqueeze(0)
    if use_cuda:
        img = img.cuda()
        digit = digit.cuda()
        is_hw = is_hw.cuda()
    z_loc, z_scale = vae.encoder(img, digit, is_hw)
    z = dist.Normal(z_loc, z_scale).sample()
    img_expectation = vae.decoder(z, digit, is_hw)
    return img_expectation.squeeze().view(28, 28).detach()

def compare_images(img1, img2):    #B
    fig = plt.figure()
    ax0 = fig.add_subplot(121)
    plt.imshow(img1.cpu(), cmap='Greys_r', interpolation='nearest')
    plt.axis('off')
    plt.title('original')
    ax1 = fig.add_subplot(122)
    plt.imshow(img2.cpu(), cmap='Greys_r', interpolation='nearest')
    plt.axis('off')
    plt.title('reconstruction')
    plt.show()
    

import torch.nn.functional as F

def get_random_example(loader):    #A
    random_idx = np.random.randint(0, len(loader.dataset))    #A
    img, digit, is_handwritten = loader.dataset[random_idx]    #A
    return img.squeeze(), digit, is_handwritten    #A

def reshape_data(img, digit, is_handwritten):    #B
    digit = F.one_hot(digit, 10).squeeze()    #B
    img = img.reshape(-1, 28*28)    #B
    return img, digit, is_handwritten    #B

def generate_coded_data(vae, use_cuda=USE_CUDA):    #C
    z_loc = torch.zeros(1, vae.z_dim)    #C
    z_scale = torch.ones(1, vae.z_dim)    #C
    z = dist.Normal(z_loc, z_scale).to_event(1).sample()    #C
    p_digit = torch.ones(1, 10)/10    #C
    digit = dist.OneHotCategorical(p_digit).sample()    #C
    p_is_handwritten = torch.ones(1, 1)/2    #C
    is_handwritten = dist.Bernoulli(p_is_handwritten).sample()    #C
    if use_cuda:    #C
        z = z.cuda()
        digit = digit.cuda()
        is_handwritten = is_handwritten.cuda()    #C
    img = vae.decoder(z, digit, is_handwritten)    #C
    return img, digit, is_handwritten    #C

def generate_data(vae, use_cuda=USE_CUDA):    #D
    img, digit, is_handwritten = generate_coded_data(vae, use_cuda)    #D
    img = img.squeeze().view(28, 28).detach()    #D
    digit = torch.argmax(digit, 1)    #D
    is_handwritten = torch.argmax(is_handwritten, 1)    #D
    return img, digit, is_handwritten    #D


from pyro.infer import SVI, Trace_ELBO
from pyro.optim import Adam

pyro.clear_param_store()    #A
vae = VAE()    #B
train_loader, test_loader = setup_dataloaders(batch_size=256)    #C
svi_adam = Adam({"lr": 1.0e-3})    #D
model = vae.training_model    #E
guide = vae.training_guide    #E
svi = SVI(model, guide, svi_adam, loss=Trace_ELBO())    #E


def test_epoch(vae, test_loader):
    epoch_loss_test = 0    #A
    for img, digit, is_hw in test_loader:    #A
        batch_size = img.shape[0]    #A
        if USE_CUDA:    #A
            img = img.cuda()    #A
            digit = digit.cuda()    #A
            is_hw = is_hw.cuda()    #A
        img, digit, is_hw = reshape_data(    #A
            img, digit, is_hw    #A
        )    #A
        epoch_loss_test += svi.evaluate_loss(    #A
            img, digit, is_hw, batch_size    #A
        )    #A
    test_size = len(test_loader.dataset)    #A
    avg_loss = epoch_loss_test/test_size    #A
    print("Epoch: {} avg. test loss: {}".format(epoch, avg_loss))    #A
    print("Comparing a random test image to its reconstruction:")    #B
    random_example = get_random_example(test_loader)    #B
    img_r, digit_r, is_hw_r = random_example    #B
    img_recon = reconstruct_img(vae, img_r, digit_r, is_hw_r)    #B
    compare_images(img_r, img_recon)    #B
    print("Generate a random image from the model:")    #C
    img_gen, digit_gen, is_hw_gen = generate_data(vae)    #C
    plot_image(img_gen, "Generated Image")    #C
    print("Intended digit: ", int(digit_gen))    #C
    print("Intended as handwritten: ", bool(is_hw_gen == 1))    #C
    
    

NUM_EPOCHS = 2500
TEST_FREQUENCY = 10

train_loss = []
train_size = len(train_loader.dataset)

for epoch in range(0, NUM_EPOCHS+1):    #A
    loss = 0
    for img, digit, is_handwritten in train_loader:
        batch_size = img.shape[0]
        if USE_CUDA:
            img = img.cuda()
            digit = digit.cuda()
            is_handwritten = is_handwritten.cuda()
        img, digit, is_handwritten = reshape_data(
            img, digit, is_handwritten
        )
        loss += svi.step(    #B
            img, digit, is_handwritten, batch_size    #B
        )    #B
    avg_loss = loss / train_size
    print("Epoch: {} avgs training loss: {}".format(epoch, loss))
    train_loss.append(avg_loss)
    if epoch % TEST_FREQUENCY == 0:    #C
        test_epoch(vae, test_loader)    #C