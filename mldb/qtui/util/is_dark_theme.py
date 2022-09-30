import sys
import subprocess


def is_dark_theme_macos() -> bool:
    """Checks DARK/LIGHT mode of MacOS."""
    cmd = 'defaults read -g AppleInterfaceStyle'
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)

    # Will be either the string b'Dark' or empty
    dark_or_nah = p.communicate()[0]

    return bool(dark_or_nah)


def is_dark_theme() -> bool:
    if sys.platform == 'darwin':
        return is_dark_theme_macos()
    else:
        raise NotImplementedError(f'Unsupported platform {sys.platform}')
