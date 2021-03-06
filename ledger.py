""" Ledger
"""

import json
from market import Price
from report import Report
from configuration import Buildings

class Ledger(object):
    """ Ledger Class
    """
    INPUT = "input"
    OUTPUT = "output"
    STATUS = "status"
    EFFICIENCY = "efficiency"
    MISSING_INPUT = "missing_input"
    MISSING_SUPPLY = "missing_supply"
    PURCHASE_INPUT = "purchase_input"
    PURCHASE_SUPPLY = "purchase_supply"

    ACTIVE = 1
    INACTIVE = 0

    def __init__(self, stream_id, line_id, line_type, building_count, market):
        self.stream_id = stream_id
        self.line_id = line_id
        self.line_type = line_type
        self.building_count = building_count
        self.market = market
        self.entries = []
        self.start_efficiency = None
        self.end_efficiency = None

    def __str__(self):
        return json.dumps({'line_id': self.line_id, 'entries': self.entries})

    def add(self, clock, itemtype, description, **kwargs):
        """ adds items to the ledger """
        entry = {
            'clock': str(clock),
            'type': itemtype,
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
        """ merges two ledgers, adding one to the current instance """
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
        """ outputs a summary of the ledger to the provided outfile """
        summary = self.summarize_ledger()
        building = 'Summarization'
        if self.line_type:
            building = self.line_type

        if self.building_count:
            line = "{}.{} ({} x {})"\
                .format(self.stream_id, self.line_id, self.building_count, building)
        else:
            line = "{}.{} ({})".format(self.stream_id, self.line_id, building)

        uptime = 'Uptime     : {active_cycles}/{total_cycles} cycles ({uptime_percent:.2%})'\
            .format(**summary)
        efficiency = 'Efficiency : \u03B1 {start:5.2%} \u03C9 {end:5.2%} \u0394 {delta:5.2%} '\
            .format(**summary['efficiencies'])
        price_head = '                   {}'.format(Price.HEADER_FMT)
        total_value = 'Production Value : {total_production_value}'.format(**summary)
        total_cost = 'Production Cost  : {total_production_cost}'.format(**summary)
        total_purchases = 'Purchases Cost   : {total_purchases}'.format(**summary)
        gain_loss = 'Net Gain/Loss    : {total_gain_loss}'.format(**summary)

        report = Report(outfile)
        report.start()
        report.output_general(line)
        report.output_general(uptime)
        report.output_general(efficiency)
        report.output_general("")
        report.output_general(price_head)
        report.output_general(total_value)
        report.output_general(total_cost)
        report.output_general(total_purchases)
        report.output_general(gain_loss)
        report.major_break()
        report.output_value_table_w_perday(summary['production'], "Produced Materials", duration)
        report.major_break()
        report.output_value_table_w_perday(summary['consumption'], "Consumed Materials", duration)
        if len(summary['purchases'].keys()) > 0:
            report.major_break()
            report.output_value_table_w_perday(summary['purchases'], "Purchases", duration)
        report.major_break()
        report.output_value_table_w_perday(summary['net_production'], "Net Materials", duration)

        if len(summary['missing_inputs']) > 0:
            report.major_break()
            report.output_general('Missing Inputs:')
            report.major_break()
            for missing in summary['missing_inputs']:
                report.output_general(missing)

        if len(summary['missing_supplies']) > 0:
            report.major_break()
            report.output_general('Missing Supplies:')
            report.major_break()
            for missing in summary['missing_supplies']:
                report.output_general(missing)

        report.end()
        return {
            'net': summary['total_gain_loss'].avg,
            'uptime': summary['uptime_percent'],
            'e-start': summary['efficiencies']['start'],
            'e-delta': summary['efficiencies']['delta']
        }

    def summarize_ledger(self):
        """ generates summary metrics for the ledger """
        total_cycles = 0
        active_cycles = 0
        efficiencies = []
        production = {}
        consumption = {}
        net_production = {}
        purchases = {}
        total_production_value = Price()
        total_production_cost = Price()
        total_purchases = Price()
        missing_inputs = []
        missing_supplies = []

        for entry in self.entries:
            if entry['type'] == Ledger.STATUS:
                total_cycles = total_cycles + 1
                active_cycles = active_cycles + entry['state']

            elif entry['type'] == Ledger.EFFICIENCY:
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

            elif entry['type'] == Ledger.PURCHASE_INPUT:
                product = entry['product']
                count = entry['count']
                price = self.market.price(product)
                value = price.multiply(count)
                total_purchases = total_purchases.add(value)

                fmt = '{0[clock]} {0[line]}.{0[bnum]} purchased {0[count]:4.2f} {0[product]} ' +\
                      '(need {0[need]:4.2f} have {0[available]:4.2f})'
                missing_inputs.append(fmt.format(entry))

                if product in purchases:
                    purchases[product]['count'] = purchases[product]['count'] + count
                    purchases[product]['value'] = purchases[product]['value'].add(value)
                else:
                    purchases[product] = {}
                    purchases[product]['count'] = count
                    purchases[product]['value'] = value

            elif entry['type'] == Ledger.PURCHASE_SUPPLY:
                product = entry['product']
                count = entry['count']
                price = self.market.price(product)
                value = price.multiply(count)
                total_purchases = total_purchases.add(value)

                fmt = '{0[clock]} {0[line]} purchased {0[count]:4.2f} {0[product]} ' +\
                      '(need {0[need]:4.2f} have {0[available]:4.2f})'
                missing_supplies.append(fmt.format(entry))

                if product in purchases:
                    purchases[product]['count'] = purchases[product]['count'] + count
                    purchases[product]['value'] = purchases[product]['value'].add(value)
                else:
                    purchases[product] = {}
                    purchases[product]['count'] = count
                    purchases[product]['value'] = value

            elif entry['type'] == Ledger.MISSING_INPUT:
                fmt = '{0[clock]} {0[line]}.{0[bnum]} missing {0[count]:4.2f} {0[ticker]} ' +\
                      '(need {0[need]:4.2f} have {0[available]:4.2f})'
                missing_inputs.append(fmt.format(entry))

            elif entry['type'] == Ledger.MISSING_SUPPLY:
                fmt = '{0[clock]} {0[line]} missing {0[count]:4.2f} {0[ticker]} ' +\
                      '(need {0[need]:4.2f} have {0[available]:4.2f})'
                missing_supplies.append(fmt.format(entry))

        total_gain_loss = total_production_value.add(total_production_cost)
        return {
            'total_cycles': total_cycles,
            'active_cycles': active_cycles,
            'uptime_percent': float(active_cycles)/float(total_cycles),
            'efficiencies': self._summarize_efficiencies(efficiencies),
            'production': production,
            'consumption': consumption,
            'net_production': net_production,
            'purchases': purchases,
            'total_production_value': total_production_value,
            'total_production_cost': total_production_cost,
            'total_gain_loss': total_gain_loss,
            'total_purchases': total_purchases,
            'missing_inputs': missing_inputs,
            'missing_supplies': missing_supplies
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
