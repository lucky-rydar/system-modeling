import random
import math

class Rand:
    def exp(mean_time):
        a = 0
        while a == 0:
            a = random.random()
        a = -mean_time * math.log(a)
        return a
        
    def norm(mean_time, std_deviation):
        a = random.normalvariate(mean_time, std_deviation)
        return a
    
    def uniform(a, b):
        a = random.uniform(a, b)
        return a

    def erlang(mean_time, k):
        return random.gammavariate(k, mean_time / k)
    