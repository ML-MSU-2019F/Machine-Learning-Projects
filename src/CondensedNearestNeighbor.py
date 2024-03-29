from KNearestNeighbor import KNearestNeighbor
import numpy
class CondensedNearestNeighbor(KNearestNeighbor):
    data = None
    data_set = None
    def run(self,data_set,regression):
        self.data_set = data_set
        original_data = self.data_set.data[0:]
        # init the condensed set to nothing
        condensed_set = []
        # say our last accuracy was 0
        last_accuracy = 0
        print("Accuracy on iteration {} {:2.2f}".format(0, (last_accuracy) * 100))
        # doing batch removal
        last_data = None
        iterations = 0
        # bootstrap process by adding a single point
        original_point = original_data.pop()
        condensed_set.append(original_point)
        degraded = False
        done = False
        accuracy = None
        # stop at 20 iterations regardless
        while iterations != 21:
            # set last data
            last_data = condensed_set[0:]
            # add to iterations
            iterations+=1
            # maintain a list of points to add
            add_list = []
            # set initial index
            index = 0
            while True:
                # empty set, we should end
                if len(original_data) is 0:
                    # is empty
                    done = True
                    break
                # check accuracy, if is wrong, add it to condensed set
                one = original_data[index]
                all = condensed_set
                closest = self.getNearestNeighbor(one,all,1)
                if(self.classify(one[self.data_set.target_location],closest) is 0):
                    add_list.append(index)
                index += 1
                # if we don't add any, we are done
                if len(add_list) is 0:
                    done = True
                    break
                # if we reach our batch of 50, break to add those points
                if (len(add_list) == 50):
                    break
            # add and keep track of what we are adding
            add_offset = 0
            for i in add_list:
                condensed_set.append(original_data[i - add_offset])
                del original_data[i-add_offset]
                add_offset += 1
            # get accuracy
            result = self.runTenFold(condensed_set)
            accuracy = result[1] / result[0]
            print("Condensed Size: {}".format(result[0]))
            print("Accuracy on iteration {} {:2.2f}".format(iterations, (accuracy) * 100))
            if done:
                break
        # finished, set final_data
        print("Set stopped growing in size, accuracy: {:2.2f}".format((accuracy) * 100))
        self.final_data = last_data
