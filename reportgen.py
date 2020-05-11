""" report generation class
"""

from market import Price

class Report(object):
    """ Report class
    """
    ## Table formating strings ##
    TABLE_WIDTH = 87
    VT_HEADFMT = '{:<5} {:>12} {:>12s} {:>12s} {:>12s} {:>12s}'
    VT_HEAD = VT_HEADFMT.format('Item', 'Count', 'Last', 'Ask', 'Bid', 'Avg')
    VT_BODYFMT = '  {product:<3} {count:>12.2f} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f}'
    VT_TOTFMT = '{product:<5} {count:>12.2f} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f}'

    VT_HEADFMT_WDUR = '{:<5} {:>12} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s}'
    VT_HEAD_WDUR = VT_HEADFMT_WDUR.format('Item', 'Count', 'Last', 'Ask', 'Bid', 'Avg', 'PerDay')
    VT_BODYFMT_WDUR = '  {product:<3} {count:>12.2f} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f} {perday:>12.2f}'
    VT_TOTFMT_WDUR = '{product:<5} {count:>12.2f} {price.last:>12.2f} {price.ask:>12.2f} {price.bid:>12.2f} {price.avg:>12.2f} {perday:>12.2f}'

    #GENERAL = '\u2551 {{:<{}s}} \u2551'.format(str(len(VT_HEAD_WDUR)))
    GENERAL = '\u2551 {{:<{}s}} \u2551'.format(str(TABLE_WIDTH-4))
    
    HEADBREAK = u'\u2554' + u'\u2550' * (TABLE_WIDTH-2) + u'\u2557'
    MAJBREAK = u'\u2560' + u'\u2550' * (TABLE_WIDTH-2) + u'\u2563'
    MINBREAK = u'\u255F' + u'\u2500' * (TABLE_WIDTH-2)  + u'\u2562'
    FOOTBREAK = u'\u255A' + u'\u2550' * (TABLE_WIDTH-2) + u'\u255D'

    def start(self):
        print(self.HEADBREAK)

    def output_general(self, output):
        print(self.GENERAL.format(output))

    def major_break(self): 
        print(self.MAJBREAK)

    def minor_break(self): 
        print(self.MINBREAK)

    def output_value_table(self, inventory, name=None):
        total_count = 0
        total_prices = Price()

        if name:
            header = "{}:".format(name)
            self.output_general(header)

        self.minor_break()
        self.output_general(self.VT_HEAD)
        for key in inventory.keys():
            total_count = total_count + inventory[key]['count']
            total_prices = total_prices.add(inventory[key]['value'])
            product_line = self.VT_BODYFMT.format(
                product=key,
                count=inventory[key]['count'],
                price=inventory[key]['value'])
            self.output_general(product_line)
        self.minor_break()
        total_line = self.VT_TOTFMT.format(product='TOTAL', count=total_count, price=total_prices)
        self.output_general(total_line)

    def output_value_table_w_perday(self, inventory, name, duration):
        total_count = 0
        total_prices = Price()
        total_perday = 0.0
        days = duration.to_days()

        if name:
            header = "{}:".format(name)
            self.output_general(header)

        self.minor_break()
        self.output_general(self.VT_HEAD_WDUR)
        for key in inventory.keys():
            count = inventory[key]['count']
            total_count = total_count + count
            total_prices = total_prices.add(inventory[key]['value'])
            perday = float(count)/float(days)
            total_perday = total_perday + perday
            product_line = self.VT_BODYFMT_WDUR.format(
                product=key,
                count=inventory[key]['count'],
                price=inventory[key]['value'],
                perday=perday)
            self.output_general(product_line)
        self.minor_break()
        total_line = self.VT_TOTFMT_WDUR.format(product='TOTAL', count=total_count, price=total_prices,perday=total_perday)
        self.output_general(total_line)

    def end(self):
        print(self.FOOTBREAK)
