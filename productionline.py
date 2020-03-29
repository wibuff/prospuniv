""" a Product Line
"""

import sys
import json
from clock import DecrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes
from ledger import Ledger

class ProductionLine(object):
    """ ProductionLine class
    """

    def __init__(self, stream_id, line_id, queue, inventory, market, master_clock):
        self.line_id = line_id
        self.linetype = ProductionLines[line_id]
        self.efficiency = self._calc_efficiency()
        self.queue = self._init_production_queue(queue)
        self.ledger = Ledger(stream_id, line_id, market)
        self.inventory = inventory
        
        self.producing = False
        self.recipe_clock = DecrClock(Duration("0"))
        self._start_next_recipe(master_clock)

        print('{} {} initialized: {}'.format(master_clock, line_id, self))

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

        self.inventory.add(product, count)
        self.producing = False
        self.ledger.add(master_clock, Ledger.OUTPUT, 'output produced', count=count, product=product)
        # TODO capture value of produced goods
    
    def _set_next_recipe_active(self):
        last = self.queue.pop(0)
        self.queue.append(last)

    def _inputs_available(self, recipe, inputs, num_runs):
        for input in inputs: 
            product = input['id']
            count = input['count'] * num_runs
            available = self.inventory.count(product)
            if available - count < 0:
                return False
        return True

    def _consume_inputs(self, master_clock, inputs, num_runs):
        for input in inputs: 
            product = input['id']
            count = input['count'] * num_runs
            if not self.inventory.remove(product, count):
                raise Exception('removing {} {} from inventory failed'.format(count, product))
            self.ledger.add(master_clock, Ledger.INPUT, 'input consumed', count=count, product=product)

    def _start_next_recipe(self, master_clock):
        active = self.queue[0]
        recipe = active['recipe']
        output = recipe['output']
        if self._inputs_available(output, recipe['inputs'], active['count']):
            # TODO capture cost of goods and production fees (10.00 ICA per 24 baseline production hours)
            self.producing = True
            self._consume_inputs(master_clock, recipe['inputs'], active['count'])
            self.recipe_clock = self._set_recipe_clock(active)

    def step(self, master_clock):
        self.recipe_clock.step()
        if not self.producing:
            # not currently producing, attempt to start next item in queue
            self._start_next_recipe(master_clock)
        elif self.recipe_clock.to_minutes() > 0:
            # producing, time remaining 
            pass
        else: 
            # production done, produce output and attempt to start next item in queue
            self._produce(master_clock)
            self._set_next_recipe_active()
            self._start_next_recipe(master_clock)
        if self.producing:
            self.ledger.add(master_clock, Ledger.STATUS, 'producing', state=Ledger.ACTIVE) 
        else:
            self.ledger.add(master_clock, Ledger.STATUS, 'starved', state=Ledger.INACTIVE) 

       