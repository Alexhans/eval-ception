# SPDX-FileCopyrightText: 2026-present Alex Hans <alexhans.dev@gmail.com>
#
# SPDX-License-Identifier: MIT

# Keep package import lightweight so adapter CLIs can run without optional heavy deps.


def ask(*args, **kwargs):
    from .baseline import ask as _ask

    return _ask(*args, **kwargs)


def setup_logging(*args, **kwargs):
    from .baseline import setup_logging as _setup_logging

    return _setup_logging(*args, **kwargs)


__all__ = ["ask", "setup_logging"]
