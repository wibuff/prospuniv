""" Value Stream Class
"""

import json
from datetime import datetime
from clock import IncrClock
from inventory import Inventory
from productionline import ProductionLine
from market import Price
from ledger import Ledger

class ValueStream(object):
    """ ValueStream class
    """
    def __init__(self, config):
        self.stream_id = '{:%Y%m%d.%H%M%S.%f}'.format(datetime.now())
        self.config = config
        self.outfile = config['outfile']
        self.config_date = config['config-date']

        print("", file=self.outfile)
        print('value stream {} initializing'.format(self.stream_id), file=self.outfile)
        self.inventory = config['inventory']
        self.market = config['market']
        self.duration = config['duration']
        self.clock = IncrClock(config['duration'])
        self.streamconfig = config['valstream']

    def _init_lines(self, streamconfig):
        lines = []
        for line_spec in streamconfig['productionLines']:
            pline = ProductionLine(self.stream_id, line_spec, self.config, self.clock)
            lines.append(pline)
        return lines

    def run(self):
        """ runs the value stream simulation """
        start_inv = Inventory(json.loads(str(self.inventory)))
        lines = self._init_lines(self.streamconfig)

        print("", file=self.outfile)
        print('{} value stream {} run started'
              .format(self.clock, self.stream_id), file=self.outfile)
        print('{} description "{}"'
              .format(self.clock, self.streamconfig['description']), file=self.outfile)

        while self.clock.step():
            for line in lines:
                line.step(self.clock)
        for line in lines:
            line.step(self.clock)

        print('{} value stream {} run complete'
              .format(self.clock, self.stream_id), file=self.outfile)
        end_inv = Inventory(json.loads(str(self.inventory)))
        self.summarize_run(lines, start_inv, end_inv)

    def log_run(self, summary):
        """ log the run to the run logs file """
        with open('logs/runlog.txt', mode='a') as logfile:
            print(summary, file=logfile)

    def summarize_run(self, lines, start_inv, end_inv):
        """ summarize and report on the summary """
        print('', file=self.outfile)
        print('*** RUN SUMMARY {} ***'.format(self.stream_id), file=self.outfile)
        print('', file=self.outfile)

        print('Value Stream Summary:', file=self.outfile)
        stream_ledger = Ledger(self.stream_id, 'RUN.TOTALS', None, None, self.market)
        for line in lines:
            stream_ledger.add_ledger(line.ledger)
        stream_summary = stream_ledger.output_summary(self.duration, self.outfile)

        print('', file=self.outfile)
        print('Production Line Summaries:', file=self.outfile)
        line_summary = []
        for line in lines:
            line.ledger.output_summary(self.duration, self.outfile)
            line_summary.append(line.line_identity())
            print("", file=self.outfile)

        print('Inventory Summaries:', file=self.outfile)
        start_inv.output_summary('Starting Assets', self.market, self.outfile)
        end_inv.output_summary('Ending Assets', self.market, self.outfile)
        net_inv = end_inv.diff(start_inv)
        net_inv.output_summary('Asset Changes', self.market, self.outfile)

        self.log_run({
            'net': '{:5.2f}'.format(stream_summary['net']),
            'fp': '-'.join(line_summary),
            'uptime': stream_summary['uptime'],
            'e-start': '{:5.2%}'.format(stream_summary['e-start']),
            'e-delta': '{:5.2%}'.format(stream_summary['e-delta']),
            'cdate': self.config_date,
            'id': self.stream_id
        })

    def calc_output(self, starting, ending):
        """ calculate valuestream outputs """
        net = {}
        for key in ending.keys():
            start_val = 0
            if key in starting:
                start_val = starting[key]
            net[key] = ending[key] - start_val
        return net

    def calc_mkt_values(self, net_prod):
        """ calculate the market values of the produced outputs """
        total = Price()
        subtotals = {}
        for product in net_prod:
            num_produced = net_prod[product]
            if num_produced > 0:
                price = self.market.price(product)
                subtotal = price.multiply(num_produced)
                subtotals[product] = subtotal
                total = total.add(subtotal)
        return {"totals": total, "subtotals": subtotals}
   