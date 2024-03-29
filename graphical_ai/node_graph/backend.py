import tensorflow as tf


def objv_mse(ypred, y):
    n = len(ypred)
    return sum((ypred - y) ** 2) / n


class ModelLinearReg():
    def __init__(self, independent_var):
        self.coef = tf.Variable([1.0 for _ in range(0, independent_var)])
        self.bias = tf.Variable(0.0)

    def pred(self, x):
        # x.shape() == (_, features)
        # coef.shape() == (features)
        return tf.math.reduce_sum(x * self.coef, axis=1) + self.bias

    def update(self, x, y, learning_rate):
        with tf.GradientTape(persistent=True) as g:
            loss = objv_mse(self.pred(x), y)

        print("loss: ", loss)

        dy_dm = g.gradient(loss, self.coef)
        dy_db = g.gradient(loss, self.bias)

        # print(dy_dm)
        # print(dy_db)

        self.coef.assign_sub(learning_rate * dy_dm)
        self.bias.assign_sub(learning_rate * dy_db)

    def train(self, x, y, epochs, learning_rate=0.01):
        for i in range(epochs):
            # print("Epoch: ", i)

            self.update(x, y, learning_rate)


class ModelLogisticReg():
    def __init__(self):
        self.l = tf.Variable(1.0)
        self.k = tf.Variable(1.0)
        self.x0 = tf.Variable(0.0)

    def pred(self, x):
        return self.l/(1+tf.math.exp(-self.k*(x-self.x0)))

    def update(self, x, y, learning_rate):
        with tf.GradientTape(persistent=True) as g:
            loss = objv_mse(self.pred(x), y)

        print("loss: ", loss)

        dy_dl = g.gradient(loss, self.l)
        dy_dk = g.gradient(loss, self.k)
        dy_dx0 = g.gradient(loss, self.x0)

        # print(dy_dm)
        # print(dy_db)

        self.l.assign_sub(learning_rate*dy_dl)
        self.k.assign_sub(learning_rate*dy_dk)
        self.x0.assign_sub(learning_rate*dy_dx0)

    def train(self, x, y, epochs, learning_rate=0.01):
        for i in range(epochs):
            # print("Epoch: ", i)

            self.update(x, y, learning_rate)

