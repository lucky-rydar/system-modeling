from framework import *
from rand import *


class CarInput(Create):
    def __init__(self, delay_func, name):
        super().__init__(0, name)
        self.delay_func = delay_func

    def out_act(self):
        self.quantity += 1
        self.tnext = self.tcurr + self.delay_func()

        self.in_act_for_highest_priority_or_empty_queue()
    
    def in_act_for_highest_priority_or_empty_queue(self):
        if len(self.next_elements) != 2:
            raise Exception('CarInput has to have exactly 2 next elements')
        
        if self.next_elements[0].queue > 0 or self.next_elements[1].queue > 0:
            if self.next_elements[0].queue <= self.next_elements[1].queue:
                self.next_elements[0].in_act()
            else:
                self.next_elements[1].in_act()
        else:
            self.next_elements[0].in_act()


class BankLine(Process):
    def __init__(self, delay_func, name, maxqueue):
        super().__init__(0, name, maxqueue, devices_amount=1, priority=0)
        self.delay_func = delay_func
        self.other_bank_line = None

        # stats
        self.mean_queue = 0
        self.last_out_tcurr = 0

        self.mean_load = 0 # tcurr / (quantity * mean_process_time)
        
        self.between_out_act_sum = 0
        self.between_out_act_count = 0
        self.between_out_act_avg = 0

        
        self.mean_process_time_sum = 0
        self.mean_process_time_count = 0
        self.mean_process_time = 0 # mean process time

        self.mean_queue_time = 0 # mean queue * mean process time
        self.mean_process_queue_time = 0 # mean process time + mean queue time

        # mean queue

        self.failure_rate = 0 # failure / quantity

        self.rebalance_count = 0

    def do_statistics(self, delta):
        super().do_statistics(delta)

        if self.tcurr == 0 or self.quantity == 0 or self.mean_process_time_count == 0 or self.between_out_act_count == 0:
            return

        self.mean_process_time = self.mean_process_time_sum / self.mean_process_time_count

        self.mean_queue = self.meanQueue / self.tcurr
        self.mean_load = self.tcurr / self.quantity
        self.between_out_act_avg = self.between_out_act_sum / self.between_out_act_count

        self.mean_queue_time = self.mean_queue * self.mean_process_time
        self.mean_process_queue_time = self.mean_process_time + self.mean_queue_time

        self.failure_rate = self.failure / (self.quantity + self.failure)
    

    def in_act(self):
        if self.get_free_device() is not None:
            device = self.get_free_device()
            device.state = State.BUSY
            
            delay = self.delay_func()
            self.mean_process_time_sum += delay
            self.mean_process_time_count += 1

            device.tnext = self.tcurr + delay
        else:
            if self.queue < self.maxqueue:
                self.queue += 1
            else:
                self.failure += 1

    def out_act(self):
        self.quantity += 1

        self.between_out_act_sum += self.tcurr - self.last_out_tcurr
        self.between_out_act_count += 1
        self.last_out_tcurr = self.tcurr

        min_dev = self.get_min_device()
        
        min_dev.state = State.FREE
        min_dev.tnext = float(sys.maxsize)
        if self.queue > 0:
            self.queue -= 1
            free_device = self.get_free_device()
            free_device.state = State.BUSY
            free_device.tnext = self.tcurr + self.delay_func()

        self.rebalance_queue()

    def rebalance_queue(self):
        if self.other_bank_line.queue > self.queue + 1:
            self.other_bank_line.queue -= 1
            self.queue += 1
            self.rebalance_count += 1
        elif self.other_bank_line.queue < self.queue - 1:
            self.other_bank_line.queue += 1
            self.queue -= 1
            self.rebalance_count += 1

    def print_stats(self):
        print(f'{self.name} stats:')
        print(f'\tmean queue: {self.mean_queue}')
        print(f'\tmean load: {self.mean_load}')
        print(f'\tbetween out act avg: {self.between_out_act_avg}')
        print(f'\tmean process time: {self.mean_process_time}')
        print(f'\tmean queue time: {self.mean_queue_time}')
        print(f'\tmean process queue time: {self.mean_process_queue_time}')
        print(f'\tfailure rate: {self.failure_rate}')
        print(f'\trebalance count: {self.rebalance_count}')



def main():
    car_input = CarInput(lambda: Rand.exp(0.5), 'CarInput')

    bank_line1 = BankLine(lambda: Rand.exp(0.3), 'BankLine1', 3)
    bank_line2 = BankLine(lambda: Rand.exp(0.3), 'BankLine2', 3)

    bank_line1.other_bank_line = bank_line2
    bank_line2.other_bank_line = bank_line1

    car_input.next_elements = [bank_line1, bank_line2]

    car_input.tnext = 0.1
    bank_line1.tnext = Rand.norm(1, 0.3)
    bank_line2.tnext = Rand.norm(1, 0.3)
    bank_line1.queue = 2
    bank_line2.queue = 2
    
    model = Model([car_input, bank_line1, bank_line2], debug=False)
    model.simulate(100)


    # print stats
    print('\n')
    bank_line1.print_stats()
    bank_line2.print_stats()



if __name__ == "__main__":
    main()
