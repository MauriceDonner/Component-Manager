class AutosetupMenuError(Exception):
    """Base class for Autosetup Menu exceptions"""
    pass

class ComponentMenuError(Exception):
    """Base class for Component Menu exceptions"""
    pass

class ComponentError(Exception):
    """Base class for Component exceptions"""

class OutOfRange(Exception):
    """Raise, when user input is out of range"""
    pass

class UserRejection(Exception):
    """Raise, when user rejects an input"""

class DoubleConfiguration(AutosetupMenuError):
    """Raise when there are both WMC and SemDex Components found"""
    pass

class MultipleUnconfiguredLoadports(AutosetupMenuError):
    """Raise, when there are multiple unconfigured loadports found"""
    pass

class NoBackup(AutosetupMenuError):
    """Raise, when the backup file could not be created"""
    pass

class NoConnection(AutosetupMenuError):
    """Raise, when no component is connected"""
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

class UnknownComponent(AutosetupMenuError):
    """Raise when the component has not been added yet"""
    pass

class TeachingDataOutOfRange(ComponentMenuError):
    """Raise when the teaching data doesn't fit into the expected range"""
    pass

class LargeTeachingChange(ComponentError):
    """Raise when a teaching value is changed more than 2mm"""
    pass