import random
from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from typing import Dict, Set, FrozenSet, List, Tuple, Any

from datetime import datetime, timedelta
from core.generate_initial_trip import AttractionModify, InitIndividual, Attraction

from dataclasses import dataclass

from core.generate_initial_trip import DiverseScheduleGenerator, TimeRange
from core.read_from_csv import time_to_datetime
from core.generate_multiple_day_trip import DayConfig, MultiDayInitIndividual, ScheduleTransformer
from collections import defaultdict

# from methods.toolbox_operator import *


# [新增] 評估配置類
@dataclass
class EvaluationConfig:
    """評估系統的配置參數"""
    time_overlap_penalty: float = 1000.0  # 時間重疊懲罰
    business_hour_penalty: float = 2000.0  # 營業時間違規懲罰
    specific_location_bonus: float = 51111  # 特定位置獎勵


class OptimizationProblem:

    def __init__(self):
        self.toolbox = base.Toolbox()
        self.parameters = {}  # TODO: this is deprecated
        self.toolbox = base.Toolbox()
        self.all_waypoints = list()
        self.config = EvaluationConfig()
        self.start = ''
        self.end = ''

        self.normalizer = {
            'distance': {
                'min': float('inf'),
                'max': float('-inf')
            },
            'price': {
                'min': float('inf'),
                'max': float('-inf')
            },
            'rating': {
                'min': float('inf'),
                'max': float('-inf')
            }
        }

        # 新增餐廳相關設定
        self.restaurant_config = {
            'min_restaurants_per_day': 2,  # Minimum restaurants per day
            'max_restaurants_per_day': 3,  # Maximum restaurants per day
            'restaurant_penalty': 1000.0,  # Base penalty for violations
            'restaurant_categories': {'restaurant', 'food', 'cafe'},  # Restaurant categories
            'lunch_window': {
                'start': datetime.strptime('11:30', '%H:%M').time(),
                'end': datetime.strptime('14:00', '%H:%M').time()
            },
            'dinner_window': {
                'start': datetime.strptime('17:30', '%H:%M').time(),
                'end': datetime.strptime('21:00', '%H:%M').time()
            },
            'timing_penalty': 800.0  # Penalty for poor timing
        }

    def setup(self, all_waypoints_set: Set[list[str]],
              waypoint_distances: Dict[FrozenSet[str], float],
              attractionsDetail, place_additional_info, daily_depart_time: str,
              daily_return_time: str, departure_datetime, return_datetime):
        # attractionsDetail include attraction.name, attraction.open_time, attraction.close_time, stay_time
        # place_additional_info include  "price_level", "rating", "user_rating_totals", "category"

        self.start = 'Maryland State House, 100 State Cir, Annapolis, MD 21401'
        self.last = 'Mount Vernon, Fairfax County, Virginia'

        self.daily_depart_time = daily_depart_time
        self.daily_return_time = daily_return_time
        self.departure_datetime = departure_datetime
        self.return_datetime = return_datetime
        # print(self.daily_depart_time)
        # print(self.daily_return_time)

        self.all_waypoints = list(all_waypoints_set)
        self.waypoint_distances = waypoint_distances

        # create population fucntion
        self.toolbox = base.Toolbox()
        self.attractionsDetail = attractionsDetail
        self.place_additional_info = place_additional_info

        self.define_individual_and_fitness()
        self.register_tools()

        # self.toolbox.register('waypoints', random.sample, self.all_waypoints,
        #                       4)
        # self.toolbox.register('individual', tools.initIterate,
        #                       creator.Individual, self.toolbox.waypoints)
        # self.toolbox.register('population', tools.initRepeat, list,
        #                       self.toolbox.individual)

        # [[], [], []]

    def define_individual_and_fitness(self):
        creator.create(
            'FitnessMulti',
            base.Fitness,
            weights=(
                1.0,
                -1.0,  # distance
                # 1.0, # specific score , disabled
                -1.0,  # price level
                1.0,  # rating
                1.0,  # user rating totals
                # -1.0,  # [新增] 時間順序懲罰 , disabled
                -1.0  # [新增] 餐廳頻率懲罰
                # TODO:  delete some of the weigths
            ))
        creator.create('Individual', list, fitness=creator.FitnessMulti)

    def register_tools(self):
        self.toolbox.register('population', self.generate_population)
        self.toolbox.register('evaluate', self.__eval_capitol_trip)
        self.toolbox.register('mutate', self.__mutation_operator)
        self.toolbox.register('select', self.__pareto_selection_operator)
        self.toolbox.register('mate', self.__crossover_operator)

    def __calculate_base_metrics(self,
                                 individual: List[AttractionModify]) -> Dict:
        """計算基本評估指標"""
        trip_length = 0.0
        price_level_sum = 0
        rating = 0.0
        user_rating_totals = 0

        for index in range(1, len(individual)):
            waypoint1 = individual[index - 1].attr.name
            waypoint2 = individual[index].attr.name
            # print(f"waypoint1: {waypoint1} waypoint2: {waypoint2}")
            # print(f"fronzenset {frozenset([waypoint1, waypoint2])}")
            trip_length += self.waypoint_distances[frozenset(
                [waypoint1, waypoint2])]
            price_level_sum += self.place_additional_info[waypoint1][
                'price_level']
            rating += self.place_additional_info[waypoint1]['rating']
            user_rating_totals += self.place_additional_info[waypoint1][
                'user_rating_totals']
            # print(f"trip_length: {trip_length}")

        return {
            'trip_length': trip_length,
            'price_level_sum': price_level_sum,
            'rating': rating,
            'user_rating_totals': user_rating_totals
        }

    # [新增] 計算時間懲罰的輔助方法
    def __calculate_time_penalties(
            self, individual: List[AttractionModify]) -> float:
        """計算時間相關的懲罰"""
        total_penalty = 0.0

        # 檢查相鄰景點的時間順序
        for i in range(1, len(individual)):
            prev_attr = individual[i - 1]
            curr_attr = individual[i]

            if prev_attr.time_range.end_time > curr_attr.time_range.start_time:
                time_diff = (
                    prev_attr.time_range.end_time -
                    curr_attr.time_range.start_time).total_seconds() / 3600
                total_penalty += time_diff * self.config.time_overlap_penalty

        # 檢查營業時間違規
        for attr in individual:
            # 提前到達
            if attr.time_range.start_time < attr.attr.open_time:
                time_diff = (attr.attr.open_time -
                             attr.time_range.start_time).total_seconds() / 3600
                total_penalty += time_diff * self.config.business_hour_penalty

            # 關門後離開
            if attr.time_range.end_time > attr.attr.close_time:
                time_diff = (attr.time_range.end_time -
                             attr.attr.close_time).total_seconds() / 3600
                total_penalty += time_diff * self.config.business_hour_penalty

        return total_penalty

    def __calculate_restaurant_penalty(self, individual: List[AttractionModify]) -> float:
        """Calculate penalties for restaurant frequency and timing"""
        # Group attractions by date
        daily_restaurants = defaultdict(list)

        for attr in individual:
            place_info = self.place_additional_info.get(attr.attr.name, {})
            place_categories = place_info.get('category', set())

            # Check if it's a restaurant
            if self.restaurant_config['restaurant_categories'].intersection(place_categories):
                visit_date = attr.time_range.start_time.date()
                daily_restaurants[visit_date].append(attr)

        total_penalty = 0.0

        # Evaluate each day's restaurant distribution
        for date, restaurants in daily_restaurants.items():
            # Check frequency
            count = len(restaurants)
            if count < self.restaurant_config['min_restaurants_per_day']:
                total_penalty += (self.restaurant_config['min_restaurants_per_day'] - count) * \
                               self.restaurant_config['restaurant_penalty']
            elif count > self.restaurant_config['max_restaurants_per_day']:
                total_penalty += (count - self.restaurant_config['max_restaurants_per_day']) * \
                               self.restaurant_config['restaurant_penalty']

            # Check timing
            lunch_found = dinner_found = False
            bad_timing_count = 0

            for rest in restaurants:
                visit_time = rest.time_range.start_time.time()

                # Check if within lunch window
                if (self.restaurant_config['lunch_window']['start'] <= visit_time <=
                    self.restaurant_config['lunch_window']['end']):
                    lunch_found = True
                # Check if within dinner window
                elif (self.restaurant_config['dinner_window']['start'] <= visit_time <=
                      self.restaurant_config['dinner_window']['end']):
                    dinner_found = True
                else:
                    bad_timing_count += 1

            # Add penalties for poor timing
            if not lunch_found and count > 0:
                total_penalty += self.restaurant_config['timing_penalty']
            if not dinner_found and count > 1:
                total_penalty += self.restaurant_config['timing_penalty']
            total_penalty += bad_timing_count * self.restaurant_config['timing_penalty']

        return total_penalty

    def generate_population(self):
        day_configs = DayConfig.create_day_configs(
            departure_datetime=self.departure_datetime,
            return_datetime=self.return_datetime,
            daily_depart_time=self.daily_depart_time,
            daily_return_time=self.daily_return_time)

        generator = MultiDayInitIndividual(
            attractions=self.attractionsDetail,
            day_configs=day_configs,
            place_additional_info=self.place_additional_info)
        # attractionsDetail include attraction.name, attraction.open_time, attraction.close_time
        # place_additional_info include  "price_level", "rating", "user_rating_totals", "category"

        # 生成初始行程
        multi_day_schedules = generator.getInitIndi()
        transformer = ScheduleTransformer()
        flattened_schedules = transformer.flatten_schedules(
            multi_day_schedules)

        # print()
        # print(
        #     'schedules generated by generate_inital_trip in problem.py.generate_population'
        # )
        for schedule in flattened_schedules:
            check_duplicate = set()
            for attraction_modify in schedule:
                if attraction_modify.attr.name in check_duplicate:
                    # print('error id is duplicate')
                    exit()
                check_duplicate.add(attraction_modify.attr.name)
        #         print(
        #             f"{attraction_modify.attr.name}, {attraction_modify.time_range.start_time}, {attraction_modify.time_range.end_time}"
        #         )
        #     print()
        # print(
        #     'the end of schedules generated by generate_inital_trip in problem.py.generate_population'
        # )

        # 轉換為DEAP個體
        population = []
        for schedule in flattened_schedules:
            individual = creator.Individual(schedule)
            population.append(individual)

        return population

    # TODO: deprecated
    def generate_population2(self):
        startTime = datetime.strptime("08:00", "%H:%M")
        endTime = datetime.strptime("22:00", "%H:%M")
        '''
        print('\nattractionsDetail in problems.py')
        for attr in self.attractionsDetail:
            print(attr.name, attr.open_time, attr.close_time, attr.stay_time)
        '''

        init_individual = InitIndividual(self.attractionsDetail, startTime,
                                         endTime, 3)

        population = []
        for schedule in init_individual.getInitIndi():
            individual = creator.Individual(schedule)
            population.append(individual)
        return population  # poplation is Deap(Individual(AttractionModify)

        # return [
        #     creator.Individual(attr) for attr in schedule for schedule in indi
        # ]

    @staticmethod
    def checkIndividualType(individual):
        print('\nindi type')
        for indi in individual:
            print(type(indi))
            if type(indi) == str:
                print(indi)
        print()

    def __eval_capitol_trip(self, individual):
        """
            type:
            individual: deap.creator.Individual

            This function returns the total distance traveled on the current road trip
            as well as the number of waypoints visited in the trip.

            The genetic algorithm will favor road trips that have shorter
            total distances traveled and more waypoints visited.
        """

        def printBefore():
            print('\ntype')
            print(type(individual))
            print(type(individual[0]))
            print(type(individual[0].attr.name))
            print(individual[0].attr.name)

            print('\nindi type')
            for indi in individual:
                print(type(indi))
                if type(indi) == str:
                    print(1)
                    print(indi)
            print()

        # printBefore()

        # individual = list(individual)

        # Adding the starting point to the end of the trip forces it to be a round-trip
        # individual += [individual[0]]

        # 1. 計算基本指標
        base_metrics = self.__calculate_base_metrics(individual)

        # 2. 計算時間懲罰 TODO: disabled dont needed anymore(?)
        # time_penalty = self.__calculate_time_penalties(individual)

        # 3. [新增] 計算餐廳頻率懲罰
        restaurant_penalty = self.__calculate_restaurant_penalty(individual)

        # 更新最大最小值
        self.__update_normalizer(base_metrics)
        # 歸一化處理
        normalized_metrics = self.__normalize_metrics(base_metrics)

        # 應用權重
        # TODO: change weight
        WEIGHTS = {
            'distance': 1.0,
            'price': 2.0,  # 加大價格的權重
            'rating': 1.0
        }

        # 3. 計算特定位置獎勵
        # specific_score = 0
        # if individual[0] == self.start:
        #     specific_score += self.config.specific_location_bonus
        # if individual[len(individual) - 1] == self.last:
        #     specific_score += self.config.specific_location_bonus

        # print(f"specific score: {specific_score}")

        # 4. 返回所有評估指標
        return (
            len(set(attr.attr.name for attr in individual)),  # 不同景點數量
            normalized_metrics['distance'] * WEIGHTS['distance'],  # 歸一化的距離
            # specific_score,  # 特定位置獎勵 disabled
            normalized_metrics['price'] * WEIGHTS['price'],  # 歸一化的價格
            normalized_metrics['rating'] * WEIGHTS['rating'],  # 歸一化的評分
            base_metrics['user_rating_totals'],  # 用戶評價總數
            # -time_penalty,  # 時間順序懲罰 disabled
            -restaurant_penalty  # [新增] 餐廳頻率懲罰
        )

    def __normalize_metrics(self, metrics: Dict) -> Dict:
        """
        將各指標歸一化到[0,1]範圍
        """
        normalized = {}

        # 距離歸一化
        if self.normalizer['distance']['max'] != self.normalizer['distance'][
                'min']:
            normalized['distance'] = (metrics['trip_length'] - self.normalizer['distance']['min']) / \
                                     (self.normalizer['distance']['max'] - self.normalizer['distance']['min'])
        else:
            normalized['distance'] = 0

        # 價格歸一化
        if self.normalizer['price']['max'] != self.normalizer['price']['min']:
            normalized['price'] = (metrics['price_level_sum'] - self.normalizer['price']['min']) / \
                                  (self.normalizer['price']['max'] - self.normalizer['price']['min'])
        else:
            normalized['price'] = 0

        # 評分歸一化
        if self.normalizer['rating']['max'] != self.normalizer['rating'][
                'min']:
            normalized['rating'] = (metrics['rating'] - self.normalizer['rating']['min']) / \
                                   (self.normalizer['rating']['max'] - self.normalizer['rating']['min'])
        else:
            normalized['rating'] = 0

        return normalized

    def __update_normalizer(self, metrics: Dict):
        """
        更新用於歸一化的最大最小值
        """
        # 更新距離範圍
        self.normalizer['distance']['min'] = min(
            self.normalizer['distance']['min'], metrics['trip_length'])
        self.normalizer['distance']['max'] = max(
            self.normalizer['distance']['max'], metrics['trip_length'])

        # 更新價格範圍
        self.normalizer['price']['min'] = min(self.normalizer['price']['min'],
                                              metrics['price_level_sum'])
        self.normalizer['price']['max'] = max(self.normalizer['price']['max'],
                                              metrics['price_level_sum'])

        # 更新評分範圍
        self.normalizer['rating']['min'] = min(
            self.normalizer['rating']['min'], metrics['rating'])
        self.normalizer['rating']['max'] = max(
            self.normalizer['rating']['max'], metrics['rating'])

    def __pareto_selection_operator(self, individuals, k):
        """
            This function chooses what road trips get copied into the next generation.

            The genetic algorithm will favor road trips that have shorter
            total distances traveled and more waypoints visited.
        """
        return tools.selNSGA2(individuals, int(k / 5.)) * 5

    def __mutation_operator(self, individual):
        """
            This function applies a random change to one road trip:

                - Insert: Adds one new waypoint to the road trip
                - Delete: Removes one waypoint from the road trip
                - Point: Replaces one waypoint with another different one
                - Swap: Swaps the places of two waypoints in the road trip
        """
        possible_mutations = ['point']

        if len(individual) < len(self.attractionsDetail):
            # possible_mutations.append('insert')
            # possible_mutations.append('point')
            pass
        if len(individual) > 2:
            pass
            possible_mutations.append('delete')

        mutation_type = random.sample(possible_mutations, 1)[0]

        # Insert mutation
        if mutation_type == 'insert':
            self.__insert_mutation_operator(individual)
        # Delete mutation
        elif mutation_type == 'delete':
            self.__delete_mutation_operator(individual)
        # Point mutation
        elif mutation_type == 'point':
            self.__point_mutation_operator(individual)
        # Swap mutation
        elif mutation_type == 'swap':
            self.__swap_mutation_operator(individual)

        # debug
        # print('\nin problem.py mutation')
        # self.checkIndividualType(individual)
        # print('end\n')

        return individual,

    def __insert_mutation_operator(self, individual):
        waypoint_to_add = individual[0]
        while waypoint_to_add in individual:
            waypoint_to_add = random.sample(self.attractionsDetail, 1)[0]
        # print('\ntype of waypoint to add')
        # print(type(waypoint_to_add))
        index_to_insert = random.randint(0, len(individual) - 1)
        individual.insert(index_to_insert, waypoint_to_add)

    def __delete_mutation_operator(self, individual):
        index_to_delete = random.randint(0, len(individual) - 1)
        del individual[index_to_delete]

    def __point_mutation_operator(self, individual):
        index_to_replace = random.randint(0, len(individual) - 1)
        replaced_attr_mod = individual[index_to_replace]

        suitable_attractions = [
            attr for attr in self.attractionsDetail
            if attr not in [attr_mod.attr for attr_mod in individual]
            and attr.open_time <= replaced_attr_mod.time_range.start_time
            and attr.close_time >= replaced_attr_mod.time_range.end_time
            # TODO:  replaced_attr_mod.time_range.start_time + timedelta(hours=attr.stay_time)).time() maybe need to change to replaced_attr_mod.time_range.end_time
        ]

        if suitable_attractions:
            waypoint_to_add = random.choice(suitable_attractions)

            new_attr_mod = AttractionModify(
                attr=waypoint_to_add,
                time_range=TimeRange(
                    start_time=replaced_attr_mod.time_range.start_time,
                    end_time=replaced_attr_mod.time_range.end_time))

            individual[index_to_replace] = new_attr_mod

            # 調整替換位置之後的所有景點的時間
            for i in range(index_to_replace + 1, len(individual)):
                prev_end_time = individual[i - 1].time_range.end_time
                individual[i].time_range.start_time = prev_end_time
                individual[i].time_range.end_time = prev_end_time + timedelta(
                    hours=individual[i].attr.stay_time)

    def __swap_mutation_operator(self, individual):
        index1 = random.randint(0, len(individual) - 1)
        index2 = index1
        while index2 == index1:
            index2 = random.randint(0, len(individual) - 1)
        individual[index1], individual[index2] = individual[
            index2], individual[index1]

    def __has_duplicates(self, individual):
        """檢查行程中是否有重複的景點"""
        seen = set()  # 用來記錄已經看過的景點
        for attr_mod in individual:
            place_id = attr_mod.attr.name  # 獲取景點的ID
            if place_id in seen:  # 如果這個ID已經在seen集合中
                return True  # 表示發現重複，返回True
            seen.add(place_id)  # 將這個ID加入seen集合
        return False  # 沒有發現重複，返回False

    def __crossover_operator(self, ind1, ind2):
        """Main crossover operator that randomly selects and applies different crossover strategies"""
        possible_crossovers = ['one_point', 'two_point', 'uniform', 'pmx']
        crossover_type = random.choice(possible_crossovers)

        # 使用toolbox.clone來正確複製Individual
        offspring1, offspring2 = self.toolbox.clone(ind1), self.toolbox.clone(
            ind2)

        if crossover_type == 'one_point':
            offspring1, offspring2 = self.__one_point_crossover(
                offspring1, offspring2)
        elif crossover_type == 'two_point':
            offspring1, offspring2 = self.__two_point_crossover(
                offspring1, offspring2)
        elif crossover_type == 'uniform':
            offspring1, offspring2 = self.__uniform_crossover(
                offspring1, offspring2)
        # elif crossover_type == 'pmx':
        #     offspring1, offspring2 = self.__partially_mapped_crossover(
        #         offspring1, offspring2)

        # Update time ranges for both offspring
        # FIXME: need to fix
        # self.__update_schedule_times(offspring1)
        # self.__update_schedule_times(offspring2)

        # 檢查是否有重複景點
        if self.__has_duplicates(offspring1) or self.__has_duplicates(
                offspring2):
            return ind1, ind2  # 如果有重複，返回原始個體

        # 將fitness設為無效
        del offspring1.fitness.values
        del offspring2.fitness.values

        return offspring1, offspring2

    def __one_point_crossover(self, ind1, ind2):
        """Single point crossover for schedules"""
        if len(ind1) > 1 and len(ind2) > 1:
            point = random.randint(1, min(len(ind1), len(ind2)) - 1)
            ind1[point:], ind2[point:] = ind2[point:], ind1[point:]
        return ind1, ind2

    def __two_point_crossover(self, ind1, ind2):
        """Two point crossover for schedules"""
        if len(ind1) > 2 and len(ind2) > 2:
            size = min(len(ind1), len(ind2))
            point1 = random.randint(1, size - 2)
            point2 = random.randint(point1 + 1, size - 1)
            ind1[point1:point2], ind2[point1:point2] = ind2[
                point1:point2], ind1[point1:point2]
        return ind1, ind2

    def __uniform_crossover(self, ind1, ind2):
        """Uniform crossover with probability for each attraction"""
        size = min(len(ind1), len(ind2))
        for i in range(size):
            if random.random() < 0.5:  # 50% chance to swap each attraction
                ind1[i], ind2[i] = ind2[i], ind1[i]
        return ind1, ind2

    def __partially_mapped_crossover(self, ind1, ind2):
        """Partially Mapped Crossover (PMX) for schedules"""
        size = min(len(ind1), len(ind2))
        if size <= 2:
            return ind1, ind2

        # Choose two crossover points
        point1 = random.randint(0, size - 2)
        point2 = random.randint(point1 + 1, size - 1)

        # Create mapping between segments
        mapping = {}
        for i in range(point1, point2):
            mapping[ind1[i].attr.name] = ind2[i].attr.name
            mapping[ind2[i].attr.name] = ind1[i].attr.name

        # Create offspring using the mapping
        offspring1 = self.__apply_pmx_mapping(ind1, ind2, point1, point2,
                                              mapping)
        offspring2 = self.__apply_pmx_mapping(ind2, ind1, point1, point2,
                                              mapping)

        return offspring1, offspring2

    def __apply_pmx_mapping(self, parent1, parent2, point1, point2, mapping):
        """Helper function for PMX crossover"""
        offspring = parent1.copy()

        # Copy the mapping segment from parent2
        offspring[point1:point2] = parent2[point1:point2]

        # Fix any conflicts using the mapping
        for i in range(len(parent1)):
            if i < point1 or i >= point2:
                current_attr = offspring[i].attr.name
                while current_attr in mapping and mapping[
                        current_attr] != offspring[i].attr.name:
                    current_attr = mapping[current_attr]
                # Find the attraction object with the mapped name
                for attr in parent2:
                    if attr.attr.name == current_attr:
                        offspring[i] = attr
                        break

        return offspring

    def __update_schedule_times(self, schedule):
        """Update time ranges for attractions after crossover"""
        if not schedule:
            return

        current_time = schedule[0].time_range.start_time
        for attr_mod in schedule:
            # Update start and end times
            attr_mod.time_range.start_time = current_time
            attr_mod.time_range.end_time = current_time + timedelta(
                hours=attr_mod.attr.stay_time)
            # Add travel time buffer
            current_time = attr_mod.time_range.end_time + timedelta(minutes=30)
