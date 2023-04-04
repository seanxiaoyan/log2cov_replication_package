from json import JSONEncoder

class logRe():
    def __init__(self, module=None,lineno=None,begin_cycle=False,end_cycle=False,begin_loop=False,\
        end_loop=False,coverage=set(), may_coverage = set(), must_not_coverage = set() ,**entries):

        self.module = module 
        self.lineno = lineno
        self.begin_cycle = begin_cycle
        self.end_cycle = end_cycle
        self.begin_loop = begin_loop
        self.end_loop = end_loop
        self.coverage = coverage
        self.may_coverage = may_coverage
        self.must_not_coverage = must_not_coverage
        # converting dict to obejct 
        self.__dict__.update(entries)

    def __eq__(self, other):
        return (self.module, self.lineno, self.begin_cycle, self.end_cycle, self.begin_loop, self.end_loop) \
            == (other.module, other.lineno, other.begin_cycle, other.end_cycle, other.begin_loop, other.end_loop)

    def __hash__(self):
        return hash((self.module, self.lineno, self.begin_cycle, self.end_cycle, self.begin_loop, self.end_loop))

    def __str__(self):
        return f"{self.module}{self.lineno}{self.begin_cycle}{self.end_cycle}{self.begin_loop}{self.end_loop}"

    def copy(self):

        new_logRE = logRe()
        new_logRE.module = self.module
        new_logRE.lineno = self.lineno
        new_logRE.begin_cycle = self.begin_cycle
        new_logRE.end_cycle = self.end_cycle
        new_logRE.begin_loop = self.begin_loop
        new_logRE.end_loop = self.end_loop
        new_logRE.coverage = self.coverage.copy()
        new_logRE.may_coverage = self.may_coverage.copy()
        new_logRE.must_not_coverage = self.must_not_coverage.copy()

        return new_logRE
# subclass JSONEncoder
class LogEncoder(JSONEncoder):
    def default(self, o):
        try:
            return o.__dict__
        except AttributeError:
            return list(o)