"""Custom exceptions."""

from subprocess import CalledProcessError


class CalledProcessCustomError(CalledProcessError):
    """A customization of CalledProcessError."""

    def __init__(self, called_process_error: CalledProcessError) -> None:
        super().__init__(
            returncode=called_process_error.returncode,
            cmd=called_process_error.cmd,
            output=called_process_error.output,
            stderr=called_process_error.stderr,
        )

    def __str__(self) -> str:
        return (
            f"\ncommand: {' '.join(self.cmd)}\n"
            f"   code: {self.returncode}\n"
            f"  error: {self.stderr.decode("utf-8")}"
        )
