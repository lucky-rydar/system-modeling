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

    def get_priority(self):
        raise NotImplementedError()

    def can_accept(self):
        raise NotImplementedError()
    
    def put_in_queue(self, element):
        raise NotImplementedError()

    def get_mean_delay(self):
        raise NotImplementedError()

    def get_next_element_with_highest_priority(self):
        max_priority = float(sys.maxsize)
        ret_element = None
        for element in self.next_elements:
            if element.get_priority() < max_priority and element.can_accept():
                max_priority = element.get_priority()
                ret_element = element
        return ret_element
    
    def in_act_for_highest_priority_and_acceptable(self):
        el = self.get_next_element_with_highest_priority()
        if el is None:
            if len(self.next_elements) > 0:
                self.next_elements[0].in_act()
        else:
            el.in_act()


class Create(Element):
    def __init__(self, delay, name):
        super().__init__(delay, name)
    
    def out_act(self):
        super().out_act()
        self.tnext = self.tcurr + self.delayMean

        self.in_act_for_highest_priority_and_acceptable()
    
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
    
    def get_priority(self):
        raise NotImplementedError('Create element has no priority')

    def can_accept(self):
        raise NotImplementedError('Create element cant accept')


class Device:
    def __init__(self, name):
        self.name = name
        self.tnext = float(sys.maxsize)
        self.state = State.FREE
        
        self.data = None


class Process(Element):
    def __init__(self, delay, name, maxqueue, devices_amount = 1, priority = 0):
        super().__init__(delay, name)
        self.queue = 0
        self.maxqueue = maxqueue
        self.failure = 0
        self.meanQueue = 0
        self.priority = priority

        self.devices = []
        self.devices_amount = devices_amount
        for i in range(devices_amount):
            self.devices.append(Device(f'Device({i})'))

    def get_priority(self):
        return self.priority
    
    def can_accept(self):
        return self.queue < self.maxqueue

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

        self.in_act_for_highest_priority_and_acceptable()

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
    def __init__(self, elements, debug = False):
        self.elements = elements
        self.delta = 0.0
        self.tnext = 0.0
        self.tcurr = 0.0
        self.curr_element = None
        self.debug = debug
    
    def simulate(self, time_modeling, logging = True):
        i = 0
        while self.tcurr < time_modeling:
            self.tnext = float(sys.maxsize)
            for element in self.elements:
                if element.get_tnext() < self.tnext:
                    self.tnext = element.get_tnext()
                    self.curr_element = element
            
            if logging:
                print(f'Next event at {self.tnext:.2f} time in {self.curr_element.name}')

            for element in self.elements:
                element.do_statistics(self.tnext - self.tcurr)
            
            self.tcurr = self.tnext
            for element in self.elements:
                element.tcurr = self.tcurr

            for element in self.elements:
                element.out_act_all(self.tcurr)

            if self.debug:
                self.print_result(i)
                time.sleep(1)
            i += 1

        if logging:
            print('\n\nModeling finished!\n')
            self.print_result()
    
    def print_result(self, iteration=None):
        if iteration is not None:
            print('\n\n')
            print(f'Iretation: {iteration}, tcurr: {self.tcurr:.2f}')
        for element in self.elements:
            element.print_info()
