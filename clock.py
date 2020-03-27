""" Clock Utilities
"""

import sys

DAYS = 0
HOURS = 1
MINUTES = 2
SECONDS = 3

class Duration(object):
    """ Duration Class
    Note: Truncates seconds after normalizing hours and minutes
    """
    def __init__(self, duration_str):
        self.vals = list(map(int, duration_str.split(":")))
        if len(self.vals) > 4: 
            raise Exception('error: invalid duration {}'.format(duration_str))
        self._normalize()

    def __str__(self):
        return '{:02d} {:02d}:{:02d}:{:02d}'.format(self.vals[DAYS], self.vals[HOURS], self.vals[MINUTES], self.vals[SECONDS])

    def __repl__(self):
        return '{:02d} {:02d}:{:02d}:{:02d}'.format(self.vals[DAYS], self.vals[HOURS], self.vals[MINUTES], self.vals[SECONDS])

    def _normalize(self):
        while len(self.vals) < 4:
            self.vals.insert(0,0)
        if self.vals[SECONDS] >= 60:
            mins = self.vals[SECONDS] // 60
            secs = self.vals[SECONDS] % 60
            self.vals[MINUTES] = self.vals[MINUTES] + mins
            self.vals[SECONDS] = secs
        if self.vals[MINUTES] >= 60:
            hrs = self.vals[MINUTES] // 60
            mins = self.vals[MINUTES] % 60
            self.vals[HOURS] = self.vals[HOURS] + hrs
            self.vals[MINUTES] = mins
        if self.vals[HOURS] >= 24:
            days = self.vals[HOURS] // 24
            hrs = self.vals[HOURS] % 24
            self.vals[DAYS] = self.vals[DAYS] + days
            self.vals[HOURS] = hrs
        self.vals[SECONDS] = 0

    def to_minutes(self):
        return self.vals[DAYS] * 24 * 60 + self.vals[HOURS] * 60 + self.vals[MINUTES]

    def apply_efficiency(self, efficiency):
        mins = float(self.to_minutes()) / efficiency
        self.vals[HOURS] = int(mins) // 60
        self.vals[MINUTES] = int(mins) % 60
        self._normalize()

class IncrClock(object):
    """ An Incrementing Clock 
    Increments from 00:00:00 to the provided Duration
    """

    def __init__(self, duration):
        self.vals=[0,0,0,0]
        self.duration = duration

    def __str__(self):
        return '{:02d} {:02d}:{:02d}:{:02d}'.format(self.vals[DAYS], self.vals[HOURS], self.vals[MINUTES], self.vals[SECONDS])

    def __repl__(self):
        return '{:02d} {:02d}:{:02d}:{:02d}'.format(self.vals[DAYS], self.vals[HOURS], self.vals[MINUTES], self.vals[SECONDS])

    def to_minutes(self):
        return self.vals[DAYS] * 24 * 60 + self.vals[HOURS] * 60 + self.vals[MINUTES]

    def step(self):
        if self.vals[HOURS] >= 23 and self.vals[MINUTES] == 59:
            self.vals[MINUTES] = 0
            self.vals[HOURS] = 0
            self.vals[DAYS] = self.vals[DAYS] + 1
        elif self.vals[MINUTES] == 59:
            self.vals[MINUTES] = 0
            self.vals[HOURS] = self.vals[HOURS] + 1
        else:
            self.vals[MINUTES] = self.vals[MINUTES] + 1
        return self.to_minutes() < self.duration.to_minutes()

class DecrClock(object):
    """ A Decrementing Clock 
    Decrements from provided Duration to 00:00:00
    """

    def __init__(self, duration):
        self.vals=duration.vals
        self.duration = duration

    def __str__(self):
        return '{:02d} {:02d}:{:02d}:{:02d}'.format(self.vals[DAYS], self.vals[HOURS], self.vals[MINUTES], self.vals[SECONDS])

    def __repl__(self):
        return '{:02d} {:02d}:{:02d}:{:02d}'.format(self.vals[DAYS], self.vals[HOURS], self.vals[MINUTES], self.vals[SECONDS])

    def to_minutes(self):
        return self.vals[DAYS] * 24 * 60 + self.vals[HOURS] * 60 + self.vals[MINUTES]

    def step(self):
        if self.vals[HOURS] > 0 and self.vals[MINUTES] == 0:
            self.vals[MINUTES] = 59
            self.vals[HOURS] = self.vals[HOURS] - 1
        elif self.vals[DAYS] > 0 and self.vals[MINUTES] == 0:
            self.vals[MINUTES] = 59
            self.vals[HOURS] = 23
            self.vals[DAYS] = self.vals[DAYS] - 1
        elif self.vals[MINUTES] > 0:
            self.vals[MINUTES] = self.vals[MINUTES] - 1
        return self.to_minutes() > 0

