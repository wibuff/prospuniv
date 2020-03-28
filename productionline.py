""" a Product Line
"""

import sys
import json
from clock import DecrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes

class ProductionLine(object):
    """ ProductionLine class
    """

    def __init__(self, line_id, queue, inventory):
        self.line_id = line_id
        self.linetype = ProductionLines[line_id]
        self.efficiency = self._calc_efficiency()
        self.queue = self._init_production_queue(queue)
        self.inventory = inventory
        
        self.producing = False
        self.recipe_clock = DecrClock(Duration("0"))
        self._start_next_recipe()

        print('  line {} initialized: {}'.format(line_id, self))
 

    def __str__(self):
        return json.dumps({ 
            'lineId': self.line_id, 
            'efficiency': self.efficiency,
            'producing': self.producing,
            'recipeClock': str(self.recipe_clock), 
            'linetype': self.linetype, 
            'queue': self.queue 
            })

    def _calc_efficiency(self):
        return self.linetype['worksat'] * self.linetype['condition'] +\
            self.linetype['experts'] + self.linetype['soil'] + self.linetype['cogc']

    def _init_production_queue(self, queue):
        prodqueue = []
        for item in queue:
            if item['recipe'] not in Recipes: 
                raise Exception('recipe {} not found'.format(item['recipe']))
            production = {
                'id': item['recipe'],
                'count': item['count'],
                'recipe': Recipes[item['recipe']]
            }
            prodqueue.append(production)
        return prodqueue

    def _set_recipe_clock(self, active):
        recipe = active['recipe']
        count = active['count']
        duration = Duration(recipe['time'])
        duration.apply_multiplier(count)
        duration.apply_efficiency(self.efficiency)
        return DecrClock(duration)

    def _produce(self, master_clock):
        active = self.queue[0]
        recipe = active['recipe']
        product = recipe['output']
        count = active['count'] * recipe['count']

        # TODO capture value of produced goods
        self.inventory.add(product, count)
        self.producing = False

        # print('{}: {} produced {} {}'.format(master_clock, self.line_id, count, product))
        # print('{}: inventory updated {}'.format(master_clock, self.inventory))
    
    def output_prod_status(self, master_clock):
        active = self.queue[0]
        runcount = active['count']
        recipe = active['recipe']
        outputcount = recipe['count']
        product = recipe['output']
        if self.producing: 
            print('{}: {} producing {}x{} {} in {}'.format(master_clock, self.line_id, runcount, outputcount, product, self.recipe_clock))
        else:
            print('{}: {} !! WARNING !! {} production starved'.format(master_clock, self.line_id, product) )
    
    def _set_next_recipe_active(self):
        last = self.queue.pop(0)
        self.queue.append(last)

    def _inputs_available(self, recipe, inputs, num_runs):
        available = True
        missing = {}
        for input in inputs: 
            id = input['id']
            count = input['count'] * num_runs
            available = self.inventory.count(id)
            if available - count < 0:
                needed = count - available
                missing[id] = needed
                available = False
        if not available:
            #print('{} production missing {}'.format(recipe, missing))
            pass
        return available

    def _consume_inputs(self, inputs, num_runs):
        for input in inputs: 
            id = input['id']
            count = input['count'] * num_runs
            if not self.inventory.remove(id, count):
                raise Exception('removing {} {} from inventory failed'.format(count, id))

    def _start_next_recipe(self):
        active = self.queue[0]
        recipe = active['recipe']
        if self._inputs_available(recipe['output'], recipe['inputs'], active['count']):
            # TODO capture cost of goods and production fees (10.00 ICA per 24 baseline production hours)
            self.producing = True
            self._consume_inputs(recipe['inputs'], active['count'])
            self.recipe_clock = self._set_recipe_clock(active)

    def step(self, master_clock):
        self.recipe_clock.step()
        if not self.producing:
            # not currently producing, attempt to start next item in queue
            self._start_next_recipe()
            if self.producing:
                # self.output_prod_status(master_clock)
                pass
        elif self.recipe_clock.to_minutes() > 0:
            # producing, time remaining 
            # self.output_prod_status(master_clock)
            pass
        else: 
            # production done, produce output and attempt to start next item in queue
            self._produce(master_clock)
            self._set_next_recipe_active()
            self._start_next_recipe()
            self.output_prod_status(master_clock)
       