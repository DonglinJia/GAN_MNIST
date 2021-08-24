from __future__ import print_function
import torch
import torch.utils.data
from torch import nn, optim
from torchvision import datasets, transforms
from torchvision.utils import save_image
from IPython.display import Image, display
import matplotlib.pyplot as plt
from torch.autograd import Variable
import os

if not os.path.exists('results'):
    os.mkdir('results')

batch_size = 100
latent_size = 20

cuda = torch.cuda.is_available()
device = torch.device("cuda" if cuda else "cpu")

kwargs = {'num_workers': 1, 'pin_memory': True} if cuda else {}
train_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../data', train=True, download=True,
                   transform=transforms.ToTensor()),
    batch_size=batch_size, shuffle=True, **kwargs)
test_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../data', train=False, transform=transforms.ToTensor()),
    batch_size=batch_size, shuffle=True, **kwargs)


class Generator(nn.Module):
    #The generator takes an input of size latent_size, and will produce an output of size 784.
    #It should have a single hidden linear layer with 400 nodes using ReLU activations, and use Sigmoid activation for its outputs
    def __init__(self):
        super(Generator, self).__init__()
        self.sigmoid = nn.Sigmoid()
        self.relu = nn.ReLU()
        self.fc_g1 = nn.Linear(latent_size, 400)
        self.fc_g2 = nn.Linear(400, 784)

    def forward(self, z):
        h1 = self.relu(self.fc_g1(z))
        return self.sigmoid(self.fc_g2(h1))

class Discriminator(nn.Module):
    #The discriminator takes an input of size 784, and will produce an output of size 1.
    #It should have a single hidden linear layer with 400 nodes using ReLU activations, and use Sigmoid activation for its output
    def __init__(self):
        super(Discriminator, self).__init__()
        self.sigmoid = nn.Sigmoid()
        self.relu = nn.ReLU()
        self.fc_d1 = nn.Linear(784, 400)
        self.fc_d2 = nn.Linear(400, 1)

    def forward(self, x):
        h1 = self.relu(self.fc_d1(x))
        return self.sigmoid(self.fc_d2(h1))

def train(generator, generator_optimizer, discriminator, discriminator_optimizer, epoch):
    #Trains both the generator and discriminator for one epoch on the training dataset.
    #Returns the average generator and discriminator loss (scalar values, use the binary cross-entropy appropriately)
    
    avg_generator_loss = 0
    avg_discriminator_loss = 0
    criterion = nn.BCELoss(reduction='sum')

    for batch_index, (x, _) in enumerate(train_loader):

        # ======================= Train discriminator ==============================
        discriminator_optimizer.zero_grad()
        # x to be real image, y to be 1 as it is real image's prediction
        x_real, y_real = x.view(-1, 784), torch.ones(batch_size, 1)
        x_real, y_real = Variable(x_real.to(device)), Variable(y_real.to(device))
        # Train discriminator on real data
        d_output_real = discriminator(x_real)
        d_real_loss = criterion(d_output_real, y_real)
        d_real_loss.backward()

        # randomly generate noise z
        z = Variable(torch.randn(batch_size, latent_size).to(device))
        # x to be fake as they are generated by generator, y_fake as the fake label
        x_fake, y_fake = generator(z), Variable(torch.zeros(batch_size, 1).to(device))
        # Train discriminator on fake data
        d_output_fake = discriminator(x_fake)
        d_fake_loss = criterion(d_output_fake, y_fake)
        d_fake_loss.backward(retain_graph=True)

        d_loss = d_real_loss + d_fake_loss
        discriminator_optimizer.step()

        avg_discriminator_loss += d_loss.item()

        # ============================= Train generator =================================
        # To resolve model collapse, train generator twice for each discriminator train
        for _ in range(2):
            generator_optimizer.zero_grad()

            # y = Variable(torch.ones(batch_size, 1).to(device))
            # use updated discriminator to check the generated output images
            output_fake = discriminator(x_fake)
            g_loss = criterion(output_fake, y_real)

            g_loss.backward(retain_graph=True)
            generator_optimizer.step()
            
            x_fake = generator(z)
            avg_generator_loss += g_loss.item()

        if batch_index % 100 == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\t Generator Loss: {:.6f} \t Discriminator Loss: {:.6f}'.format(
                epoch, batch_index * len(x), len(train_loader.dataset),
                100. * batch_index / len(train_loader), g_loss.item() / len(x), 
                d_loss.item() / len(x)))

    avg_generator_loss /= (2 * len(train_loader.dataset))
    avg_discriminator_loss /= len(train_loader.dataset)

    return avg_generator_loss, avg_discriminator_loss

