from tensorflow.keras.datasets import fashion_mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras import utils
import numpy as np
import matplotlib.pyplot as plt

classes = ['футболка', 'брюки', 'свитер', 'платье', 'пальто', 'туфли', 'рубашка', 'кроссовки', 'сумка', 'ботинки']
(x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
x_train = x_train.reshape(60000, 784)
x_train = x_train / 255
y_train = utils.to_categorical(y_train, 10)

model = Sequential()
model.add(Dense(800, input_dim=784, activation="relu"))
model.add(Dense(10, activation="softmax"))
model.compile(loss="categorical_crossentropy", optimizer="SGD", metrics=["accuracy"])

print(model.summary())

model.fit(x_train, y_train, batch_size=200, epochs=100, verbose=1)
predictions = model.predict(x_train)

n = 5
plt.imshow(x_train[n].reshape(28, 28), cmap=plt.cm.binary)
plt.show()
print(np.argmax(predictions[n]), classes[np.argmax(predictions[n])])
print(np.argmax(y_train[n]), classes[np.argmax(y_train[n])])
