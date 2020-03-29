#!/usr/bin/python3
""" test driver for price functions
"""

import sys
from market import Price

pricedata1 = [1.0, 2.0, 3.0, 4.0]
pricedata2 = [1.0, 2.0, 4.0, 8.0]

price1 = Price(pricedata1)
price2 = Price(pricedata2)

print(price1)
print(price2)

print(price1.multiply(3.0))
print(price2.multiply(5.0))

print(price1.add(price2))