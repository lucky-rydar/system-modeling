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
        self.next_elements = []
        self.id = 0
        self.quantity = 0
    
    def __init__(self, delay, name):
        self.name = name
        self.tnext = 0.0
        self.tcurr = 0.0
        self.delayMean = delay
        self.state = State.FREE
        self.next_elements = []
        self.id = 0
        self.quantity = 0

    def in_act(self):
        pass
    
    def out_act(self):
        self.quantity += 1
    
    def out_act_all(self, tcurr_next = None):
        pass
    
    def print_info(self):
        print(f'Name: {self.name}, \
              Quantity: {self.quantity}, \
              tnext: {self.tnext:.2f}, \
              tcurr: {self.tcurr:.2f}, \
              delayMean: {self.delayMean:.2f}')
    
    def do_statistics(self, delta):
        raise NotImplementedError()

    def get_tnext(self):
        raise NotImplementedError()


class Create(Element):
    def __init__(self, delay, name):
        super().__init__(delay, name)
    
    def out_act(self):
        super().out_act()
        self.tnext = self.tcurr + self.delayMean

        for element in self.next_elements:
            element.in_act()
    
    def out_act_all(self, tcurr_next = None):
        if self.tnext == tcurr_next:
            self.out_act()

    def do_statistics(self, delta):
        pass

    def get_tnext(self):
        return self.tnext

    def print_info(self):
        super().print_info()
        print(f'\tState: {self.state}')


class Device:
    def __init__(self, name):
        self.name = name
        self.tnext = float(sys.maxsize)
        self.state = State.FREE


class Process(Element):
    def __init__(self, delay, name, maxqueue, devices_amount = 1):
        super().__init__(delay, name)
        self.queue = 0
        self.maxqueue = maxqueue
        self.failure = 0
        self.meanQueue = 0

        self.devices = []
        self.devices_amount = devices_amount
        for i in range(devices_amount):
            self.devices.append(Device(f'Device({i})'))

    def get_free_device(self):
        for device in self.devices:
            if device.state == State.FREE:
                return device
        return None

    def in_act(self):
        super().in_act()
        if self.get_free_device() is not None:
            device = self.get_free_device()
            device.state = State.BUSY
            device.tnext = self.tcurr + self.delayMean
        else:
            if self.queue < self.maxqueue:
                self.queue += 1
            else:
                self.failure += 1
    
    def get_min_device(self):
        tmp_tnext = float(sys.maxsize)
        ret_device = None
        for device in self.devices:
            if device.tnext < tmp_tnext:
                tmp_tnext = device.tnext
                ret_device = device
        return ret_device

    def out_act_all(self, tcurr_next=None):
        for device in self.devices:
            if device.tnext == tcurr_next:
                self.out_act()


    def out_act(self):
        super().out_act()

        min_dev = self.get_min_device()
        
        min_dev.state = State.FREE
        min_dev.tnext = float(sys.maxsize)
        if self.queue > 0:
            self.queue -= 1
            free_device = self.get_free_device()
            free_device.state = State.BUSY
            free_device.tnext = self.tcurr + self.delayMean

        for element in self.next_elements:
            element.in_act()

    def do_statistics(self, delta):
        self.meanQueue += (self.queue * delta)
    
    def get_tnext(self):
        tmp_tnext = float(sys.maxsize)
        for device in self.devices:
            if device.tnext < tmp_tnext:
                tmp_tnext = device.tnext
        return tmp_tnext
    
    def print_info(self):
        super().print_info()
        print(f'Queue: {self.queue}, \
              Maxqueue: {self.maxqueue}, \
              Failure: {self.failure}, \
              MeanQueue: {((self.meanQueue/self.tcurr) if self.tcurr != 0.0 else (0.0)):.2f}, \
              Failure probability: {((self.failure / (self.quantity + self.failure)) if (self.quantity + self.failure) > 0 else 0.0):.2f}')
        for device in self.devices:
            print(f'\tDevice: {device.name}, \
                  tnext: {device.tnext:.2f}, \
                  state: {device.state}')


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
                if element.get_tnext() < self.tnext:
                    self.tnext = element.get_tnext()
                    self.curr_element = element
            
            print(f'Next event at {self.tnext:.2f} time in {self.curr_element.name}')

            for element in self.elements:
                element.do_statistics(self.tnext - self.tcurr)
            
            self.tcurr = self.tnext
            for element in self.elements:
                element.tcurr = self.tcurr

            for element in self.elements:
                element.out_act_all(self.tcurr)

            # self.print_result(i) # debug
            i += 1

        print('\n\nModeling finished!\n')
        self.print_result()
    
    def print_result(self, iteration=None):
        if iteration is not None:
            print('\n\n')
            print(f'Iretation: {iteration}, tcurr: {self.tcurr:.2f}')
        for element in self.elements:
            element.print_info()


def main():
    create = Create(0.2, 'Create')

    process1 = Process(1, 'Process1', 10, 2)
    create.next_elements = [process1]

    process2 = Process(0.6, 'Process2', 10, 1)
    process3 = Process(0.6, 'Process3', 10, 1)
    process1.next_elements = [process2, process3]

    # process2.next_elements = [process1]

    model = Model([create, process1, process2, process3])
    model.simulate(1000)


if __name__ == "__main__":
    main()
