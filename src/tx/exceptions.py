class TxMesCliError(Exception):
    """Base class for exceptions in this module."""

    pass


class CannotLoginError(TxMesCliError):
    """Exception raised for errors in the login process.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
