class AutosetupMenuError(Exception):
    """Base class for component menu exceptions"""
    pass

class MultipleUnconfiguredLoadports(AutosetupMenuError):
    """Raise, when there are multiple unconfigured loadports found"""
    pass

class DoubleConfiguration(AutosetupMenuError):
    """Raise when there are both WMC and SemDex Components found"""
    pass

class NoSystem(AutosetupMenuError):
    """Raise when there is no system information found""" 
    pass

class TestException(AutosetupMenuError):
    """Test whether exceptions are handled correctly"""
    pass