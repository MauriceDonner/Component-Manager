class AutosetupMenuError(Exception):
    """Base class for component menu exceptions"""
    pass

class DoubleConfiguration(AutosetupMenuError):
    """Raise when there are both WMC and SemDex Components found"""
    pass

class MultipleUnconfiguredLoadports(AutosetupMenuError):
    """Raise, when there are multiple unconfigured loadports found"""
    pass

class NoBackup(AutosetupMenuError):
    """Raise, when the backup file could not be created"""
    pass

class NoSystem(AutosetupMenuError):
    """Raise when there is no system information found""" 
    pass

class TestException(AutosetupMenuError):
    """Test whether exceptions are handled correctly"""
    pass

class Unhandled(Exception):
    """Raise when no Exception has been defined yet"""
    pass
