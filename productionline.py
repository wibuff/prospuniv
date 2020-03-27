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
        for item in queue:
            if item['recipe'] not in Recipes: 
                raise Exception('recipe {} not found'.format(item['recipe']))
            queuedRecipe = {
                'id': item['recipe'],
                'count': item['count'],
                'recipe': Recipes[item['recipe']]
            }
            self.queue.append(queuedRecipe)
        self.inventory = inventory
        self.recipe_clock = self._set_recipe_clock(self.queue[0], self.line_spec['efficiency'])
        print('  line initialized: {}'.format(self))
 

    def __str__(self):
        return json.dumps({ 'lineId': self.line_id, 'recipeClock': str(self.recipe_clock), 'lineSpec': self.line_spec, 'queue': self.queue })

    def _set_recipe_clock(self, active, efficiency):
        recipe = active['recipe']
        count = active['count']
        duration = Duration(recipe['time'])
        duration.apply_multiplier(count)
        duration.apply_efficiency(efficiency)
        return DecrClock(duration)

    def _produce(self, master_clock):
        active = self.queue[0]
        recipe = active['recipe']
        product = recipe['output']
        count = active['count'] * recipe['count']
        print('{}: {} produced {} {}'.format(master_clock, self.line_id, count, product))
        self.inventory.add(product, count)
        print('{}: inventory updated {}'.format(master_clock, self.inventory))
    
    def output_prod_status(self, master_clock):
        active = self.queue[0]
        runcount = active['count']
        recipe = active['recipe']
        outputcount = recipe['count']
        product = recipe['output']
        print('{}: {} producing {}x{} {} in {}'.format(master_clock, self.line_id, runcount, outputcount, product, self.recipe_clock))
    
    def _next_recipe(self, master_clock):
        last = self.queue.pop(0)
        self.queue.append(last)
        self.recipe_clock = self._set_recipe_clock(self.queue[0], self.line_spec['efficiency'])
        self.output_prod_status(master_clock)

    def step(self, master_clock):
        self.recipe_clock.step()
        if self.recipe_clock.to_minutes() > 0:
            # self.output_prod_status(master_clock)
            pass
        else: 
            self._produce(master_clock)
            self._next_recipe(master_clock)
        