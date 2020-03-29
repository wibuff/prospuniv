""" Ledger
"""

import sys
import json
from market import Price

class Ledger(object):
    """ Ledger Class
    """
    CREDIT = "credit"
    DEBIT = "debit"
    INPUT = "input"
    OUTPUT = "output"
    STATUS = "status"
    NOTE = "note"

    ACTIVE = 1
    INACTIVE = 0

    def __init__(self, stream_id, line_id, market):
        self.stream_id = stream_id
        self.line_id = line_id
        self.market = market
        self.entries = []

    def __str__(self):
        return json.dumps({ 'line_id': self.line_id, 'entries': self.entries })

    def add(self, clock, type, description, **kwargs):
        entry = {
            'clock': str(clock),
            'type': type,
            'description': description,
        }
        for key, value in kwargs.items():
            entry[key] = value
        self.entries.append(entry)

    def add_ledger(self, ledger):
        self.entries.extend(ledger.entries)
    
    HEADFMT = '{:<5} {:>8} {:>12s} {:>12s} {:>12s} {:>12s}'
    HEAD = HEADFMT.format('Item', 'Count', 'Last', 'Ask', 'Bid', 'Avg')
    BREAK = u'\u2550' * len(HEAD)
    MBREAK = u'\u2500' * len(HEAD)
    #BREAKFMT = '{:<5}\u2550{:>8}\u2550{:>12s}\u2550{:>12s}\u2550{:>12s}\u2550{:>12s}'
    #BREAK = BREAKFMT.format(u'\u2550'*5, u'\u2550'*8, u'\u2550'*12, u'\u2550'*12, u'\u2550'*12, u'\u2550'*12)
    # MBREAK = BREAKFMT.format(u'\u2500'*5, u'\u2500'*8, u'\u2500'*12, u'\u2500'*12, u'\u2500'*12, u'\u2500'*12)
    BODYFMT = '  {product:<3} {count:>8} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f}'
    TOTFMT = '{product:<5} {count:>8} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f}'

    def _output_table(self, summary, name): 
        total_count = 0
        total_prices = Price([0.0,0.0,0.0,0.0])
        
        print("{}:".format(name))
        print(self.BREAK)
        print(self.HEAD)
        for key in summary.keys():
            total_count = total_count + summary[key]['count']
            total_prices = total_prices.add(summary[key]['value'])
            print(self.BODYFMT.format(
                product=key, 
                count = summary[key]['count'], 
                price = summary[key]['value']))
        print(self.MBREAK)
        print(self.TOTFMT.format(product='TOTAL', count = total_count, price = total_prices))
        print(self.BREAK)

    def output_summary(self, output_net=False):
        print("{}.{}".format(self.stream_id, self.line_id))
        summary = self.summarize_ledger()
        print('Uptime: {active_cycles}/{total_cycles} cycles ({uptime_percent:.2%})'.format(**summary))
        self._output_table(summary['consumption'], "Consumed Materials")
        self._output_table(summary['production'], "Produced Materials")
        if output_net:
            self._output_table(summary['net_production'], "Net Materials")

        """
        print("")
        for entry in self.entries: 
            if entry['type'] == Ledger.OUTPUT or entry['type'] == Ledger.INPUT:
                print('{0[clock]} {0[type]:<10s} {0[description]:<20s} {0[value]:8d} {0[product]:<3s}'.format(entry))
            elif entry['type'] == Ledger.STATUS:
                # print('{0[clock]} {0[type]:<10s} {0[description]:<20s} {0[value]:8d}'.format(entry))
                pass
            else:
                print('{0[clock]} {0[type]:<10s} {0[description]:<20s} {0[value]:8.2}'.format(entry))
        """

    def summarize_ledger(self):
        total_cycles = 0
        active_cycles = 0
        production = {}
        consumption = {}
        net_production = {}

        for entry in self.entries: 
            if entry['type'] == Ledger.STATUS:
                total_cycles = total_cycles + 1
                active_cycles = active_cycles + entry['state']
                
            elif entry['type'] == Ledger.OUTPUT:
                product = entry['product']
                count = entry['count']
                price = self.market.price(product)
                value = price.multiply(count)

                if product in production:
                    production[product]['count'] = production[product]['count'] + count
                    production[product]['value'] = production[product]['value'].add(value)
                else:
                    production[product] = {}
                    production[product]['count'] = count
                    production[product]['value'] = value
                    
                if product in net_production:
                    net_production[product]['count'] = net_production[product]['count'] + count
                    net_production[product]['value'] = net_production[product]['value'].add(value)
                else:
                    net_production[product] = {}
                    net_production[product]['count'] = count
                    net_production[product]['value'] = value

            elif entry['type'] == Ledger.INPUT:
                product = entry['product']
                count = entry['count']
                price = self.market.price(product)
                value = price.multiply(-count)

                if product in consumption:
                    consumption[product]['count'] = consumption[product]['count'] + count
                    consumption[product]['value'] = consumption[product]['value'].add(value)
                else:
                    consumption[product] = {}
                    consumption[product]['count'] = count
                    consumption[product]['value'] = value

                if product in net_production:
                    net_production[product]['count'] = net_production[product]['count'] - count
                    net_production[product]['value'] = net_production[product]['value'].add(value)
                else:
                    net_production[product] = {}
                    net_production[product]['count'] = -count
                    net_production[product]['value'] = value

        return {
            'total_cycles': total_cycles,
            'active_cycles': active_cycles,
            'uptime_percent': float(active_cycles)/float(total_cycles),
            'production': production,
            'consumption': consumption,
            'net_production': net_production
        }

    