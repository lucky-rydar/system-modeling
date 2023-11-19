from framework import *
from rand import *

# The task is to:
# - calculate average time of TechProcessGenerator to be in SLOW mode
# - average failures amount during turning resesrve EOM on

class TechProcessGenerator(Create):
    class Mode(Enum):
        NORMAL = 0
        SLOW = 1

    def __init__(self, name):
        super().__init__(None, name)
        #self.name = name
        self.working_mode = TechProcessGenerator.Mode.NORMAL

        self.modes = {
            TechProcessGenerator.Mode.NORMAL: (8, 12),
            TechProcessGenerator.Mode.SLOW: (16, 24)
        }

        self.received_control_signal = False

        self.main_eom = None
        self.reserve_eom = None
    
    def set_working_mode(self, mode):
        self.working_mode = mode

    def out_act(self):
        self.quantity += 1

        if not self.received_control_signal:
            self.working_mode = TechProcessGenerator.Mode.SLOW
        else:
            self.working_mode = TechProcessGenerator.Mode.NORMAL
            self.received_control_signal = False

        distribution = self.modes[self.working_mode]
        self.tnext = self.tcurr + Rand.uniform(distribution[0], distribution[1])

        if self.main_eom.is_shutdown:
            self.reserve_eom.in_act()
        else:
            self.main_eom.in_act()

    def send_element_proceeded(self):
        self.received_control_signal = True

    def print_info(self):
        print(f'Name: {self.name}, \
                Quantity: {self.quantity}, \
                tnext: {self.tnext:.2f}, \
                tcurr: {self.tcurr:.2f}, \
                working_mode: {self.working_mode}')


class MainEOM(Process):
    def __init__(self, delay, name, reserve_eom, generator):
        super().__init__(delay, name, None, 1, 0)

        self.shutdown_delay_f = lambda: Rand.uniform(270, 330)
        self.recovery_delay = 100
        self.i_am_working_delay = 30
        self.is_shutdown = False

        self.tnext_shutdown = self.tcurr + self.shutdown_delay_f()
        self.tnext_recovery = float(sys.maxsize)
        self.tnext_i_am_working = float(sys.maxsize)

        if not isinstance(reserve_eom, ReservEOM):
            raise TypeError('Reserve EOM must be an instance of ReservEOM class')
        self.reserve_eom = reserve_eom

        if not isinstance(generator, TechProcessGenerator):
            raise TypeError('Generator must be an instance of TechProcessGenerator class')
        self.generator = generator

    def get_tnext(self):
        tmp_tnext = float(sys.maxsize)
        for device in self.devices:
            if device.tnext < tmp_tnext:
                tmp_tnext = device.tnext
        
        return min(self.tnext_shutdown, self.tnext_recovery, tmp_tnext, self.tnext_i_am_working)

    def in_act(self):
        if self.get_free_device() is not None:
            device = self.get_free_device()
            device.state = State.BUSY
            device.tnext = self.tcurr + self.delayMean
        else:
            self.failure += 1

    def send_control_signal_to_reserve_EOM(self):
        self.reserve_eom.main_is_alive()

    def inform_generator_element_proceeded(self):
        self.generator.send_element_proceeded()

    def out_act_all(self, tcurr_next=None):
        super().out_act_all(tcurr_next)
        if self.tnext_shutdown == tcurr_next:
            self.out_act()
        if self.tnext_i_am_working == tcurr_next:
            self.out_act()
        if self.tnext_recovery == tcurr_next:
            self.out_act()

    def out_act(self):
        tmp_tnext = self.get_tnext()
        if tmp_tnext == self.tnext_shutdown:
            self.is_shutdown = True
            self.tnext_recovery = self.tcurr + self.recovery_delay
            self.tnext_shutdown = float(sys.maxsize)
            self.tnext_i_am_working = float(sys.maxsize)
            
            self.devices[0].tnext = float(sys.maxsize)

            # expected to be one device
            min_dev = self.get_min_device()
            if min_dev is not None:
                min_dev.state = State.FREE
                min_dev.tnext = float(sys.maxsize)

        elif tmp_tnext == self.tnext_recovery:
            self.is_shutdown = False
            self.tnext_shutdown = self.tcurr + self.shutdown_delay_f()
            self.tnext_recovery = float(sys.maxsize)
            self.tnext_i_am_working = self.tcurr + self.i_am_working_delay

        elif tmp_tnext == self.tnext_i_am_working:
            self.send_control_signal_to_reserve_EOM()
            self.tnext_i_am_working = self.tcurr + self.i_am_working_delay

        else:
            if not self.is_shutdown:
                self.quantity += 1
                self.inform_generator_element_proceeded()
            min_dev = self.get_min_device()
            min_dev.state = State.FREE
            min_dev.tnext = float(sys.maxsize)


class ReservEOM(Process):
    class WorkingState(Enum):
        PASSIVE = 0
        ACTIVE = 1

    def __init__(self, delay, name, generator):
        super().__init__(delay, name, None, 1, 1)

        if not isinstance(generator, TechProcessGenerator):
            raise TypeError('Generator must be an instance of TechProcessGenerator class')
        self.generator = generator

        self.is_main_alive = True
        self.tnext_main_alive = 1
        self.tnext_started_up = float(sys.maxsize)

        self.main_alive_delay = 30
        self.started_up_delay = 5

        self.working_state = ReservEOM.WorkingState.PASSIVE

    def main_is_alive(self):
        self.is_main_alive = True
        self.tnext_main_alive = self.tcurr + self.main_alive_delay

    def get_tnext(self):
        tmp_tnext = float(sys.maxsize)
        for device in self.devices:
            if device.tnext < tmp_tnext:
                tmp_tnext = device.tnext
        
        return min(tmp_tnext, self.tnext_main_alive, self.tnext_started_up)

    def in_act(self):
        if self.get_free_device() is not None:
            device = self.get_free_device()
            device.state = State.BUSY
            device.tnext = self.tcurr + self.delayMean
        else:
            self.failure += 1

    def inform_generator_element_proceeded(self):
        self.generator.send_element_proceeded()

    def out_act(self):
        tmp_tnext = self.get_tnext()
        if tmp_tnext == self.tnext_main_alive:
            self.is_main_alive = False
            self.tnext_main_alive = float(sys.maxsize)
            self.tnext_started_up = self.tcurr + self.started_up_delay

        elif tmp_tnext == self.tnext_started_up:
            self.working_state = ReservEOM.WorkingState.ACTIVE
            self.tnext_started_up = float(sys.maxsize)

        else:
            self.quantity += 1
            self.inform_generator_element_proceeded()

            min_dev = self.get_min_device()
            min_dev.state = State.FREE
            min_dev.tnext = float(sys.maxsize)
    
    def out_act_all(self, tcurr_next=None):
        super().out_act_all(tcurr_next)
        if self.tnext_main_alive == tcurr_next:
            self.out_act()
        if self.tnext_started_up == tcurr_next:
            self.out_act()

    def print_info(self):
        super().print_info()
        print(f'\tworking_state: {self.working_state} \
                is_main_alive: {self.is_main_alive} \
                tnext_main_alive: {self.tnext_main_alive} \
                tnext_started_up: {self.tnext_started_up}')



if __name__ == '__main__':
    generator = TechProcessGenerator('Generator')

    reserve_eom = ReservEOM(3, 'Reserve EOM', generator)
    main_eom = MainEOM(3, 'Main EOM', reserve_eom, generator)

    generator.main_eom = main_eom
    generator.reserve_eom = reserve_eom

    model = Model([generator, reserve_eom, main_eom], debug=True)
    model.simulate(1000)
