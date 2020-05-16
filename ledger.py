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
    MISSING_INPUT = "missing_input"
    NOTE = "note"

    ACTIVE = 1
    INACTIVE = 0

    def __init__(self, stream_id, line_id, buildingCount, market):
        self.stream_id = stream_id
        self.line_id = line_id
        self.buildingCount = buildingCount
        self.market = market
        self.entries = []
        self.start_efficiency = None
        self.end_efficiency = None

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

        # update efficiency summary
        if entry['type'] == Ledger.EFFICIENCY and self.start_efficiency is None:
            self.start_efficiency = entry['value']
        if entry['type'] == Ledger.EFFICIENCY:
            self.end_efficiency = entry['value']


    def add_ledger(self, ledger):
        # merge efficiency numbers between the ledgers
        if self.start_efficiency is None:
            self.start_efficiency = ledger.start_efficiency
        elif ledger.start_efficiency is not None:
            self.start_efficiency = (self.start_efficiency + ledger.start_efficiency)/2
        if self.end_efficiency is None:
            self.end_efficiency = ledger.end_efficiency
        elif ledger.end_efficiency is not None:
            self.end_efficiency = (self.end_efficiency + ledger.end_efficiency)/2
        # add the passed ledger to self
        self.entries.extend(ledger.entries)
    
    def output_summary(self, duration, outfile):
        summary = self.summarize_ledger()
        building = 'Summarization'
        if self.line_id in ProductionLines:
            building = Buildings[ProductionLines[self.line_id]['building']]['name']

        if self.buildingCount: 
            line = "{}.{} ({} x {})".format(self.stream_id, self.line_id, self.buildingCount, building)
        else: 
            line = "{}.{} ({})".format(self.stream_id, self.line_id, building)

        uptime =      'Uptime     : {active_cycles}/{total_cycles} cycles ({uptime_percent:.2%})'.format(**summary)
        efficiency =  'Efficiency : \u03B1 {start:5.2%} \u03C9 {end:5.2%} \u0394 {delta:5.2%} '.format(**summary['efficiencies'])
        price_head =  '                   {}'.format(Price.HEADER_FMT)
        total_value = 'Production Value : {total_production_value}'.format(**summary)
        total_cost =  'Production Cost  : {total_production_cost}'.format(**summary)
        gain_loss =   'Net Gain/Loss    : {total_gain_loss}'.format(**summary)

        report = Report(outfile)
        report.start()
        report.output_general(line)
        report.output_general(uptime)
        report.output_general(efficiency)
        report.output_general("")
        report.output_general(price_head)
        report.output_general(total_value)
        report.output_general(total_cost)
        report.output_general(gain_loss)
        report.major_break() 
        report.output_value_table_w_perday(summary['production'], "Produced Materials", duration)
        report.major_break() 
        report.output_value_table_w_perday(summary['consumption'], "Consumed Materials", duration)
        report.major_break() 
        report.output_value_table_w_perday(summary['net_production'], "Net Materials", duration)

        if len(summary['missing']) > 0:
            report.major_break() 
            report.output_general('Missing Inputs:')
            report.major_break()
            for missing in summary['missing']:
                report.output_general(missing)

        report.end()
        return {
            'net': summary['total_gain_loss'].avg,
            'uptime': summary['uptime_percent'],
            'e-start': summary['efficiencies']['start'],
            'e-delta': summary['efficiencies']['delta']
        }

    def summarize_ledger(self):
        total_cycles = 0
        active_cycles = 0
        efficiencies = []
        production = {}
        consumption = {}
        net_production = {}
        total_production_value = Price()
        total_production_cost = Price()
        missing = []

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
                total_production_value = total_production_value.add(value)
                
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
                count = -entry['count']
                price = self.market.price(product)
                value = price.multiply(count)
                total_production_cost = total_production_cost.add(value)

                if product in consumption:
                    consumption[product]['count'] = consumption[product]['count'] + count
                    consumption[product]['value'] = consumption[product]['value'].add(value)
                else:
                    consumption[product] = {}
                    consumption[product]['count'] = count
                    consumption[product]['value'] = value

                if product in net_production:
                    net_production[product]['count'] = net_production[product]['count'] + count
                    net_production[product]['value'] = net_production[product]['value'].add(value)
                else:
                    net_production[product] = {}
                    net_production[product]['count'] = -count
                    net_production[product]['value'] = value

            elif entry['type'] == Ledger.MISSING_INPUT:
                msg = '{0[clock]} {0[line]} needs {0[count]} {0[ticker]} ({0[available]} available)'.format(entry)
                missing.append(msg)
                

        total_gain_loss = total_production_value.add(total_production_cost)
        return {
            'total_cycles': total_cycles,
            'active_cycles': active_cycles,
            'uptime_percent': float(active_cycles)/float(total_cycles),
            'efficiencies': self._summarize_efficiencies(efficiencies),
            'production': production,
            'consumption': consumption,
            'net_production': net_production,
            'total_production_value': total_production_value,
            'total_production_cost': total_production_cost,
            'total_gain_loss': total_gain_loss,
            'missing': missing
        }

    def _summarize_efficiencies(self, efficiencies):
        result = {}
        if len(efficiencies) > 0:
            result['mean'] = sum(efficiencies)/len(efficiencies)
            result['min'] = min(efficiencies)
            result['max'] = max(efficiencies)
            result['start'] = self.start_efficiency
            result['end'] = self.end_efficiency
            result['delta'] = self.end_efficiency - self.start_efficiency
        return result
            
