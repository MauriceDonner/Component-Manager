class AutosetupMenuError(Exception):
    """Base class for component menu exceptions"""
    pass

class DoubleConfiguration(AutosetupMenuError):
    """Raise when there are both WMC and SemDex Components found"""
    pass

class TestException(AutosetupMenuError):
    """Test whether exceptions are handled correctly"""
    pass