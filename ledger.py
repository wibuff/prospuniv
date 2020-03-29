""" Ledger
"""

import sys
import json

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

    def __init__(self, stream_id, line_id):
        self.stream_id = stream_id
        self.line_id = line_id
        self.entries = []

    def __str__(self):
        return json.dumps({ 'line_id': self.line_id, 'entries': self.entries })

    def add(self, clock, type, description, value=0.0, **kwargs):
        entry = {
            'clock': str(clock),
            'type': type,
            'description': description,
            'value': value
        }
        for key, value in kwargs.items():
            entry[key] = value
        self.entries.append(entry)

    def add_ledger(self, ledger):
        self.entries.extend(ledger.entries)
    
    def output_summary(self, output_net=False):
        print("{}.{}".format(self.stream_id, self.line_id))
        summary = self.summarize_ledger()
        print('Uptime: {active_cycles}/{total_cycles} cycles ({uptime_percent:.2%})'.format(**summary))
        print("Consumed Materials:")
        for key in summary['consumption'].keys():
            print('  {:<3} {:>8}'.format(key, summary['consumption'][key]))
        print("Produced Materials:")
        for key in summary['production'].keys():
            print('  {:<3} {:>8}'.format(key, summary['production'][key]))
        if output_net:
            print("Net Materials:")
            for key in summary['net_production'].keys():
                print('  {:<3} {:>8}'.format(key, summary['net_production'][key]))
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
                active_cycles = active_cycles + entry['value']
                
            elif entry['type'] == Ledger.OUTPUT:
                product = entry['product']
                count = entry['value']
                if product in production:
                    production[product] = production[product] + count
                else:
                    production[product] = count
                if product in net_production:
                    net_production[product] = net_production[product] + count
                else:
                    net_production[product] = count

            elif entry['type'] == Ledger.INPUT:
                product = entry['product']
                count = entry['value']
                if product in consumption:
                    consumption[product] = consumption[product] + count
                else:
                    consumption[product] = count
                if product in net_production:
                    net_production[product] = net_production[product] - count
                else:
                    net_production[product] = -count

        return {
            'total_cycles': total_cycles,
            'active_cycles': active_cycles,
            'uptime_percent': float(active_cycles)/float(total_cycles),
            'production': production,
            'consumption': consumption,
            'net_production': net_production
        }

    