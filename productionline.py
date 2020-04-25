""" a Product Line
"""

import sys
import json
from clock import DecrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes
from inventory import Inventory
from ledger import Ledger

class ProductionLine(object):
    """ ProductionLine class
    """

    def __init__(self, stream_id, line_spec, inventory, market, master_clock):
        self.line_id = line_spec['lineId']
        self.linetype = ProductionLines[self.line_id]
        self.building = Buildings[self.linetype['building']]
        self.buildingCount = line_spec['buildingCount']
        self.production = self._init_production(self.buildingCount)
        self.queue = self._init_production_queue(line_spec['queue'])
        self.ledger = Ledger(stream_id, self.line_id, self.buildingCount, market)
        self.inventory = inventory
        
        # initialize workers and efficiency before initializing production
        self.worker_efficiency = 0.0
        self.workers = self._init_workers()
        self.worker_clock = DecrClock(Duration("0"))
        self._reset_workers(master_clock)
        self.efficiency = self._calc_line_efficiency()

        for bnum in range(0, self.buildingCount):
            self._set_next_recipe_active(master_clock, bnum)
            self.production[bnum]['producing'] = self._start_next_recipe(master_clock, bnum)

        print('{} {} initialized - {} buildings'.format(master_clock, self.line_id, self.buildingCount))

    def __str__(self):
        return json.dumps({ 
            'lineId': self.line_id, 
            'efficiency': self.efficiency,
            'production': self.production,
            'workerClock': str(self.recipe_clock), 
            'linetype': self.linetype, 
            'queue': self.queue 
            })

    def _calc_line_efficiency(self):
        efficency = self.worker_efficiency * self.linetype['condition'] * \
            (1.0 + self.linetype['experts']) * (1.0 + self.linetype['soil']) * \
                (1.0 + self.linetype['cogc'])
        return efficency

    def _init_workers(self):
        workers = []
        needed = self.building['workers']
        for need in needed:
            workerType = need['type']
            workerCount = need['count'] * self.buildingCount
            if workerType not in Workers:
                raise Exception("worker {} not defined".format(workerType))
            worker = Workers[workerType]
            workers.append({'type': workerType, 'count': workerCount, 'worker': worker})
        return workers   
        
    def _produce(self, master_clock, buildingNum):
        active = self.production[buildingNum]
        recipe = active['recipe']
        product = recipe['output']
        count = active['count'] * recipe['count']

        self.inventory.add(product, count)
        self.ledger.add(master_clock, Ledger.OUTPUT, 'output produced', count=count, product=product)
    
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

    def _init_production_queue(self, queue):
        prodqueue = []
        for item in queue:
            if item['recipe'] not in Recipes: 
                raise Exception('recipe {} not found'.format(item['recipe']))
            product = {
                'id': item['recipe'],
                'count': item['count'],
                'recipe': Recipes[item['recipe']]
            }
            prodqueue.append(product)
        return prodqueue

    def _init_production(self, buildCount):
        return [{
            "recipe": None,
            "count": 0,
            "clock": DecrClock(Duration("0")),
            "producing": False
        }] * buildCount 

    def _set_recipe_clock(self, recipe, count):
        duration = Duration(recipe['time'])
        duration.apply_multiplier(count)
        duration.apply_efficiency(self.efficiency)
        return DecrClock(duration)

    def _set_next_recipe_active(self, master_clock, buildingNum):
        prod = self.queue.pop(0)
        active = self.production[buildingNum]
        active['recipe'] = prod['recipe']
        active['count'] = prod['count'] 
        active['clock']= self._set_recipe_clock(prod['recipe'], prod['count'])
        active['producing'] = False
        self.queue.append(prod)

    def _start_next_recipe(self, master_clock, buildingNum):
        active = self.production[buildingNum]
        recipe = active['recipe']
        producing = False
        if self._inputs_available(recipe['output'], recipe['inputs'], active['count']):
            # TODO capture production fees (10.00 ICA per 24 baseline production hours)
            producing = True
            self._consume_inputs(master_clock, recipe['inputs'], active['count'])
        return producing

    def _log_production_activity(self, master_clock):
        producing = True
        for prod in self.production:
            if not prod['producing']:
                producing = False
        if producing:
            self.ledger.add(master_clock, Ledger.STATUS, 'producing', state=Ledger.ACTIVE) 
        else:
            self.ledger.add(master_clock, Ledger.STATUS, 'starved', state=Ledger.INACTIVE) 

    def step(self, master_clock):
        for buildingNum in range(0, self.buildingCount):
            self._recipe_step(master_clock, buildingNum)
        self._worker_step(master_clock)
        self._log_production_activity(master_clock)

    def _recipe_step(self, master_clock, buildingNum):
        active = self.production[buildingNum]
        active['clock'].step()

        if not active['producing']:
            # not currently producing, attempt to start next item in queue
            active['producing'] = self._start_next_recipe(master_clock, buildingNum)
        elif active['clock'].to_minutes() > 0:
            # producing, time remaining 
            pass
        else: 
            # production done, produce output and attempt to start next item in queue
            active['producing'] = False
            self._produce(master_clock, buildingNum)
            self._set_next_recipe_active(master_clock, buildingNum)
            active['producing'] = self._start_next_recipe(master_clock, buildingNum)

    def _worker_step(self, master_clock):
        self.worker_clock.step()
        if self.worker_clock.to_minutes() <= 0:
            self._reset_workers(master_clock)
            self.efficiency = self._calc_line_efficiency()
        self.ledger.add(master_clock, Ledger.EFFICIENCY, 'efficiency', value=self.efficiency) 

    def _reset_workers(self, master_clock):
        """
        Can operate with not enough workers
            actual efficiency = efficiency * (num avail workers / num required workers)
        Workforce will continue working if at least one essential resource is available
        Workforce will stop working if no essential resources are available
            even if non-essentials are available
        TODO handle edge/unhappy path cases for unsupplied workers
             for now, just ensure adequate supply... :-) 
        """
        self.worker_clock = DecrClock(Duration("24:00:00"))
        worker_efficiencies = []
        for staff in self.workers:
            needs = self._calc_worker_needs(staff)
            supplies = self._determine_available_supplies(staff, needs)
            efficiency = self._consume_supplies(master_clock, staff, supplies)
            worker_efficiencies.append(efficiency)
        if len(worker_efficiencies) > 0:
            self.worker_efficiency = sum(worker_efficiencies)/len(worker_efficiencies) 
        else:
            raise Exception("{} line misconfigured, no workers".format(self.line_id))

    def _calc_worker_needs(self, staff):
        needs = []
        workertype = staff['type']
        worker = staff['worker']
        numworkers = float(staff['count'])

        for resource in worker['essentials']:
            rate = resource['rate']
            basis = resource['basis']
            amount = numworkers * rate/basis
            needs.append({ 'id': resource['id'], 'amount': amount, 'essential': True })

        for resource in worker['non-essentials']:
            rate = resource['rate']
            basis = resource['basis']
            amount = numworkers * rate/basis
            needs.append({ 'id': resource['id'], 'amount': amount, 'essential': False })

        return needs

    def _determine_available_supplies(self, staff, needs):
        supplies = []
        inv = self.inventory
        for resource in needs: 
            available = inv.count(resource['id']) 
            need = resource['amount']
            use = need
            if available < need: 
                use = available
            supplies.append({ 'id': resource['id'], 'need': need, 'use': use, 'essential': resource['essential'] })
        return supplies
            
    def _consume_supplies(self, master_clock, staff, supplies):
        worker = staff['worker']
        required_essentials = 0.0
        acquired_essentials = 0.0
        required_nonessentials = 0.0
        acquired_nonessentials = 0.0

        for resource in supplies:
            product = resource['id']
            use = resource['use']
            need = resource['need']

            # consume supplies
            if not self.inventory.remove(product, use):
                raise Exception('removing {} {} from inventory failed'.format(use, product))
            self.ledger.add(master_clock, Ledger.INPUT, 'supplies consumed', count=use, product=product, extype='opex')
            if resource['essential']:
                acquired_essentials = acquired_essentials + use
                required_essentials = required_essentials + need
            else:
                acquired_nonessentials = acquired_nonessentials + use
                required_nonessentials = required_nonessentials + need
        
        # set efficiency based on worker supply
        essentials_base_eff = worker['efficiency']
        essentials_factor = acquired_essentials/required_essentials
        essentials_mod_eff = essentials_base_eff * essentials_factor

        nonessentials_base_eff = 1.0 - worker['efficiency']
        nonessentials_factor = acquired_nonessentials/required_nonessentials
        nonessentials_mod_eff = nonessentials_base_eff * nonessentials_factor
        
        efficiency = essentials_mod_eff
        if essentials_mod_eff > 0.0:
            efficiency = essentials_mod_eff + nonessentials_mod_eff
        return efficiency
