from framework import *
from rand import *

from enum import Enum
import numpy as np
import copy
from queue import PriorityQueue, Queue


class SickType(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3

class SickHuman:
    def __init__(self, sick_type):
        self.sick_type = sick_type
    
    # implement < so type 1 is highest priority
    def __lt__(self, other):
        if self.sick_type == SickType.FIRST and other.sick_type != SickType.FIRST:
            return True
        else:
            return False


class HumanInput(Create):
    # next element is expected to be Hospital
    def __init__(self, name):
        super().__init__(0, name)
        self.sick_type_distribution = {
            SickType.FIRST: 0.5,
            SickType.SECOND: 0.1,
            SickType.THIRD: 0.4
        }

        self.sick_type_delay = {
            SickType.FIRST: 15,
            SickType.SECOND: 40,
            SickType.THIRD: 30
        }

        self.sick_human_to_send = self._generate_next_sick()
        self.tnext = self.tcurr + self.sick_type_delay[self.sick_human_to_send.sick_type]

    def out_act(self):
        self.quantity += 1

        sick_human = self._generate_next_sick()
        self.tnext = self.tcurr + self.sick_type_delay[sick_human.sick_type]

        if len(self.next_elements) > 1:
            raise Exception('HumanInput has to have exactly 1 next element')
        
        self.next_elements[0].in_act(copy.deepcopy(self.sick_human_to_send))
        self.sick_human_to_send = sick_human

    def _generate_next_sick(self) -> SickHuman:
        # generate next sick dies to distribution
        sick_type = np.random.choice(np.arange(1, 4), p=[
            self.sick_type_distribution[SickType.FIRST],
            self.sick_type_distribution[SickType.SECOND],
            self.sick_type_distribution[SickType.THIRD]
        ])

        return SickHuman(SickType(sick_type))


class GeneralSickProcessor(Process):
    def __init__(self, delay_func, name, maxqueue, devices_amount = 1):
        super().__init__(None, name, maxqueue, devices_amount, 0)
        self.sick_human = None
        self.queue = Queue(maxqueue)
        self.delay_func = delay_func

    def do_statistics(self, delta):
        self.meanQueue += (self.queue.qsize() * delta)        

    def print_info(self):
        print(f'Name: {self.name}, \
              Quantity: {self.quantity}, \
              Queue: {self.queue.qsize()}, \
              Maxqueue: {self.maxqueue}, \
              Failure: {self.failure}, \
              MeanQueue: {((self.meanQueue/self.tcurr) if self.tcurr != 0.0 else (0.0)):.2f}, \
              Failure probability: {((self.failure / (self.quantity + self.failure)) if (self.quantity + self.failure) > 0 else 0.0):.2f}')
        for device in self.devices:
            print(f'\tDevice: {device.name}, \
                  tnext: {device.tnext:.2f}, \
                  state: {device.state}')
    
    def can_accept(self):
        return self.queue.full() == False

    def put_in_queue(self, sick_human):
        raise Exception('Not implemented')

    def get_delay_specific(self, sick_human = None):
        raise Exception('Not implemented')

    def in_act(self, sick_human):
        if self.get_free_device() is not None:
            device = self.get_free_device()
            device.state = State.BUSY
            device.tnext = self.tcurr + self.get_delay_specific(sick_human)
            device.data = sick_human
        else:
            if self.queue.qsize() < self.maxqueue:
                self.put_in_queue(sick_human)
            else:
                self.failure += 1

    def out_act(self):
        self.quantity += 1

        min_dev = self.get_min_device()
        
        min_dev.state = State.FREE
        min_dev.tnext = float(sys.maxsize)
        self.data_to_send = copy.deepcopy(min_dev.data)
        min_dev.data = None

        if self.queue.qsize() > 0:
            element_to_attach = self.queue.get()

            free_device = self.get_free_device()
            free_device.state = State.BUSY
            free_device.tnext = self.tcurr + self.get_delay_specific(element_to_attach)
            free_device.data = element_to_attach

        # after super() call in child use self.data_to_send to send where needed
    


class Hospital(GeneralSickProcessor):
    def __init__(self, delay_func, name, maxqueue):
        super().__init__(delay_func, name, maxqueue, 2)
        self.queue = PriorityQueue(maxqueue)

    def put_in_queue(self, sick_human):
        if sick_human.sick_type == SickType.FIRST:
            self.queue.put(sick_human)
        else:
            self.queue.put(sick_human)

    def get_delay_specific(self, sick_human = None):
        return self.delay_func()

    def __call_in_act_first_type_in_smo2_other_in_lab(self):
        if len(self.next_elements) != 2:
            raise Exception('Hospital has to have exactly 2 next elements')

        try:
            if self.data_to_send.sick_type == SickType.FIRST:
                self.next_elements[0].in_act(copy.deepcopy(self.data_to_send))
            else:
                self.next_elements[1].in_act(copy.deepcopy(self.data_to_send))
        except:
            raise Exception('Hospital must use Room and LabReg as next elements')

    def out_act(self):
        super().out_act()

        self.__call_in_act_first_type_in_smo2_other_in_lab()


class Room(GeneralSickProcessor): # post hospital room
    def __init__(self, delay_func, name, maxqueue):
        super().__init__(delay_func, name, maxqueue, 3)

    def put_in_queue(self, sick_human):
        self.queue.put(sick_human)

    def get_delay_specific(self, sick_human = None):
        return self.delay_func()

    def out_act(self):
        super().out_act()
        # no in act because it is last element


class LabReg(GeneralSickProcessor):
    def __init__(self, delay_func, name, maxqueue):
        super().__init__(delay_func, name, maxqueue, 1)
    
    def put_in_queue(self, sick_human):
        self.queue.put(sick_human)

    def get_delay_specific(self, sick_human = None):
        return self.delay_func()
    
    def out_act(self):
        super().out_act()
        
        if len(self.next_elements) != 1:
            raise Exception('LabReg has to have exactly 1 next element')
        
        # send to Lab
        self.next_elements[0].in_act(copy.deepcopy(self.data_to_send))

class Lab(GeneralSickProcessor):
    def __init__(self, delay_func, name, maxqueue):
        super().__init__(delay_func, name, maxqueue, 2)
    
    def put_in_queue(self, sick_human):
        self.queue.put(sick_human)

    def get_delay_specific(self, sick_human = None):
        return self.delay_func()
    
    def __call_in_act_for_half_probability(self):
        if len(self.next_elements) != 1:
            raise Exception('Lab has to have exactly 1 next element')
        
        if np.random.choice([True, False]):
            sick_to_change = copy.deepcopy(self.data_to_send)
            sick_to_change.sick_type = SickType.FIRST
            self.next_elements[0].in_act(sick_to_change)

    def out_act(self):
        super().out_act()
        
        if len(self.next_elements) != 1:
            raise Exception('LabReg has to have exactly 1 next element')
        
        # send to PathToHospital
        self.__call_in_act_for_half_probability()

class PathToHospital(GeneralSickProcessor):
    def __init__(self, delay_func, name, maxqueue, devices_amount=1):
        super().__init__(delay_func, name, maxqueue, devices_amount)

    def put_in_queue(self, sick_human):
        self.queue.put(sick_human)
    
    def get_delay_specific(self, sick_human = None):
        return self.delay_func()
    
    def out_act(self):
        super().out_act()
        
        if len(self.next_elements) != 1:
            raise Exception('PathToHospital has to have exactly 1 next element')
        
        # send to Hospital
        self.next_elements[0].in_act(copy.deepcopy(self.data_to_send))


if __name__ == '__main__':
    human_input = HumanInput('HumanInput')

    hospital = Hospital(lambda: Rand.exp(15), 'Hospital', 10)
    room = Room(lambda: Rand.uniform(3, 8), 'Room', 10)
    lab_reg = LabReg(lambda: Rand.erlang(4.5, 3), 'LabReg', 10)
    lab = Lab(lambda: Rand.erlang(4, 2), 'Lab', 10)
    path_to_hospital = PathToHospital(lambda: Rand.uniform(2, 5), 'PathToHospital', 10)

    human_input.next_elements = [hospital]
    hospital.next_elements = [room, lab_reg]
    room.next_elements = []
    lab_reg.next_elements = [lab]
    lab.next_elements = [path_to_hospital]
    path_to_hospital.next_elements = [hospital]

    model = Model([human_input, hospital, room, lab_reg, lab, path_to_hospital], debug=False)
    model.simulate(1000)
