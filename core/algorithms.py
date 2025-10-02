import numpy as np
from deap import (algorithms, tools, creator)
import copy
from tqdm import tqdm
from typing import Dict, Set, FrozenSet, List, Tuple, Any

from core.problems import OptimizationProblem
from datetime import datetime, timedelta

from core.generate_initial_trip import InitIndividual, Attraction


class NSGAIIAlgorithm:

    def __init__(self, population_size: int, ngen: int, cxpb=0., mutpb=1.0):
        self.population_size = population_size
        self.ngen = ngen
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.problem: OptimizationProblem = OptimizationProblem()

    def setup(self, all_waypoints_set: Set[list[str]], waypoint_distances: Dict[FrozenSet[str], float],
              attractionsDetail: List[Attraction], place_additional_info, daily_depart_time: str, daily_return_time: str, departure_datetime, return_datetime):
        self.problem.setup(all_waypoints_set, waypoint_distances, attractionsDetail, place_additional_info, daily_depart_time, daily_return_time, departure_datetime, return_datetime)
        # attractionsDetail include attraction.name, attraction.open_time, attraction.close_time

        # self.attractionsDetail = attractionsDetail

    # TODO: deprecated
    def initIndividual(self):
        startTime = datetime.strptime("08:00", "%H:%M")
        endTime = datetime.strptime("22:00", "%H:%M")

        generate = InitIndividual(self.attractionsDetail, startTime, endTime, 3)
        return generate.getInitIndi()

    # TODO: change to multiple day
    @staticmethod
    def to_list(hof):

        return [
            [
                {
                    "place_id": attraction.attr.name,
                    "place_start_datetime": attraction.time_range.start_time,
                    "place_end_datetime": attraction.time_range.end_time,
                }
                for attraction in route
            ]
            for route in hof
        ]



    def run(self):
        pop = self.problem.toolbox.population()
        # exit()

        # allSchedules = generateByDfs()
        # allSchedules = self.initIndividual()
        # pop = [creator.Individual(schedule) for schedule in allSchedules]

        # print('generated schedules in algorithms.py')
        # print(pop)
        # print(pop[0].attr)

        # print('\n population before runing')
        # for ind in pop:
        #     print(ind)
        #     print(f"type {type(ind)}")

        hof = tools.ParetoFront(similar=self.pareto_eq)
        pbar = tqdm(total=self.ngen)
        stats = self.define_statistics(hof, pbar)

        # How many iterations of the genetic algorithm to run
        # The more iterations you allow it to run, the better the solutions it will find
        pop, log = algorithms.eaSimple(pop,
                                       self.problem.toolbox,
                                       cxpb=self.cxpb,
                                       mutpb=self.mutpb,
                                       ngen=self.ngen,
                                       stats=stats,
                                       halloffame=hof,
                                       verbose=False)
        pbar.close()
        return pop, hof, self.to_list(hof)

    def define_statistics(self, hof, pbar):
        stats = tools.Statistics(lambda ind: (int(ind.fitness.values[0]), round(ind.fitness.values[1], 2)))
        stats.register('Minimum', np.min, axis=0)
        stats.register('Maximum', np.max, axis=0)
        # This stores a copy of the Pareto front for every generation of the genetic algorithm
        stats.register('ParetoFront', lambda x: copy.deepcopy(hof))
        # This is a hack to make the tqdm progress bar work
        stats.register('Progress', lambda x: pbar.update())
        return stats

    @staticmethod
    def pareto_eq(ind1, ind2):
        return np.all(ind1.fitness.values == ind2.fitness.values)
