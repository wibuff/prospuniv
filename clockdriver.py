#!/usr/bin/python3
""" test driver for clock functions
"""

import sys
from clock import Duration, IncrClock, DecrClock

print('{} = {}'.format('30', Duration('30')))
print('{} = {}'.format('60', Duration('60')))
print('{} = {}'.format('30:30', Duration('30:30')))
print('{} = {}'.format('60:30', Duration('60:30')))
print('{} = {}'.format('60:60', Duration('60:60')))
print('{} = {}'.format('30:30:30', Duration('30:30:30')))
print('{} = {}'.format('24:30:30', Duration('24:30:30')))
print('{} = {}'.format('24:60:60', Duration('24:60:60')))
print('{} = {}'.format('1:0:0:0', Duration('1:0:0:0')))
print('{} = {}'.format('10:24:60:60', Duration('10:24:60:60')))
print('{} = {}'.format('3600', Duration('3600')))
print('{} = {}'.format('86400', Duration('86400')))

iclock = IncrClock(Duration('1:0:0:0'))
print('')
print('IncrClock {}'.format(iclock))
while iclock.step():
    print('          {}'.format(iclock))
print('          {}'.format(iclock))

dclock = DecrClock(Duration('1:0:0:0'))
print('')
print('DecrClock {}'.format(dclock))
while dclock.step():
    print('          {}'.format(dclock))
print('          {}'.format(dclock))