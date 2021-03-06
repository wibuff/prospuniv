""" a Product Line
"""

import sys
import json
import math
from clock import DecrClock, Duration
from configuration import Buildings, Workers, Recipes
from inventory import Inventory
from ledger import Ledger

class ProductionLine(object):
    """ ProductionLine class
    """

    def __init__(self, stream_id, line_spec, config, master_clock):
        self.line_id = line_spec['line-id']
        self.linetype = line_spec['line-type']
        self.site_name = line_spec['site-name']
        self.site_efficiency = config['efficiency'][self.site_name]
        self.building = Buildings[self.linetype]
        self.building_count = line_spec['buildingCount'] #TODO change camel to kebab case
        self.production = self._init_production(self.building_count)
        self.queue_identity = ''
        self.queue = self._init_production_queue(line_spec['queue'])
        self.ledger = Ledger(stream_id, self.line_id, self.linetype, self.building_count, config['market'])
        self.inventory = config['inventory']
        self.sourcing_strategy = config['sourcing-strategy']
        self.essentials_strategy = config['essentials-strategy']
        self.non_essentials_strategy = config['non-essentials-strategy']
        
        # initialize workers and efficiency before initializing production
        self.worker_efficiency = 0.0
        self.workers = self._init_workers()
        self.worker_clock = DecrClock(Duration("0"))
        self._reset_workers(master_clock)
        self.efficiency = self._calc_line_efficiency()

        for bnum in range(0, self.building_count):
            self._set_next_recipe_active(master_clock, bnum)
            self.production[bnum]['producing'] = \
                self._start_next_recipe(master_clock, bnum, last_round_producing=False)

        print('{} {} initialized - {} buildings'.format(master_clock, self.line_id, self.building_count),
            file=config['outfile'])

    def __str__(self):
        return json.dumps({ 
            'lineId': self.line_id, 
            'efficiency': self.efficiency,
            'production': self.production,
            'linetype': self.linetype, 
            'queue': self.queue 
            })

    def line_identity(self):
        return self.linetype + str(self.building_count) + "[" + self.queue_identity + "]"

    def _calc_line_efficiency(self):
        value = 1.0
        building = self.building
        expertise = building['expertise']
        site_efficiency = self.site_efficiency

        # COGC Worker Efficiencies
        for worker in building['workers']:
            factor = 1.0 + site_efficiency['cogc-worker-bonus'][worker['type']]
            value = value * factor
            
        # COGC Industry Efficiencies
        factor = 1.0 + site_efficiency['cogc-industry-bonus'][expertise]
        value = value * factor

        # Expert Efficiencies
        experts = site_efficiency['experts'][expertise]
        factor = 1.0 + site_efficiency['expert-factors'][experts]
        value = value * factor

        # Soil Fertility Efficiencies
        if expertise == 'AGRICULTURE':
            factor = 1.0 + site_efficiency['soil-fertility']
            value = value * factor

        value = value * self.worker_efficiency
        if value < 0.33:
            return 0.33
        return value

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
        self.queue_identity = '.'.join(map(lambda x: x['id'].replace('.', '') + "x" + str(x['count']), prodqueue))
        return prodqueue

    def _init_production(self, buildCount):
        return [{
            "recipe": None,
            "count": 0,
            "clock": DecrClock(Duration("0")),
            "producing": False
        }] * buildCount 

    def _init_workers(self):
        workers = []
        needed = self.building['workers']
        for need in needed:
            workerType = need['type']
            workerCount = need['count'] * self.building_count
            if workerType not in Workers[self.site_name]:
                raise Exception("worker {} not defined".format(workerType))
            worker = Workers[self.site_name][workerType]
            workers.append({'type': workerType, 'count': workerCount, 'worker': worker})
        return workers   
        
    def step(self, master_clock):
        for buildingNum in range(0, self.building_count):
            self._recipe_step(master_clock, buildingNum)
        self._worker_step(master_clock)
        self._log_production_activity(master_clock)

    def _recipe_step(self, master_clock, buildingNum):
        active = self.production[buildingNum]
        if not active['producing']:
            # not currently producing, attempt to start producing
            active['producing'] = self._start_next_recipe(master_clock, buildingNum, last_round_producing=False)

        if active['producing']:
            # producing, decrement the active recipe clock and check for completion
            active['clock'].step()
            if active['clock'].to_minutes() > 0:
                # still producing, time remaining 
                pass
            else: 
                # production done, produce output and attempt to start next item in queue
                active['producing'] = False
                self._produce(master_clock, buildingNum)
                self._set_next_recipe_active(master_clock, buildingNum)
                active['producing'] = self._start_next_recipe(master_clock, buildingNum, last_round_producing=True)

    def _produce(self, master_clock, buildingNum):
        active = self.production[buildingNum]
        recipe = active['recipe']
        outputs = recipe['outputs']
        for output in outputs:
            product = output['id']
            count = active['count'] * output['count']
            self.inventory.add(product, count)
            self.ledger.add(master_clock, Ledger.OUTPUT, 'output produced', count=count, product=product)
    
    def _consume_inputs(self, master_clock, inputs, num_runs):
        for input in inputs: 
            product = input['id']
            count = input['count'] * num_runs
            if not self.inventory.remove(product, count):
                raise Exception('removing {} {} from inventory failed'.format(count, product))
            self.ledger.add(master_clock, Ledger.INPUT, 'input consumed', count=count, product=product)

    def _inputs_available(self, inputs, num_runs):
        status = {
            'available': True,
            'missing': []
        }
        for input in inputs: 
            product = input['id']
            count = input['count'] * num_runs
            available = self.inventory.count(product)
            if available - count < 0:
                status['available'] = False
                status['missing'].append({ "ticker": product, "count": count, "available": available})
        return status

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

    def _start_next_recipe(self, master_clock, buildingNum, last_round_producing=False):
        active = self.production[buildingNum]
        recipe = active['recipe']
        producing = False

        input_status = self._inputs_available(recipe['inputs'], active['count'])
        if not input_status['available'] and self.sourcing_strategy == 'market':
            # not enough inventory to start production
            # sourcing strategy is to acquire missing inputs from market
            for missing in input_status['missing']:
                product = missing['ticker']
                count = missing['count']
                available = missing['available']
                purchase = count - available
                self.inventory.add(product, purchase)
                self.ledger.add(master_clock, Ledger.PURCHASE_INPUT, 'input purchased', 
                                line=self.line_id, bnum=buildingNum, count=purchase, 
                                product=product, need=count, available=available)
            input_status = self._inputs_available(recipe['inputs'], active['count'])

        if input_status['available']:
            # inputs available, consume them from inventory
            producing = True
            self._consume_inputs(master_clock, recipe['inputs'], active['count'])
            # TODO capture production fees (10.00 ICA per 24 baseline production hours)
        elif last_round_producing:
            # not enough inventory to start production
            # sourcing strategy is default or inventory-only
            # capture missing input if we are not able to produce and were producing last step
            for missing in input_status['missing']:
                self.ledger.add(master_clock, Ledger.MISSING_INPUT, 'missing', 
                    line=self.line_id, bnum=buildingNum, ticker=missing['ticker'], 
                    count=missing['count'], need=missing['count'], available=missing['available'])
        return producing

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
        worker = staff['worker']
        numworkers = float(staff['count'])
        for resource in worker['needs']:
            rate = resource['rate']
            basis = resource['basis']
            amount = numworkers * rate/basis
            essential = resource['essential']
            needs.append({'id': resource['id'], 'amount': amount, 'essential': essential})
        return needs

    def _determine_available_supplies(self, staff, needs):
        supplies = []
        inv = self.inventory
        for resource in needs: 
            essential = resource['essential']
            available = inv.count(resource['id']) 
            need = resource['amount']
            use = need
            if available < need: 
                use = available
            supply = { 'id': resource['id'], 'need': need, 'use': use, 'essential': essential }
            supplies.append(supply)
        return supplies
            
    def _consume_supplies(self, master_clock, staff, supplies):
        worker = staff['worker']
        essentials = {'required': 0.0, 'acquired': 0.0}
        non_essentials = {'required': 0.0, 'acquired': 0.0}

        for supply in supplies:
            product = supply['id']
            essential = supply['essential']
            need = supply['need']
            use = supply['use']

            # check for not enough supply
            if use < need and essential and self.essentials_strategy == 'market' or \
               use < need and not essential and self.non_essentials_strategy == 'market':
                # 'market' strategy in place - purchase supplies 
                purchase = math.ceil(need - use)
                self.inventory.add(product, purchase)
                self.ledger.add(master_clock, Ledger.PURCHASE_SUPPLY, 'supply purchased', 
                                line=self.line_id, count=purchase, 
                                product=product, need=need, available=use)
                use = need
            elif use < need:
                # 'default' or other strategy in place - rely on inventory only
                self.ledger.add(master_clock, Ledger.MISSING_SUPPLY, 'missing', 
                    line=self.line_id, ticker=product, count=need-use, 
                    need=need, available=use)

            # consume supplies
            if not self.inventory.remove(product, use):
                raise Exception('removing {} {} from inventory failed'.format(use, product))
            self.ledger.add(master_clock, Ledger.INPUT, 'supplies consumed', 
                            count=use, product=product, extype='opex')

            # track consumption metrics for for efficiency calc
            if essential:
                essentials['acquired'] = essentials['acquired'] + use
                essentials['required'] = essentials['required'] + need
            else:
                non_essentials['acquired'] = non_essentials['acquired'] + use
                non_essentials['required'] = non_essentials['required'] + need
        
        return self._calc_worker_efficiency(worker, essentials, non_essentials)

    def _calc_worker_efficiency(self, worker, essentials, non_essentials):
        # set efficiency based on worker supply
        essentials_base_eff = worker['efficiency']
        essentials_factor = essentials['acquired']/essentials['required']
        essentials_mod_eff = essentials_base_eff * essentials_factor

        nonessentials_base_eff = 1.0 - worker['efficiency']
        nonessentials_factor = non_essentials['acquired']/non_essentials['required']
        nonessentials_mod_eff = nonessentials_base_eff * nonessentials_factor
        
        efficiency = essentials_mod_eff
        if essentials_mod_eff > 0.0:
            efficiency = essentials_mod_eff + nonessentials_mod_eff
        return efficiency

    def _log_production_activity(self, master_clock):
        producing = True
        for prod in self.production:
            if not prod['producing']:
                producing = False
        if producing:
            self.ledger.add(master_clock, Ledger.STATUS, 'producing', state=Ledger.ACTIVE) 
        else:
            self.ledger.add(master_clock, Ledger.STATUS, 'starved', state=Ledger.INACTIVE) 

