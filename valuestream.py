""" Value Stream Class
"""

import sys
import json
from datetime import datetime
from clock import IncrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes
from productionline import ProductionLine

class ValueStream(object):
    """ ValueStream class
    """
    def __init__(self, streamconfig, inventory, market, duration):
        self.stream_id = '{:%Y%m%d.%H%M%S.%f}'.format(datetime.now())
        print("")
        print('value stream {} initializing'.format(self.stream_id))
        self.inventory = inventory
        self.market = market
        self.duration = duration
        self.clock = IncrClock(duration)
        self.streamconfig = streamconfig
        self.lines = self._init_lines(self.streamconfig)
        
    def _init_lines(self, streamconfig):
        lines = []
        for line in streamconfig['productionLines']:
            print('configuring line {}'.format(line['lineId']))
            pline = ProductionLine(line['lineId'], line['queue'], self.inventory)
            lines.append(pline)
        return lines
        
    def calc_output(self, starting, ending):
        net = {}
        for key in ending.keys(): 
            start_val = 0
            if key in starting:
                start_val = starting[key]
            net[key] = ending[key] - start_val
        return net


    def run(self):
        start_inv = json.loads(str(self.inventory))

        print("")
        print('value stream {} started'.format(self.stream_id))
        print('{}: running value stream "{}"'.format(self.clock, self.streamconfig['description']))
        print('{}: starting inventory {}'.format(self.clock, self.inventory))

        for line in self.lines:
            line.output_prod_status(self.clock)

        while self.clock.step():
            for line in self.lines:
                line.step(self.clock)
        for line in self.lines:
            line.step(self.clock)

        print('{}: ending inventory {}'.format(self.clock, self.inventory))

        end_inv = json.loads(str(self.inventory))
        self.summarize_run(start_inv, end_inv)
        
    def summarize_run(self, start_inv, end_inv):
        print("")
        print("*** RUN SUMMARY {} ***".format(self.stream_id))
        print("")
        print("Inventories:")
        output = self.calc_output(start_inv, end_inv)
        print('starting inventory {}'.format(start_inv))
        print('ending inventory   {}'.format(end_inv))
        print('total output       {}'.format(json.dumps(output)))

        print("")
        print("Market Values:")
        mkt_values = self.calc_mkt_values(output)
        fmt = '{label:>5s}\t{prices[last]:>10.2f}\t{prices[ask]:>10.2f}\t{prices[bid]:>10.2f}\t{prices[avg]:>10.2f}'
        sfmt = '{label:<5s}\t{prices[last]:>10s}\t{prices[ask]:>10s}\t{prices[bid]:>10s}\t{prices[avg]:>10s}'
        print(sfmt.format(label='Item', prices={ 'last': 'Last', 'ask': 'Ask', 'bid': 'Bid', 'avg': 'Avg'}))
        print(fmt.format(label='Total', prices=mkt_values['totals']))
        for key in mkt_values['subtotals']: 
            label = key
            if len(label) < 3: 
                label = label + " "
            print(fmt.format(label=label, prices=mkt_values['subtotals'][key]))

    def calc_mkt_values(self, net_prod):
        totals = { 'last': 0.0, 'ask': 0.0, 'bid': 0.0, 'avg': 0.0 }
        subtotals = {}
        for key in net_prod: 
            if key not in self.market['prices']: 
                raise Exception('missing market value for {}'.format(key))

            prod = net_prod[key]            
            if prod > 0:
                prices = self.market['prices'][key]

                subtotals[key] = {}
                subtotals[key]['last'] = prod * prices[0]
                subtotals[key]['ask'] = prod * prices[1]
                subtotals[key]['bid'] = prod * prices[2]
                subtotals[key]['avg'] = prod * prices[3]

                totals['last'] = totals['last'] + prod * prices[0]
                totals['ask'] = totals['ask'] + prod * prices[1]
                totals['bid'] = totals['bid'] + prod * prices[2]
                totals['avg'] = totals['avg'] + prod * prices[3]

        return { "totals": totals, "subtotals": subtotals }
   