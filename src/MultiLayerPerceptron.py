from Algorithm import Algorithm
from MLPNode import Node
from Layer import Layer
from DataSet import DataSet
import math
import numpy
import pandas
import multiprocessing
import time
import matplotlib.pyplot as plt
plt.close('all')


class FeedForwardNetwork(Algorithm):

    def __init__(self, inputs: int, hidden_layers: int, nodes_by_layers: list, outputs: int, learning_rate, momentum_constant):
        self.layers = []
        self.inputs = inputs
        self.hidden_layers = hidden_layers
        self.nodes_by_layers = nodes_by_layers
        self.outputs = outputs
        self.learning_rate = learning_rate
        self.momentum_constant = momentum_constant
        self.regression = False
        print("Constructing Neural Net")
        self.constructInputLayer()
        self.constructHiddenLayers()
        self.constructOutputLayer()
        self.link_layers()
        self.initializeWeights()
        print("Neural Net constructed")

    def resetNetwork(self):
        self.layers = []
        self.constructInputLayer()
        self.constructHiddenLayers()
        self.constructOutputLayer()
        self.link_layers()
        self.initializeWeights()

    # set to false for now, but will change later
    def run(self, data_set: DataSet, regression=False):
        self.data_set = data_set
        self.regression = regression
        data_set.makeRandomMap(data_set.data, 5)
        total_accuracies = []
        epoch_converged = []
        time_took = []
        for i in range(0, 5):
            print("Starting fold {}".format(i))
            test_set = data_set.getRandomMap(i)
            data = data_set.getAllRandomExcept(i)
            epoch_error = []
            test_set_errors = []
            headless_data = data_set.separateClassFromData(data=data)
            iter = 0
            start = time.time()
            # training
            increased = 0
            while True:
                iter += 1
                print("Epoch: {}".format(iter))
                # input values into the input layer
                for index in range(0, len(headless_data)):
                    line = headless_data[index]
                    if len(line) != self.inputs:
                        print("Error, we need to have as many inputs as features")
                        print("We have {} features, but only {} layers".format(len(line), self.inputs))
                        exit(1)
                    self.runForward(line)
                    if not self.regression:
                        results, max_value, max_index = self.getResults()
                        actual_class = data[index][self.data_set.target_location]
                        distance = self.getDistanceFromWantedResult(results, actual_class)
                        for i in range(0, len(results)):
                            self.layers[len(self.layers)-1].output = results[i]
                        # square it for MSE/Cross Entropy error
                        squared_distance = 0.5 * numpy.power(distance, 2)
                        epoch_error.append(numpy.sum(squared_distance)/len(squared_distance))
                        self.runBackprop(-distance)
                    else:
                        output = self.layers[len(self.layers) - 1].nodes[0].output
                        actual_value = data[index][self.data_set.target_location]
                        distance = actual_value - output
                        # square it for MSE/Cross Entropy error
                        squared_distance = numpy.power(distance, 2)
                        epoch_error.append(numpy.sum(squared_distance))
                        self.runBackprop([-distance])
                latest_accuracy = self.checkAccuracyAgainstSet(test_set, self.regression)
                print(latest_accuracy)
                error_length = len(test_set_errors)
                if len(test_set_errors) > 0:
                    # .001 is arbitrary padding to prevent not stopping
                    if test_set_errors[error_length - 1] - .0001 <= latest_accuracy:
                        increased += 1
                        if increased == 2:
                            print("Test set error converged")
                            epoch_converged.append(iter)
                            break
                    else:
                        increased = 0
                        test_set_errors.append(latest_accuracy)
                else:
                    test_set_errors.append(latest_accuracy)
            end = time.time()
            time_took.append(end-start)
            # get final accuracy and append it to test set
            total_accuracies.append(test_set_errors[len(test_set_errors)-1])
            self.resetNetwork()
        print("Average Time: {}".format(numpy.mean(time_took)))
        print("Average Error: {}".format(numpy.mean(total_accuracies)))
        print("Average Epoch End: {}".format(numpy.mean(epoch_converged)))
        ts = pandas.Series(total_accuracies)
        ts.plot()
        plt.show()
        tse = pandas.Series(epoch_converged)
        tse_plot = tse.plot(title="Forest Fire Training, 2 Hidden Layers")
        tse_plot.set(xlabel='Epoch', ylabel='MSE Accuracy')
        plt.show()

    def getDistanceFromWantedResult(self, results, actual_class):
        wanted_results = []
        output_layer_index = self.data_set.ordered_classes[actual_class]
        # make matrix of what we want, which will be the wanted class being 1, the unwanted being zero
        # ex, class 2 is what we want and we have 5 classes: [0,0,1,0,0] (this assumes softmax is being used)
        for i in range(0, len(results)):
            if output_layer_index is i:
                wanted_results.append(1)
            else:
                wanted_results.append(0)
        # get the distance of what we wanted from what we got
        distance = numpy.subtract(wanted_results, results)
        return distance

    def checkAccuracyAgainstSet(self, test_set, regression):
        headless = self.data_set.separateClassFromData(data=test_set)
        if not regression:
            accuracy = 0

            for index in range(0, len(headless)):
                self.runForward(headless[index])
                results, max_value, max_index = self.getResults()
                class_actual = test_set[index][self.data_set.target_location]
                distance = self.getDistanceFromWantedResult(results, class_actual)
                accuracy += numpy.sum(.5*numpy.power(distance, 2))
            return accuracy/len(headless)
        else:
            mse_sum = 0
            for index in range(0, len(headless)):
                self.runForward(headless[index])
                output = self.layers[len(self.layers) - 1].nodes[0].output
                actual = test_set[index][self.data_set.target_location]
                mse = numpy.power(actual-output, 2)
                mse_sum += mse
            return mse_sum/len(test_set)

    def runForward(self, line):
        for i in range(0, len(line)):
            # input values into first layer
            self.layers[0].nodes[i].overrideInput(line[i])
        # go though each layer, running based on set input
        for i in range(0, len(self.layers)):
            for j in range(0, len(self.layers[i].nodes)):
                self.layers[i].nodes[j].run()

    def runBackprop(self, distance):
        # manually set output in output layer to the derived MSE distance
        for i in range(0, len(self.layers[len(self.layers) - 1].nodes)):
            self.layers[len(self.layers) - 1].nodes[i].error = distance[i]
        for i in range(len(self.layers) - 2, -1, -1):
            for j in range(0, len(self.layers[i].nodes)):
                self.layers[i].nodes[j].backprop()

    def runSetOfNodes(self, nodes):
        for node in nodes:
            node.run()

    def getResults(self):
        layer_length = len(self.layers)
        max_value = -math.inf  # our found max weight
        max_index = None  # our found max index
        results = []  # the results, localized from the final row
        # iterate through nodes in the last row
        for i in range(0, len(self.layers[layer_length - 1].nodes)):
            # get value of single node
            value = self.layers[layer_length - 1].nodes[i].output
            # append value to local result
            results.append(value)
            # if greater than current max, assign to variables index, and new weight
            if value > max_value:
                max_index = i
                max_value = value
        # turn results into soft_max
        exp_results = numpy.exp(results)
        soft_max_sum = numpy.sum(exp_results)
        # results = exp_results/soft_max_sum
        # set last layer results to be the softmax sum
        return results, max_value, max_index

    def link_layers(self):
        for i in range(0,len(self.layers)):
            # is not last layer
            if i+1 is not len(self.layers):
                self.layers[i].next_layer = self.layers[i+1]
            # is not first layer
            if i-1 is not -1:
                self.layers[i].prev_layer = self.layers[i-1]

    def inputData(self, input):
        if len(input) is not self.inputs:
            print("Problem occurred, inputs specified: {}, inputs given: {}".format(self.inputs, len(input)))
            exit(1)

    def initializeWeights(self):
        # iterate through all but last layer
        for i in range(0, len(self.layers)):
            # initialize weights on all nodes
            for j in range(0, len(self.layers[i].nodes)):
                self.layers[i].nodes[j].initWeights(-0.3, 0.3)

    def constructInputLayer(self):
        layer = Layer(len(self.layers))
        for i in range(0, self.inputs):
            node_i = Node(index=i, learning_rate=self.learning_rate, momentum_constant=self.momentum_constant)
            node_i.setTopNetwork(self)
            node_i.setLayer(layer)
            layer.addNode(node_i)
        node_bias = Node(index=self.inputs, learning_rate=self.learning_rate, momentum_constant=self.momentum_constant)
        node_bias.setTopNetwork(self)
        node_bias.setLayer(layer)
        node_bias.overrideOutput(1)
        layer.addNode(node_bias)
        layer.setInputLayer(True)
        self.layers.append(layer)


    def constructOutputLayer(self):
        layer = Layer(len(self.layers))
        for i in range(0, self.outputs):
            node_i = Node(index=i, learning_rate=self.learning_rate, momentum_constant=self.momentum_constant)
            node_i.setTopNetwork(self)
            node_i.setLayer(layer)
            layer.addNode(node_i)
        layer.setOutputLayer(True)
        self.layers.append(layer)

    def constructHiddenLayers(self):
        if len(self.nodes_by_layers) != self.hidden_layers:
            print("Problem occurred: Cannot have unspecified hidden nodes")
            print("\tSpecified nodes in layers: {}".format(len(self.nodes_by_layers)))
            print("\tHidden Layers: {}".format(self.hidden_layers))
            exit(1)

        for i in range(0, self.hidden_layers):
            layer = Layer(len(self.layers))
            for j in range(0, self.nodes_by_layers[i]):
                node_j = Node(index=j, learning_rate=self.learning_rate, momentum_constant=self.momentum_constant)
                node_j.setTopNetwork(self)
                node_j.setLayer(layer)
                layer.addNode(node_j)
            node_bias = Node(index=self.nodes_by_layers[i], learning_rate=self.learning_rate,
                             momentum_constant=self.momentum_constant)
            node_bias.overrideOutput(1)
            node_bias.setTopNetwork(self)
            node_bias.setLayer(layer)
            layer.addNode(node_bias)
            self.layers.append(layer)