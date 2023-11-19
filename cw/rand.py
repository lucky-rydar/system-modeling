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

if __name__ == '__main__':
    # Test exp function
    print(Rand.exp(5)) # Expected output: a float value
    
    # Test norm function
    print(Rand.norm(0, 1)) # Expected output: a float value
    
    # Test uniform function
    print(Rand.uniform(0, 10)) # Expected output: a float value
    
    # Test erlang function
    print(Rand.erlang(5, 3)) # Expected output: a float value
