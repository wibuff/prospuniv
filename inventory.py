""" class for maintaining an inventory """

import sys
import json
from reportgen import Report

class Inventory(object):
    """ Inventory Class 
    Container for managing the current inventory
    """

    def __init__(self, inventory):
        self.items = {}
        for key in inventory.keys():
            self.items[key] = inventory[key]

    def __str__(self):
        return json.dumps(self.items)

    def count(self, item):
        if item in self.items:
            return self.items[item]
        return 0.0

    def has(self, item, count):
        if item in self.items and self.items[item] >= count:
            return True
        return False

    def add(self, item, count):
        if item not in self.items:
            self.items[item] = float(count)
        else:
            self.items[item] = self.items[item] + float(count)
        return True

    def remove(self, item, count):
        if item in self.items and self.items[item] >= count:
            self.items[item] = self.items[item] - count
            return True
        return False

    def diff(self, other):
        net = {}
        for key in self.items.keys(): 
            start_val = other.count(key)
            net[key] = self.items[key] - start_val
        return Inventory(net)

    def add_all(self, materials):
        for key in materials.keys():
            self.add(key, materials[key])

    def output_summary(self, label, market):
        summary = self.summarize_inventory(market)

        report = Report()
        report.start()
        report.output_value_table(summary['inventory'], label) 
        report.end()

    def summarize_inventory(self, market):
        inventory = {}
        for product in self.items.keys(): 
            count = self.items[product]
            price = market.price(product)
            value = price.multiply(count)

            if product in inventory:
                inventory[product]['count'] = inventory[product]['count'] + count
                inventory[product]['value'] = inventory[product]['value'].add(value)
            else:
                inventory[product] = {}
                inventory[product]['count'] = count
                inventory[product]['value'] = value

        return {
            'inventory': inventory
        }
            
        