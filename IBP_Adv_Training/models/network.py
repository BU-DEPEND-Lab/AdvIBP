# Copyright (C) 2020, Jiameng Fan <jmfan@bu.edu>
#
# This program is licenced under the MIT License,
# contained in the LICENCE file in this directory.


import torch.nn as nn
import numpy as np
from IBP_Adv_Training.models.operation import Flatten


def model_mlp_any(in_dim, neurons, out_dim=10):
    """
    MLP model, each layer has the different number of neurons
    Parameter:
        in_dim: input image dimension, 784 for MNIST and 1024 for CIFAR
        neurons: a list of neurons for each layer
    """
    assert len(neurons) >= 1
    # input layer
    units = [Flatten(), nn.Linear(in_dim, neurons[0])]
    prev = neurons[0]
    # intermidiate layers
    for n in neurons[1:-1]:
        units.append(nn.ReLU())
        units.append(nn.Linear(prev, n))
        prev = n
    # output layer
    units.append(nn.ReLU())
    units.append(nn.Linear(neurons[-1], out_dim))

    return nn.Sequential(*units)


def model_cnn_2layer(in_ch, in_dim, width, linear_size=128):
    """
    CNN, small 2-layer (default kernel size is 4 by 4)
    Parameter:
        in_ch: input image channel, 1 for MNIST and 3 for CIFAR
        in_dim: input dimension, 28 for MNIST and 32 for CIFAR
        width: width multiplier
    """
    conv1_shape = conv_out_shape((in_dim, in_dim), 4, 2, 1)
    conv2_shape = conv_out_shape(conv1_shape, 4, 1, 1)
    model = nn.Sequential(
        nn.Conv2d(in_ch, 4 * width, 4, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(4 * width, 8 * width, 4, stride=1, padding=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(8 * width * np.prod(conv2_shape).item(), linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def model_cnn_2layer_ibp(in_ch, in_dim, width, linear_size=128):
    """
    CNN, small 2-layer (default kernel size is 4 by 4)
    Parameter:
        in_ch: input image channel, 1 for MNIST and 3 for CIFAR
        in_dim: input dimension, 28 for MNIST and 32 for CIFAR
        width: width multiplier
    """
    conv1_shape = conv_out_shape((in_dim, in_dim), 4, 2, 1)
    conv2_shape = conv_out_shape(conv1_shape, 4, 2, 1)
    model = nn.Sequential(
        nn.Conv2d(in_ch, 4 * width, 4, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(4 * width, 8 * width, 4, stride=2, padding=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(8 * width * np.prod(conv2_shape).item(), linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def model_cnn_3layer(in_ch, in_dim, kernel_size, width, linear_size=None):
    """
    CNN, relatively small 3-layer
    Parameter:
        in_ch: input image channel, 1 for MNIST and 3 for CIFAR
        in_dim: input dimension, 28 for MNIST and 32 for CIFAR
        kernel_size: convolutional kernel size: 3 or 5
        width: width multiplier
    """
    if linear_size is None:
        linear_size = width * 64
    if kernel_size == 5:
        h = (in_dim - 4) // 4
    elif kernel_size == 3:
        h = in_dim // 4
    else:
        raise ("Unsupported kernel size")
    model = nn.Sequential(
        nn.Conv2d(in_ch, 4 * width,
                  kernel_size=kernel_size, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(4 * width, 8 * width,
                  kernel_size=kernel_size, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(8 * width, 8 * width, kernel_size=4, stride=4, padding=0),
        nn.ReLU(),
        Flatten(),
        nn.Linear(8 * width * h * h, linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def model_cnn_4layer(in_ch, in_dim, width, linear_size):
    """
    CNN, relatively large 4-layer
    Parameter:
        in_ch: input image channel, 1 for MNIST and 3 for CIFAR
        in_dim: input dimension, 28 for MNIST and 32 for CIFAR
        width: width multiplier
    """
    model = nn.Sequential(
        nn.Conv2d(in_ch, 4 * width, 3, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(4 * width, 4 * width, 4, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(4 * width, 8 * width, 3, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(8 * width, 8 * width, 4, stride=2, padding=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(8 * width * (in_dim // 4) * (in_dim // 4), linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def model_cnn_2layer_new(in_ch, in_dim, width, linear_size):
    conv1_shape = conv_out_shape((in_dim, in_dim), 3, 2, 0)
    conv2_shape = conv_out_shape(conv1_shape, 3, 1, 0)
    model = nn.Sequential(
        nn.Conv2d(in_ch, 4 * width, 3, stride=2),
        nn.ReLU(),
        nn.Conv2d(4 * width, 8 * width, 3, stride=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(8 * width * np.prod(conv2_shape).item(), linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def model_cnn_4layer_new(in_ch, in_dim, width, linear_size):
    conv1_shape = conv_out_shape((in_dim, in_dim), 3, 2, 0)
    conv2_shape = conv_out_shape(conv1_shape, 3, 1, 0)
    conv3_shape = conv_out_shape(conv2_shape, 3, 1, 0)
    conv4_shape = conv_out_shape(conv3_shape, 3, 1, 0)
    model = nn.Sequential(
        nn.Conv2d(in_ch, 4 * width, 3, stride=2),
        nn.ReLU(),
        nn.Conv2d(4 * width, 8 * width, 3, stride=1),
        nn.ReLU(),
        nn.Conv2d(8 * width, 16 * width, 3, stride=1),
        nn.ReLU(),
        nn.Conv2d(16 * width, 32 * width, 3, stride=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(32 * width * np.prod(conv4_shape).item(), linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def IBP_large(in_ch, in_dim, linear_size=512):
    model = nn.Sequential(
        nn.Conv2d(in_ch, 64, 3, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(64, 64, 3, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(64, 128, 3, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(128, 128, 3, stride=1, padding=1),
        nn.ReLU(),
        nn.Conv2d(128, 128, 3, stride=1, padding=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear((in_dim // 2) * (in_dim // 2) * 128, linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def IBP_large_new(in_ch, in_dim, linear_size=512):
    conv1_shape = conv_out_shape((in_dim, in_dim), 3, 2, 0)
    conv2_shape = conv_out_shape(conv1_shape, 3, 1, 0)
    conv3_shape = conv_out_shape(conv2_shape, 3, 1, 0)
    conv4_shape = conv_out_shape(conv3_shape, 3, 1, 0)
    conv5_shape = conv_out_shape(conv4_shape, 3, 1, 0)
    model = nn.Sequential(
        nn.Conv2d(in_ch, 64, 3, stride=2),
        nn.ReLU(),
        nn.Conv2d(64, 64, 3, stride=1),
        nn.ReLU(),
        nn.Conv2d(64, 128, 3, stride=1),
        nn.ReLU(),
        nn.Conv2d(128, 256, 3, stride=1),
        nn.ReLU(),
        nn.Conv2d(256, 256, 3, stride=1),
        nn.ReLU(),
        Flatten(),
        nn.Linear(256 * np.prod(conv5_shape).item(), linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def IBP_debug(in_ch, in_dim, linear_size=512):
    model = nn.Sequential(
        Flatten(),
        nn.Linear(in_ch * in_dim * in_dim, linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, linear_size),
        nn.ReLU(),
        nn.Linear(linear_size, 10)
    )
    return model


def conv_out(h_in, kernel_size, stride, padding):
    return int((h_in + 2. * padding - (kernel_size - 1.) - 1.) / stride + 1.)


def conv_out_shape(h_in, kernel_size, stride, padding):
    return tuple(conv_out(x, kernel_size, stride, padding) for x in h_in)
