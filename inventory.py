""" class for maintaining an inventory """

import sys
import json

class Inventory(object):
    """ Inventory Class 
    Container for managing the current inventory
    """

    def __init__(self, inventory):
        self.items = inventory

    def __str__(self):
        return json.dumps(self.items)

    def count(self, item):
        if item in self.items:
            return self.items[item]
        return 0

    def has(self, item, count):
        if item in self.items and self.items[item] >= count:
            return True
        return False

    def add(self, item, count):
        if item not in self.items:
            self.items[item] = count
        else:
            self.items[item] = self.items[item] + count
        return True

    def remove(self, item, count):
        if item in self.items and self.items[item] >= count:
            self.items[item] = self.items[item] - count
            return True
        return False


            
        