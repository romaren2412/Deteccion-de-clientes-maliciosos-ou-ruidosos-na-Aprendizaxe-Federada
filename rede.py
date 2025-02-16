import math
import torch.nn as nn
import torch.nn.init as init


class MnistNet(nn.Module):
    def __init__(self, num_channels, num_outputs):
        super(MnistNet, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=num_channels, out_channels=30, kernel_size=3)
        self.relu1 = nn.ReLU()
        self.maxpool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(in_channels=30, out_channels=5, kernel_size=3)
        self.relu2 = nn.ReLU()
        self.maxpool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(5 * 5 * 5, 100)  # Adjust the input features
        self.relu3 = nn.ReLU()
        self.fc2 = nn.Linear(100, num_outputs)
        self.softmax = nn.Softmax(dim=1)  # Apply softmax to the output

    def forward(self, x):
        x = self.maxpool1(self.relu1(self.conv1(x)))
        x = self.maxpool2(self.relu2(self.conv2(x)))
        x = self.flatten(x)
        x = self.relu3(self.fc1(x))
        x = self.fc2(x)
        x = self.softmax(x)
        return x

    def initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                # Inicialización He para capas convolucionales
                init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                # Inicialización uniforme para capas lineales
                init.kaiming_uniform_(m.weight, a=math.sqrt(5))  # a es el factor de la rectificación lineal
                if m.bias is not None:
                    fan_in, _ = init._calculate_fan_in_and_fan_out(m.weight)
                    bound = 1 / math.sqrt(fan_in)
                    init.uniform_(m.bias, -bound, bound)
