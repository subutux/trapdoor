class ErrorTrapTransport(Exception):
    pass

class ConfigNotFoundError(Exception):
    pass

class ConfigNotParsedError(Exception):
    pass
class MibCompileError(Exception):
    pass
class MibCompileFailed(Exception):
    pass
class FilterPathError(Exception):
    pass
class FilterProcessError(Exception):
    pass
class FilterParseError(Exception):
    pass
class FilterSaveError(Exception):
    pass