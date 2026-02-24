"""SVG renderer for floorplan visualization."""

import os
import sys

# Ensure cairo shared library is discoverable on macOS with Homebrew.
# cairocffi (used by cairosvg) calls cffi's ffi.dlopen("libcairo.2.dylib")
# which only searches standard paths.  Homebrew on Apple Silicon installs
# to /opt/homebrew/lib which is not in the default search path.
# We patch cffi.FFI.dlopen to also try Homebrew paths as a fallback.
if sys.platform == "darwin":
    _BREW_LIB_DIRS = [
        d for d in ("/opt/homebrew/lib", "/usr/local/lib")
        if os.path.isdir(d)
    ]
    if _BREW_LIB_DIRS:
        try:
            import cffi

            _original_dlopen = cffi.FFI.dlopen

            def _dlopen_with_homebrew(self, name, flags=0):  # type: ignore[no-untyped-def]
                try:
                    return _original_dlopen(self, name, flags)
                except OSError:
                    if isinstance(name, str):
                        for lib_dir in _BREW_LIB_DIRS:
                            try:
                                return _original_dlopen(
                                    self, os.path.join(lib_dir, name), flags,
                                )
                            except OSError:
                                continue
                    raise

            cffi.FFI.dlopen = _dlopen_with_homebrew
        except ImportError:
            pass
