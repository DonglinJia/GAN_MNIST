# GAN For MNIST

- GAN stands for Generative Adversarial Network. It consists of two parts of neural network -- generator and discriminator 

## Generator: 
  - consists of different number of layers 
  - input: noise 
  - output: generated (fake) objects 

## Discriminator:
  - consists of different number of layers 
  - input: generator's output(fake objects) & real objects
  - output: 1/0
    1. 1 represents input is real object 
    2. 0 represents input is fake object

## Ideas behind GAN
- Two individual neural network "compete" with each other 
- loss function punish the one who fails
  1. discriminator failed to identify the fake objects 
  2. generator failed to trick discriminator 

## Model collapse for this model
- In order to avoid model collapse, I resolved it by adding multiple training times for discriminator. That is for each training the generator, the discriminator will be trained multiple times. 
- Please refer to https://github.com/soumith/ganhacks to get more tips when training GAN
