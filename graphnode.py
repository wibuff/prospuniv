""" Class representing a production tree graph node
"""

import sys
import json
from clock import Duration

class GraphNode(dict):
    def __init__(self, config, key, variant, input_nodes):
        dict.__init__(self, 
            template = key,
            variant = variant,
            description = "",
            inputs = {},
            outputs = {},
            efficiency = 1.0,
            time_base_mins = 0.0,
            time_mod_mins = 0.0,
            gross_value = 0.0,
            supply_cost = 0.0,
            input_cost = 0.0,
            total_cost = 0.0,
            net_value = 0.0,
            gross_value_per_unit = 0.0,
            supply_cost_per_unit = 0.0,
            input_cost_per_unit = 0.0,
            total_cost_per_unit = 0.0,
            net_value_per_unit = 0.0,
            gross_value_per_min = 0.0,
            supply_cost_per_min = 0.0,
            input_cost_per_min = 0.0,
            total_cost_per_min = 0.0,
            net_value_per_min = 0.0
        )    
        self._init_node(config, input_nodes)

    def _init_node(self, config, input_nodes):
        ticker = self['template'].split('.')[0]
        market = config['market']
        supply = config['supply']
        buildings = config['buildings']
        efficiency = config['efficiency']
        workers = config['workers']

        if '.MKT' in self['template']:
            price = market.price(ticker)
            self['description'] = self['template']
            self['outputs'][ticker] = 1
            self["input_cost"] = price.avg
            self["input_cost_per_unit"] = price.avg
            self["input_cost_per_min"] = price.avg
        else: 
            template = config['templates'][self['template']]
            self['description'] = self._init_description(template, input_nodes)
            self['inputs'] = self._init_inputs(template, input_nodes)
            self['outputs'] = self._init_outputs(template)
            self['efficiency'] = self._init_efficiency(template, buildings, efficiency)
            self['time_base_mins'] = Duration(template['time']).to_minutes()
            self['time_mod_mins'] = Duration(template['time']).to_minutes() / self['efficiency']
            self['gross_value'] = self._calc_gross_value(template, market)
            self['gross_value_per_unit'] = self._calc_gross_value_per_unit()
            self['gross_value_per_min'] = self._calc_gross_value_per_min(template)
            self['input_cost'] = self._calc_input_cost()
            self['input_cost_per_unit'] = self._calc_input_cost_per_unit()
            self['input_cost_per_min'] = self._calc_input_cost_per_min(template)
            self['supply_cost'] = self._calc_supply_cost(template, supply, buildings, workers)
            self['supply_cost_per_unit'] = self._calc_supply_cost_per_unit()
            self['supply_cost_per_min'] = self._calc_supply_cost_per_min(template)

        self['total_cost'] = self['supply_cost'] + self['input_cost']
        self['total_cost_per_unit'] = self['supply_cost_per_unit'] + self['input_cost_per_unit']
        self['total_cost_per_min'] = self['supply_cost_per_min'] + self['input_cost_per_min']
        self['net_value'] = self['gross_value'] - self['total_cost']
        self['net_value_per_unit'] = self['gross_value_per_unit'] - self['total_cost_per_unit']
        self['net_value_per_min'] = self['gross_value_per_min'] - self['total_cost_per_min']

    def _init_description(self, template, input_nodes):
        return '{}.{}<-{}'.format(self['template'], self['variant'], 
            '+'.join(map(lambda node: node['template'] + '.' + str(node['variant']), input_nodes)))

    def _init_inputs(self, template, input_nodes): 
        inputs = {}
        for input in template['inputs']:
            for in_node in input_nodes:
                if input['id'] in in_node['outputs']:
                    inputs[input['id']] = {
                        'count': input['count'],
                        'node': in_node
                    }
        return inputs

    def _init_outputs(self, template):
        outputs = {}
        for output in template['outputs']:
            outputs[output['id']] = output['count']
        return outputs

    def _init_efficiency(self, template, buildings, efficiency):
        value = 1.0
        prodline = template['line']
        building = buildings[prodline]
        expertise = building['expertise']
        # TODO fix hard code for Promitor
        site_efficiency = efficiency['Promitor']

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

        return value
        
    def _calc_gross_value(self, template, market):
        value = 0.0
        for output in template['outputs']:
            price = market.price(output['id'])
            value = value + price.avg * output['count']
        return value

    def _calc_gross_value_per_unit(self):
        value = self['gross_value']
        num_units = 0
        for output in self['outputs'].keys():
            num_units = num_units + self['outputs'][output]
        return value / float(num_units)

    def _calc_gross_value_per_min(self, template):
        value = self['gross_value']
        duration = Duration(template['time'])
        efficiency = self['efficiency']
        num_mins = duration.to_minutes() / efficiency
        return value / float(num_mins)

    def _calc_input_cost(self): 
        cost = 0.0
        for ticker in self['inputs']:
            input = self['inputs'][ticker]
            cost = cost + input['count'] * input['node']['total_cost']
        return cost

    def _calc_input_cost_per_unit(self):
        value = self['input_cost']
        num_units = 0
        for output in self['outputs'].keys():
            num_units = num_units + self['outputs'][output]
        return value / float(num_units)

    def _calc_input_cost_per_min(self, template):
        value = self['input_cost']
        duration = Duration(template['time'])
        efficiency = self['efficiency']
        num_mins = duration.to_minutes() / efficiency
        return value / float(num_mins)

    def _calc_supply_cost(self, template, supply, buildings, workers): 
        cost = 0.0
        prodline = template['line']
        building = buildings[prodline]
        workertypes = building['workers']
        # sum up supply costs for all supplies for all workers for 24 hours
        for workertype in workertypes:
            wtype = workertype['type']
            wcount = workertype['count']
            # TODO handle location correctly (don't hardcode Prom)
            worker = workers['Promitor'][wtype]
            # sum up daily consumption for both essential and non-essential supplies
            # TODO consider separate valuation for essentials only
            for need in worker['needs']:
                rate = need['rate']
                basis = need['basis']
                ticker = need['id']
                price = supply[ticker]
                cost = cost + price * rate * wcount / basis 
        
        # adjust cost for production duration 
        duration = Duration(template['time'])
        num_mins = duration.to_minutes()
        ratio = num_mins / (24 * 60)
        return cost * ratio

    def _calc_supply_cost_per_unit(self):
        value = self['supply_cost']
        num_units = 0
        for output in self['outputs'].keys():
            num_units = num_units + self['outputs'][output]
        return value / float(num_units)

    def _calc_supply_cost_per_min(self, template):
        value = self['supply_cost']
        duration = Duration(template['time'])
        efficiency = self['efficiency']
        num_mins = duration.to_minutes() / efficiency
        return value / float(num_mins)

    OUTPUT_FIELDS = [
        'outputs',
        'template',
        'variant',
        'description',
        'efficiency',
        'time_base_mins',
        'time_mod_mins',
        'gross_value',
        'supply_cost',
        'input_cost',
        'total_cost',
        'net_value',
        'gross_value_per_unit',
        'supply_cost_per_unit',
        'input_cost_per_unit',
        'total_cost_per_unit',
        'net_value_per_unit',
        'gross_value_per_min',
        'supply_cost_per_min',
        'input_cost_per_min',
        'total_cost_per_min',
        'net_value_per_min'
    ]

    def to_csv_header(self):
        return ",".join(GraphNode.OUTPUT_FIELDS)

    def to_csv_record(self):
        values = []
        for field in GraphNode.OUTPUT_FIELDS:
            if field == 'outputs':
                values.append('.'.join(self['outputs']))
            else:
                values.append(str(self[field]))
        return ",".join(values)