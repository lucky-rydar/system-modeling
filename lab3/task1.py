from framework import *

def main():
    create = Create(0.1, 'Create')

    process1 = Process(1, 'Process1', maxqueue=10, priority=1)
    process2 = Process(0.3, 'Process2', maxqueue=10, priority=2)

    create.next_elements = [process1, process2]

    model = Model([create, process1, process2], debug=True)
    model.simulate(1.5)


if __name__ == "__main__":
    main()
