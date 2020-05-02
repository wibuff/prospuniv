""" report generation class
"""

import sys
import json
from market import Price

class Report(object):
    """ Report class
    """
    ## Table formating strings ## 
    TABLE_WIDTH = 74
    VTABLEHEADFMT = '{:<5} {:>12} {:>12s} {:>12s} {:>12s} {:>12s}'
    VTABLEHEAD = VTABLEHEADFMT.format('Item', 'Count', 'Last', 'Ask', 'Bid', 'Avg')
    VTABLEBODFMT = '  {product:<3} {count:>12.2f} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f}'
    VTABLETOTFMT = '{product:<5} {count:>12.2f} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f}'

    GENERAL = '\u2551 {{:<{}s}} \u2551'.format(str(len(VTABLEHEAD)))
    
    HEADBREAK = u'\u2554' + u'\u2550' * (TABLE_WIDTH-2) + u'\u2557'
    MAJBREAK = u'\u2560' + u'\u2550' * (TABLE_WIDTH-2) + u'\u2563'
    MINBREAK = u'\u255F' + u'\u2500' * (TABLE_WIDTH-2)  + u'\u2562'
    FOOTBREAK = u'\u255A' + u'\u2550' * (TABLE_WIDTH-2) + u'\u255D'


    def start(self):
        print(self.HEADBREAK)

    def output_general(self, output):
        print(self.GENERAL.format(output));

    def major_break(self): 
        print(self.MAJBREAK)

    def minor_break(self): 
        print(self.MINBREAK)

    def output_value_table(self, inventory, name):
        total_count = 0
        total_prices = Price()

        if name:
            header = "{}:".format(name)
            self.output_general(header)

        # self.major_break()
        self.minor_break()
        self.output_general(self.VTABLEHEAD)

        for key in inventory.keys():
            total_count = total_count + inventory[key]['count']
            total_prices = total_prices.add(inventory[key]['value'])
            product_line = self.VTABLEBODFMT.format(
                product=key, 
                count = inventory[key]['count'], 
                price = inventory[key]['value'])
            self.output_general(product_line)

        self.minor_break()
        total_line = self.VTABLETOTFMT.format(product='TOTAL', count = total_count, price = total_prices)
        self.output_general(total_line)

    def end(self):
        print(self.FOOTBREAK)
