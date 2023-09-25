import time
import random
import numpy as np
from enum import Enum
import sys

class State(Enum):
    FREE = 0
    BUSY = 1


class Element:
    def __init__(self, delay):
        self.name = ''
        self.tnext = 0.0
        self.tcurr = 0.0
        self.delayMean = delay
        self.state = State.FREE
        self.next_element = None
        self.id = 0
        self.quantity = 0
    
    def __init__(self, delay, name):
        self.name = name
        self.tnext = 0.0
        self.tcurr = 0.0
        self.delayMean = delay
        self.state = State.FREE
        self.next_element = None
        self.id = 0
        self.quantity = 0
    
    def set_next_element(self, element):
        self.next_element = element

    def in_act(self):
        pass
    
    def out_act(self):
        self.quantity += 1
    
    def print_info(self):
        print(f'Name: {self.name}, \
              Quantity: {self.quantity}, \
              State: {self.state}, \
              tnext: {self.tnext:.2f}, \
              tcurr: {self.tcurr:.2f}, \
              delayMean: {self.delayMean:.2f}')
    
    def do_statistics(self, delta):
        raise NotImplementedError()


class Create(Element):
    def __init__(self, delay, name):
        super().__init__(delay, name)
    
    def out_act(self):
        super().out_act()
        self.tnext = self.tcurr + self.delayMean

        if self.next_element is not None:
            self.next_element.in_act()
    
    def do_statistics(self, delta):
        pass


class Process(Element):
    def __init__(self, delay, name):
        super().__init__(delay, name)
        self.queue = 0
        self.maxqueue = sys.maxsize
        self.failure = 0
        self.meanQueue = 0
    
    def __init__(self, delay, name, maxqueue):
        super().__init__(delay, name)
        self.queue = 0
        self.maxqueue = maxqueue
        self.failure = 0
        self.meanQueue = 0

    def in_act(self):
        super().in_act()
        if self.state == State.FREE:
            self.state = State.BUSY
            self.tnext = self.tcurr + self.delayMean
        else:
            if self.queue < self.maxqueue:
                self.queue += 1
            else:
                self.failure += 1
    
    def out_act(self):
        super().out_act()
        self.tnext = float(sys.maxsize)
        self.state = State.FREE

        if self.queue > 0:
            self.queue -= 1
            self.state = State.BUSY
            self.tnext = self.tcurr + self.delayMean

        if self.next_element is not None:
            self.next_element.in_act()

    def do_statistics(self, delta):
        self.meanQueue += (self.queue * delta)
    
    def print_info(self):
        super().print_info()
        print(f'Queue: {self.queue}, \
              Maxqueue: {self.maxqueue}, \
              Failure: {self.failure}, \
              MeanQueue: {((self.meanQueue/self.tcurr) if self.tcurr != 0.0 else (0.0)):.2f}, \
              Failure probability: {((self.failure / (self.quantity + self.failure)) if (self.quantity + self.failure) > 0 else 0.0):.2f}')


class Model:
    def __init__(self, elements):
        self.elements = elements
        self.delta = 0.0
        self.tnext = 0.0
        self.tcurr = 0.0
        self.curr_element = None
    
    def simulate(self, time_modeling):
        i = 0
        while self.tcurr < time_modeling:
            self.tnext = float(sys.maxsize)
            for element in self.elements:
                if element.tnext < self.tnext:
                    self.tnext = element.tnext
                    self.curr_element = element
            
            print(f'Next event at {self.tnext:.2f} time in {self.curr_element.name}')

            
            for element in self.elements:
                element.do_statistics(self.tnext - self.tcurr)
            
            self.tcurr = self.tnext
            self.curr_element.tcurr = self.tcurr
            for element in self.elements:
                element.tcurr = self.tcurr

            self.curr_element.out_act()
            for element in self.elements:
                if element.tnext == self.tcurr:
                    element.out_act()

            self.print_result(i)
            i += 1

        print('\n\nModeling finished!\n')
        self.print_result()
    
    def print_result(self, iteration=None):
        if iteration is not None:
            print('\n\n')
            print(f'Iretation: {iteration}')
        for element in self.elements:
            element.print_info()


def main():
    create = Create(0.7, 'Create')

    process1 = Process(1.3, 'Process1', 10)
    create.set_next_element(process1)

    process2 = Process(0.8, 'Process2', 10)
    process1.set_next_element(process2)    


    model = Model([create, process1, process2])
    model.simulate(10000)


if __name__ == "__main__":
    main()
