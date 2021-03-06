# -*- coding: utf-8 -*-
"""U-net.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dn_63qmGk1umxkVF__98B-l590Lm6XJT
"""

import numpy as np
import tensorflow as tf
import random
import os
# %matplotlib inline
import matplotlib.pyplot as plt


def leaky_relu(input):
    # leaky ReLU
    alpha = 0.01
    output = tf.maximum(alpha * input, input)
    return output


def conv_block(input, num_conv, kernel_size, layer_num):
    # first convolution to scale the kernels
    with tf.variable_scope('conv' + str(layer_num)):
        weights = tf.get_variable('w', kernel_size)

        input = tf.nn.conv2d(input, weights, strides=[1, 1, 1, 1], padding='SAME')  # VALID, SAME

        bias = tf.get_variable('b', [kernel_size[3]])
        input = tf.add(input, bias)
        input = leaky_relu(input)
        layer_num += 1

    kernel_size[2] = kernel_size[3]
    for i in range(num_conv - 1):
        with tf.variable_scope('conv' + str(layer_num)):
            weights = tf.get_variable('w', kernel_size)
            input = tf.nn.conv2d(input, weights, strides=[1, 1, 1, 1], padding='SAME')  # VALID, SAME

            bias = tf.get_variable('b', [kernel_size[3]])
            input = tf.add(input, bias)

            input = leaky_relu(input)
            layer_num += 1
    return input, layer_num


def load_data(path):
    return np.load(os.path.join(path, 'train_img.npy')), \
           np.load(os.path.join(path, 'train_mask.npy')), \
           np.load(os.path.join(path, 'test_img.npy')), \
           np.load(os.path.join(path, 'test_mask.npy'))


def get_next_batch(img, mask, batch_length):
    assert len(img) == len(mask)

    used_in_batch = random.sample(range(len(img)), batch_length)
    return img[used_in_batch, :], mask[used_in_batch, :]

!pip
install - U - q
PyDrive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials

auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

f = drive.CreateFile({'id': '1XeuSYBk2PPwEX7GWKyytc8ySggPkkYiB'})
f.GetContentFile('data.zip')
!unzip
data.zip

train_img, train_mask, test_img, test_mask = load_data('./')

fig = plt.figure(figsize=(18, 10))
ax = fig.subplots(nrows=1, ncols=2)
ax[0].imshow(train_img[0, :] / 255)
ax[1].imshow(train_mask[0, :] / 255)
plt.show()

batch_length = 2
# input image shape
input_shape = [48, 48, 3]
# `label` shape (here we usually call it ground truth, because there is no definite answer)
ground_truth_shape = [48, 48, 3]
leaning_rate = 1e-3
num_iteration = 8000
num_kernels = [input_shape[-1], 16, 32, 64, 128]


