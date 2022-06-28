import random

from numpy import NaN

class Counter:
    def __init__(self, num, period, trigger_first=True):
        self.counter_value = -1
        self.cycle_count = 0
        self.num = num
        self.period = period
        self.output_count = 0
        self.trigger_first = trigger_first
        self.running = False
    
    def getActive(self):
        return self.running
    
    def setActive(self, value):
        self.running = value
    
    def print_status(self, detailed=False):
        print("Output count: " + str(self.output_count))
        print("Counter value: " + str(self.counter_value))
        print("Cycle count: " + str(self.cycle_count))
        print("Total count: " + str(self.cycle_count * self.period + self.counter_value + 1))
        if detailed:
            print("Number of cycles: " + str(self.num))
            print("Length of cycle: " + str(self.period))

    def on_first(self):
        if self.trigger_first:
            return "activate"
        else:
            return "inc"
    
    def on_last(self):
        if self.trigger_first:
            return "inc"
        else: 
            return "activate"

    def reset(self):
        self.running = False
        self.counter_value = -1
        self.cycle_count = 0
        self.output_count = 0

    def rollover(self):
        self.counter_value = 0
        self.cycle_count += 1
    
    def increment(self):
        self.counter_value += 1
 
        if self.counter_value == self.period:
            self.counter_value = 0
            self.cycle_count += 1

        if self.cycle_count == self.num:
            self.reset()
            return "finished"

        if self.counter_value == self.period-1:
            return self.on_last()

        if self.counter_value == 0:

            return self.on_first()
        
        return "inc"            

    def tick(self):
        self.running = True
        out = self.increment()

        if out == "activate":
            self.output_count += 1
        
        return out

class Generation_module:
    def __init__(self, length):
        self.line = [1 for x in range(length)]

        self.collected = 0
        self.collection_counter = Counter(12, 10) #handles output during collection
        self.ice_reforming_counter = Counter(1, 10 * 2 + 4 * length) #counts how long ice takes before starting to reform

        self.running_duration = Generation_module.get_cooldown_time(length)

    def get_cooldown_time(length):
        return length * 10 * 2 + 12 * 10

    def print_state(self, detailed=False):
        print("ice line content: ")
        print(self.line)
        print("collected ice: " + str(self.collected))
        print("running_duration: " + str(self.running_duration))
        print("isOutputting: " + str(self.isOutputting()))
        if detailed:
            print("Collection counter: ")
            self.collection_counter.print_status(detailed=True)
            print("Ice Reforming counter: ")
            self.ice_reforming_counter.print_status(detailed=True)
    
    def isOutputting(self): #depricated
        return self.collection_counter.getActive()

    def collect(self):
        if self.collection_counter.getActive():
            raise Exception("Attempted to collect while counter was still active")
        if self.ice_reforming_counter.getActive():
            raise Exception("Ice reforming cannot still be happening once collection counter has finished")
        if (self.collected != 0):
            raise Exception("Attempted to collect without finishing previous collection")
        
        ice_count = 0
        for i in reversed(range(len(self.line))):
            if ice_count < 12:
                if self.line[i] == 1:
                    self.line[i] = 0
                    ice_count += 1
        self.collected = ice_count
        #print(self.collected)
        self.collection_counter.setActive(True)
        self.ice_reforming_counter.setActive(True)

    def attempt_ice(self, i):
        if random.randrange(0, 4096) == 0:
            self.line[i] = 1

    def recieve(self):
        if (self.collected > 0):
            self.collected -= 1
            return 1
        return 0

    def tick(self):

        #handle reforming counter
        if self.ice_reforming_counter.getActive():
            self.ice_reforming_counter.tick()
        
        #reform ice if reforming counter is inactive
        if not self.ice_reforming_counter.getActive():
            for i in range(len(self.line)):
                if self.line[i] == 0:
                    self.attempt_ice(i)

        #handle collection counter
        if self.collection_counter.getActive():
            if self.collection_counter.tick() == "activate":
                return self.recieve()
        
        return 0

class Farm:
    def __init__(self, module_count, module_length):
        minimum_module_count = Generation_module.get_cooldown_time(module_length) / 10 /12
        if (module_count < minimum_module_count):
            raise Exception("Too few modules, minimum is: " + str(minimum_module_count))
        
        self.module_collection = [Generation_module(module_length) for x in range(module_count)]

        self.active_module = 0
        self.module_collection[self.active_module].collect()

        self.tick_count = 0
        self.ice_count = 0

    def print_modules(self):
        for n in range(len(self.module_collection)):
            print("Module: " + str(n))
            self.module_collection[n].print_state()

    def get_outputting_module(self):
        for i in range(len(self.module_collection)):
            if self.module_collection[i].isOutputting():
                return self.module_collection[i]
        
        raise Exception("Couldn't find outputting module")

    def tick(self):
        #print("Tick " + str(self.tick_count))
        #if module is outputting currently
        if self.module_collection[self.active_module].isOutputting():
            var = self.module_collection[self.active_module].recieve()
            self.ice_count += var
            #print(var)
            #self.module_collection[self.active_module].print_state(detailed=True)
        #if module finished outputting
        else:
            if self.active_module == len(self.module_collection)-1:
                self.active_module = 0
            else:
                self.active_module += 1
            
            self.module_collection[self.active_module].collect()
            self.ice_count += self.module_collection[self.active_module].recieve()

        for m in self.module_collection:
            m.tick()

        self.tick_count += 1

    def print_results(self, detailed_print=False):
        print("ticks: " + str(self.tick_count))
        print("ice: " + str(self.ice_count))
        print("ice/tick: " + str(self.ice_count / self.tick_count))
        print("ice/hour: " + str((self.ice_count / self.tick_count) * 72000))
        print("efficiency: " + str(((self.ice_count / self.tick_count) * 72000) / 14400 * 100) + "%")
        if detailed_print:
            print("Raw data: ")
            self.print_modules()

    def tickwarp(self, time, detailed_print=False):
        for i in range(time):
            self.tick()
        self.print_results(detailed_print = detailed_print)
        

#c = Counter(12, 10)

#for x in range(121):
#    print("Tick: " + str(x))
#    c.tick()
#    c.print_status() #at 1
#    print("")

#g = Generation_module(12) 
#g.collect()
#g.print_state(detailed=True)
#g.recieve()
#for x in range(121):
#    g.tick()
    #print(g.tick())
#print("")
#g.print_state(detailed=True)

f = Farm(64, 24)
f.tickwarp(72000, detailed_print=True)






