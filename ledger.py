""" Ledger
"""

import sys
import json
from market import Price
from reportgen import Report
from configuration import Buildings, ProductionLines

class Ledger(object):
    """ Ledger Class
    """
    REVENUE = "revenue"
    EXPENSE = "expense"
    INPUT = "input"
    OUTPUT = "output"
    STATUS = "status"
    EFFICIENCY = "efficiency"
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
    
    def output_summary(self):
        summary = self.summarize_ledger()
        building = 'Summarization'
        if self.line_id in ProductionLines:
            building = Buildings[ProductionLines[self.line_id]['building']]['name']

        line = "{}.{} ({})".format(self.stream_id, self.line_id, building)
        uptime =     'Uptime: {active_cycles}/{total_cycles} cycles ({uptime_percent:.2%})'.format(**summary)
        efficiency = 'Efficiency: {min:5.2%} / {mean:5.2%} / {max:5.2%} [min/mean/max]'.format(**summary['efficiencies'])

        report = Report()
        report.start()
        report.output_general(line)
        report.output_general(uptime)
        report.output_general(efficiency)
        report.major_break() 
        report.output_value_table(summary['consumption'], "Consumed Materials")
        report.major_break() 
        report.output_value_table(summary['production'], "Produced Materials")
        report.major_break() 
        report.output_value_table(summary['net_production'], "Net Materials")
        report.end()

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
        efficiencies = []
        production = {}
        consumption = {}
        net_production = {}

        for entry in self.entries: 
            if entry['type'] == Ledger.STATUS:
                total_cycles = total_cycles + 1
                active_cycles = active_cycles + entry['state']
                
            if entry['type'] == Ledger.EFFICIENCY:
                efficiencies.append(entry['value'])
                
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
            'efficiencies': self._summarize_efficiencies(efficiencies),
            'production': production,
            'consumption': consumption,
            'net_production': net_production
        }

    def _summarize_efficiencies(self, efficiencies):
        result = {}
        if len(efficiencies) > 0:
            result['mean'] = sum(efficiencies)/len(efficiencies)
            result['min'] = min(efficiencies)
            result['max'] = max(efficiencies)
            result['start'] = efficiencies[0]
            result['end'] = efficiencies[len(efficiencies)-1]
        return result
            