def test(generator, discriminator):
    #Runs both the generator and discriminator over the test dataset.
    #Returns the average generator and discriminator loss (scalar values, use the binary cross-entropy appropriately)
    avg_generator_loss = 0
    avg_discriminator_loss = 0
    criterion = nn.BCELoss(reduction='sum')

    with torch.no_grad():
        for _, (data, _) in enumerate(test_loader):
            # =========================== Discriminator loss =============================
            # Feed real data to trained discriminator
            x_real, y_real = data.view(-1, 784), torch.ones(batch_size, 1)
            x_real, y_real = Variable(x_real.to(device)), Variable(y_real.to(device))
            d_output_real = discriminator(x_real)
            # Get real data loss 
            d_real_loss = criterion(d_output_real, y_real)

            # Feed fake data to trained discriminator
            z = Variable(torch.randn(batch_size, latent_size).to(device))
            # Get fake data and fake label
            x_fake, y_fake = generator(z), Variable(torch.zeros(batch_size, 1).to(device))
            d_output_fake = discriminator(x_fake)
            # Get fake data loss
            d_fake_loss = criterion(d_output_fake, y_fake)
            d_loss = d_real_loss + d_fake_loss

            
            # =========================== Generator loss ==========================
            g_loss = criterion(d_output_fake, y_real)
            
            avg_generator_loss += g_loss.item()
            avg_discriminator_loss += d_loss.item()


    avg_generator_loss /= len(test_loader.dataset)
    avg_discriminator_loss /= len(test_loader.dataset)

    print('\nEpoch {}: Test set: Average Generator loss: {:.6f}, Average Discriminator loss: {:.6f} \n'.format(epoch, 
        avg_generator_loss, avg_discriminator_loss))

    return avg_generator_loss, avg_discriminator_loss


epochs = 50

discriminator_avg_train_losses = []
discriminator_avg_test_losses = []
generator_avg_train_losses = []
generator_avg_test_losses = []

generator = Generator().to(device)
discriminator = Discriminator().to(device)

generator_optimizer = optim.Adam(generator.parameters(), lr=5e-4)
discriminator_optimizer = optim.Adam(discriminator.parameters(), lr=1e-3)

for epoch in range(1, epochs + 1):
    generator_avg_train_loss, discriminator_avg_train_loss = train(generator, generator_optimizer, discriminator, discriminator_optimizer, epoch)
    generator_avg_test_loss, discriminator_avg_test_loss = test(generator, discriminator)

    discriminator_avg_train_losses.append(discriminator_avg_train_loss)
    generator_avg_train_losses.append(generator_avg_train_loss)
    discriminator_avg_test_losses.append(discriminator_avg_test_loss)
    generator_avg_test_losses.append(generator_avg_test_loss)

    with torch.no_grad():
        sample = torch.randn(64, latent_size).to(device)
        sample = generator(sample).cpu()
        save_image(sample.view(64, 1, 28, 28),
                   'results/sample_GAN_' + str(epoch) + '.png')
        print('Epoch #' + str(epoch))
        display(Image('results/sample_GAN_' + str(epoch) + '.png'))
        print('\n')

fig_train_loss = plt.figure()
plt.plot(discriminator_avg_train_losses)
plt.plot(generator_avg_train_losses)
plt.title('Training Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Disc','Gen'], loc='upper right')
plt.show()
fig_train_loss.savefig('GAN_Train_loss.png')

fig_test_loss = plt.figure()
plt.plot(discriminator_avg_test_losses)
plt.plot(generator_avg_test_losses)
plt.title('Test Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Disc','Gen'], loc='upper right')
plt.show()
fig_test_loss.savefig('GAN_Test_loss.png')
