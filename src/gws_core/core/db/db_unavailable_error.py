class DbUnavailableError(Exception):
    """Raised when a database is genuinely unavailable (not yet provisioned or
    unreachable), as opposed to a programming/configuration error.

    For lazy db managers this is an expected, recoverable condition at boot
    time: the lab manager may be down or the container not started yet, so the
    db is simply unavailable and initialization is skipped (it can connect
    later). DbManagerService recognizes this type to log a clear "database
    unavailable" message and continue booting instead of treating it as a bug.
    """
