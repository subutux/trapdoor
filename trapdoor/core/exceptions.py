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