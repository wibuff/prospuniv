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
        self.line_spec = ProductionLines[line_id]
        self.queue = []
        for recipe in queue:
            self.queue.append(Recipes[recipe])
        self.inventory = inventory
        self.recipe_clock = self._set_recipe_clock(self.queue[0], self.line_spec['efficiency'])
        print('  line initialized: {}'.format(self))
 

    def __str__(self):
        return json.dumps({ 'lineId': self.line_id, 'recipeClock': str(self.recipe_clock), 'lineSpec': self.line_spec, 'queue': self.queue })

    def _set_recipe_clock(self, recipe, efficiency):
        duration = Duration(recipe['time'])
        duration.apply_efficiency(efficiency)
        return DecrClock(duration)

    def _produce(self, master_clock):
        product = self.queue[0]['output']
        count = self.queue[0]['count']
        print('{}: {} produced {} {}'.format(master_clock, self.line_id, count, product))
        # print('{}: inventory before {}'.format(master_clock, self.inventory))
        self.inventory.add(product, count)
        print('{}: inventory updated {}'.format(master_clock, self.inventory))
    
    def _next_recipe(self, master_clock):
        last = self.queue.pop(0)
        self.queue.append(last)
        self.recipe_clock = self._set_recipe_clock(self.queue[0], self.line_spec['efficiency'])
        product = self.queue[0]['output']
        print('{}: {} producing {} in {}'.format(master_clock, self.line_id, product, self.recipe_clock))


    def step(self, master_clock):
        self.recipe_clock.step()
        if self.recipe_clock.to_minutes() > 0:
            #print('{}: {} producing {} in {}'.format(master_clock, self.line_id, self.queue[0]['output'], self.recipe_clock))
            pass
        else: 
            self._produce(master_clock)
            self._next_recipe(master_clock)
        