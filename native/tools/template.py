"""Resolve and verify the exact SAGE parent before using any ROM data."""
from pathlib import Path
import hashlib
import os

PARENT_SHA256 = '952955f9a171636862f88bf6f64aa00a049abe5b8aaab7a8e63275bacdf445cd'
DEFAULT_TEMPLATE = Path('/home/anon/sonic-hacks-archive/sonic-1-at-sage-2010/Sonic the Hedgehog 1 @ SAGE 2010 (S1 Hack).bin')


class TemplateError(ValueError):
    """The selected parent is missing, unreadable, or not the required ROM."""


def load_template(path=None, recorded_path=None):
    """CLI overrides environment, then manifest, then the local default.

    Relative paths are resolved against the caller's working directory. Callers
    must pass the returned absolute path to subprocesses that change directory.
    """
    selected = path if path is not None else (
        os.environ.get('SONIC_LAB_TEMPLATE') or recorded_path or DEFAULT_TEMPLATE)
    selected = Path(selected).expanduser().resolve()
    try:
        data = selected.read_bytes()
    except OSError as error:
        raise TemplateError(
            f'Cannot read SAGE template {selected}: {error.strerror}. '
            'Supply --template PATH or set SONIC_LAB_TEMPLATE.') from error
    digest = hashlib.sha256(data).hexdigest()
    if digest != PARENT_SHA256:
        raise TemplateError(
            f'Wrong SAGE template {selected}: SHA-256 {digest}; '
            f'expected {PARENT_SHA256}. Refusing to use this ROM.')
    return selected, data