def generate_graph():
    # due to the U-net structure, it is easier to store the shapes of the downsampling part of the network
    img_sizes = []
    # we need to store the output of the left layers to be able to create skip connections
    left_layers = []
    layer_num = 0

    tf.reset_default_graph()

    # placeholders
    input = tf.placeholder(tf.float32, [None] + input_shape)
    ground_truth = tf.placeholder(tf.float32, [None] + ground_truth_shape)

    current_input = input

    # a loop to create our downsampling layers
    for n in range(0, len(num_kernels) - 2):
        with tf.variable_scope('conv' + str(layer_num)):
            layer_left, layer_num = conv_block(current_input, 1, [3, 3, num_kernels[n], num_kernels[n + 1]], layer_num)
            current_input = tf.nn.max_pool(layer_left, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1],
                                           padding='SAME')  # downsampling with pooling
            print(curren
            i
            t_input)

            left_layers.append(layer_left)
            img_sizes.append([int(layer_left.get_shape()[1]), int(layer_left.get_shape()[2])])
            layer_num += 1

    # last convolution at the `bottom` of the net
    current_input, layer_num = conv_block(current_input, 2, [3, 3, num_kernels[-2], num_kernels[-1]], layer_num)

    print(current_input)

    # now we are upsampling
    for n in range(len(num_kernels) - 1, 1, -1):
        with tf.variable_scope('conv' + str(layer_num)):
            weights = tf.get_variable('weights', [3, 3, num_kernels[n - 1], num_kernels[n]])
            layer_right = tf.nn.conv2d_transpose(current_input,
                                                 weights,
                                                 [batch_length, img_sizes[n - 2][0], img_sizes[n - 2][1],
                                                  num_kernels[n - 1]],
                                                 [1, 2, 2, 1],
                                                 padding='SAME',
                                                 name=None)
            print(layer_right)
            bias = tf.get_variable('B', [num_kernels[n - 1]])
            layer_right = tf.add(layer_right, bias)
            layer_right = leaky_relu(layer_right)
            layer_num += 1
            current_input = tf.concat([layer_right, left_layers[n - 2]], 3)
            current_input, layer_num = conv_block(current_input, 2, [3, 3, num_kernels[n], num_kernels[n - 1]],
                                                  layer_num)

    # last convolution, we use this to get the desired output shape, for example we could have a smaller size image than the original as the result of the segmentation if we wanted
    with tf.variable_scope('conv' + str(layer_num)):
        weights = tf.get_variable('weights', [3, 3, num_kernels[1], ground_truth_shape[-1]])
        layer_out = tf.nn.conv2d(current_input, weights, strides=[1, 1, 1, 1], padding='SAME')  # VALID, SAME
        bias = tf.get_variable('B', [ground_truth_shape[-1]])
        layer_out = tf.add(layer_out, bias)

    # no nonlinearity at the end
    output = layer_out
    print(output)

    # Define loss and optimizer
    with tf.name_scope('loss'):
        # L1 loss be
        abs_diff = tf.abs(tf.subtract(ground_truth, output))

        # average loss because of batching
        L1_loss = tf.reduce_mean(abs_diff)

    with tf.name_scope('optimizer'):
        # Use ADAM optimizer this is currently the best performing training algorithm in most cases
        optimizer = tf.train.AdamOptimizer(leaning_rate).minimize(L1_loss)

    print('Computation graph building done!')
    return input, ground_truth, optimizer, L1_loss, output


input, ground_truth, optimizer, L1_loss, output = generate_graph()
init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init)
    saver = tf.train.Saver()
    step = 0
    while step < num_iteration:
        step += 1

        img_batch, mask_batch = get_next_batch(train_img, train_mask, batch_length)
        _, l, output_img = sess.run([optimizer, L1_loss, output],
                                    feed_dict={input: img_batch, ground_truth: mask_batch})

        if (step % 100) == 0:
            # train accuracy
            print('Iteration: %d, loss: %.5f' % (step, l), flush=True)

        if (step % 1000) == 0:
            assert len(test_img) == len(test_mask)
            avg_loss = 0.0
            for i in range(len(test_img[0:100, :]) // batch_length):
                img_batch, mask_batch = get_next_batch(train_img, train_mask, batch_length)

                l, output_img = sess.run([L1_loss, output], feed_dict={input: img_batch, ground_truth: mask_batch})
                avg_loss += l

            avg_loss /= (len(test_img) // batch_length)
            print('Loss on test set: %.5f at step %d\n' % (l, step), flush=True)

        if (step % num_iteration) == 0:
            print('Saving model...')
            print(saver.save(sess, "./checkpoint/model", step))

# demo

input, ground_truth, optimizer, L1_loss, output = generate_graph()
init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init)
    saver = tf.train.Saver()

    saver.restore(sess, './checkpoint/model-' + str(num_iteration))

    fig = plt.figure(figsize=(15, 50))
    ax = fig.subplots(nrows=10, ncols=3)
    for i in range(10):
        random_ind = random.sample(range(len(test_img)), 1)
        input_img = np.reshape(test_img[random_ind, :], (1, 48, 48, 3))
        input_mask = np.reshape(test_mask[random_ind, :], (1, 48, 48, 3))
        batch_length = 1

        out_img = sess.run(output, feed_dict={input: input_img})
        out_img[out_img < 0] = 0

        ax[i, 0].imshow(input_img[0, :] / 255)
        ax[i, 1].imshow(input_mask[0, :] / 255)
        ax[i, 2].imshow(out_img[0] / 255)
    plt.show()