""" Class representing a production tree graph node
"""

import sys
import json

class GraphNode(dict):
    def __init__(self, config, key, variant, input_nodes):
        dict.__init__(self, 
            template = key,
            variant = variant,
            description = "",
            inputs = {},
            outputs = {},
            gross_value = 0.0,
            supply_cost = 0.0,
            input_cost = 0.0,
            total_cost = 0.0,
            net_value = 0.0,
            gross_value_per_unit = 0.0,
            supply_cost_per_unit = 0.0,
            input_cost_per_unit = 0.0,
            total_cost_per_unit = 0.0,
            net_value_per_unit = 0.0
        )    
        self._init_node(config, input_nodes)

    def _init_node(self, config, input_nodes):
        ticker = self['template'].split('.')[0]
        market = config['market']
        if '.MKT' in self['template']:
            price = market.price(ticker)
            self['description'] = self['template']
            self['outputs'][ticker] = 1
            self["input_cost"] = price.avg
            self["input_cost_per_unit"] = price.avg
        else: 
            template = config['templates'][self['template']]
            self['description'] = self._init_description(template, input_nodes)
            self['inputs'] = self._init_inputs(template, input_nodes)
            self['outputs'] = self._init_outputs(template)
            self['gross_value'] = self._calc_gross_value(template, market)
            self['gross_value_per_unit'] = self._calc_gross_value_per_unit()
            self['input_cost'] = self._calc_input_cost()
            self['input_cost_per_unit'] = self._calc_input_cost_per_unit()

        self['total_cost'] = self['supply_cost'] + self['input_cost']
        self['total_cost_per_unit'] = self['supply_cost_per_unit'] + self['input_cost_per_unit']
        self['net_value'] = self['gross_value'] - self['total_cost']
        self['net_value_per_unit'] = self['gross_value_per_unit'] - self['total_cost_per_unit']

    def _init_description(self, template, input_nodes):
        return '{}<-{}'.format(self['template'], '+'.join(map(lambda x: x['template'], input_nodes)))

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
