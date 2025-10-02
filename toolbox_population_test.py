
import random
from functools import partial

from pandas.core.internals.base import interleaved_dtype
from deap import (algorithms, tools, creator, base)

'''
random.seed(42)
gen_idx = partial(random.sample, range(10), 10)
print(tools.initIterate(list, gen_idx))
'''



creator.create('FitnessMulti', base.Fitness, weights=(1.0, -1.0, 1.0,))
creator.create('Individual', list, fitness=creator.FitnessMulti)


all_waypoints = ['asdfjioaijosdf', 'basdfijoajiosdf', 'caisodfjioajsdf', 'disdfjioasdf', 'oaisdjfoiajsdfe' ]

toolbox = base.Toolbox()
toolbox.register('waypoints', random.sample, all_waypoints, 4)
toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.waypoints)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)

# toolbox.register('individual',
# toolbox.register('population', tools.initRepeat, list, toolbox.individual)

indi = toolbox.individual()
print(f"individual: {indi}")
print(f"individual: {indi.fitness}")
print(type(indi))

# print(ind1.fitness)
# ind1.fitness = evalu(ind1)

pop = toolbox.population(n=5)

for p in pop:
    print(f"p: {p}")


[[creator], [creator], [creator]]
[[], [attractoin], [attraction]]

[[creator]]


'''
def initRepeat(container, func, n):
    return container(func(i) for i in range(n))

def initRepeat(list, random.sample, n):
    return list(random.sample(i) for i in range(n))

def population(initRepeat, n):
    return initRepeat(n)


pop = population(n=5)
'''

