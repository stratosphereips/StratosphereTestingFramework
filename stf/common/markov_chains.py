# This file is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# Library to compute some markov chain functions for the Stratosphere Project. We created them because pykov lacked the second order markov chains

import math
import sys

class Matrix(dict):
    """ The basic matrix object """
    def __init__(self, *args, **kw):
        super(Matrix,self).__init__(*args, **kw)
        self.itemlist = super(Matrix,self).keys()

    def set_init_vector(self, init_vector):
        self.init_vector = init_vector

    def walk_probability(self, states):
        """ Compute the probability of generating these states using ourselves """
        try:
            prob = 0
            index = 0
            while index < len(states) - 1 and len(states) > 1:
                statestuple = (states[index], states[index + 1])
                try:
                    prob12 = float(self[statestuple])
                except IndexError:
                    prob12 = float('-inf')
                    prob = float('-inf')
                    break
                prob += math.log(prob12)
                index += 1
            #print 'Final Prob: {}'.format(prob)
            return prob
        except Exception as err:
            print type(err)
            print err.args
            print err
            sys.exit(-1)


def maximum_likelihood_probabilities(states, order=1):
    """ Our own second order Markov Chain implementation """
    initial_matrix = {}
    initial_vector = {}
    total_transitions = 0
    amount_of_states = len(states)
    #print 'Receiving {} states to compute the Markov Matrix of {} order'.format(amount_of_states, order)
    # 1st order
    if order == 1:
        # Create matrix
        index = 0
        while index < amount_of_states:
            state1 = states[index]
            try:
                state2 = states[index + 1]
            except IndexError:
                # The last state is alone. There is no transaction, forget about it.
                break
            try:
                temp = initial_matrix[state1]
            except KeyError:
                # First time there is a transition FROM state1
                initial_matrix[state1] = {}
                initial_vector[state1] = 0
            try:
                value = initial_matrix[state1][state2]
                initial_matrix[state1][state2] = value + 1
            except KeyError:
                # First time there is a transition FROM state 1 to state2
                initial_matrix[state1][state2] = 1
            initial_vector[state1] += 1
            total_transitions += 1
            # Move along
            index += 1
        # Normalize using the initial vector
        matrix = Matrix()
        init_vector = {}
        for state1 in initial_matrix:
            # Create the init vector
            init_vector[state1] = initial_vector[state1] / float(total_transitions)
            for state2 in initial_matrix[state1]:
                value = initial_matrix[state1][state2]
                initial_matrix[state1][state2] = value / float(initial_vector[state1])
                # Change the style of the matrix
                matrix[(state1,state2)] = initial_matrix[state1][state2]
        matrix.set_init_vector(init_vector)
        #print init_vector
        #for value in matrix:
        #    print value, matrix[value]
    return (init_vector, matrix)


