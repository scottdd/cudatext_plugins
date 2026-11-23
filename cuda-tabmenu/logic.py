"""Pure helpers for Tab Menu. No CudaText imports, so unit tests run outside the editor."""

import math
import os
import re
import tempfile
import time
from urllib.parse import quote


__version__ = '0.7.0'


class FileOpError(Exception):
    """A refused or failed file copy, write, or delete."""


def format_size(size_bytes):
    size_bytes = int(size_bytes)
    if size_bytes < 0:
        raise ValueError('size must be >= 0')
    if size_bytes == 0:
        return '0 B'
    units = ('B', 'kB', 'MB', 'GB', 'TB')
    i = min(int(math.floor(math.log(size_bytes, 1024))), len(units) - 1)
    value = round(size_bytes / math.pow(1024, i), 2)
    return '%s %s' % (value, units[i])


def count_words(text):
    if not text:
        return 0
    return len(re.findall(r'\S+', text))


def count_characters(text):
    """Unicode characters in the editor buffer, including one per line break."""
    if not text:
        return 0
    return len(text)


def format_status(on_disk, modified, read_only):
    if not on_disk:
        parts = ['unsaved']
    elif modified:
        parts = ['modified']
    else:
        parts = ['saved']
    if read_only:
        parts.append('read-only')
    return ', '.join(parts)


def format_line_endings(value):
    mapping = {
        'lf': 'LF (Unix)',
        'crlf': 'CRLF (Windows)',
        'cr': 'CR (classic Mac)',
    }
    if not value:
        return '(none)'
    return mapping.get(value, value)


def format_timestamp(mtime):
    if mtime is None:
        return '(none)'
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))


def format_labeled_rows(rows):
    """rows is a list of (label, value). None values are omitted."""
    visible = []
    for label, value in rows:
        if value is None:
            continue
        visible.append((str(label), str(value)))
    if not visible:
        return ''
    width = max(len(label) for label, _value in visible)
    return '\n'.join('%s: %s' % (label.ljust(width), value) for label, value in visible)


_FILE_INFO_FIELDS = (
    ('path', 'Full path'),
    ('filename', 'Filename'),
    ('status', 'Status'),
    ('encoding', 'Encoding'),
    ('line_endings', 'Line endings'),
    ('lexer', 'Lexer'),
    ('size_disk', 'Size on disk'),
    ('size_memory', 'Size in memory (UTF-8)'),
    ('lines', 'Lines'),
    ('words', 'Words'),
    ('characters', 'Characters'),
    ('modified', 'Last modified'),
)


def format_file_info(info):
    """Format a file-info dict. Missing keys and None values are omitted."""
    rows = []
    for key, label in _FILE_INFO_FIELDS:
        if key not in info:
            continue
        rows.append((label, info[key]))
    return format_labeled_rows(rows)


def suggest_duplicate_name(filename, exists):
    """Return a basename stem_copy.ext, then stem_copy2.ext, that exists() rejects.

    exists is called with candidate basenames, not full paths.
    """
    stem, ext = os.path.splitext(filename)
    candidate = '%s_copy%s' % (stem, ext)
    if not exists(candidate):
        return candidate
    number = 2
    while number <= 10000:
        candidate = '%s_copy%d%s' % (stem, number, ext)
        if not exists(candidate):
            return candidate
        number += 1
    raise FileOpError('could not find a free duplicate name')


def clean_duplicate_basename(name):
    """A single file name in the same folder. Rejects paths."""
    cleaned = (name or '').strip()
    if not cleaned or cleaned in ('.', '..'):
        raise FileOpError('Enter a file name')
    if '/' in cleaned or '\\' in cleaned or os.path.basename(cleaned) != cleaned:
        raise FileOpError('Enter a file name in the same folder, not a path')
    return cleaned


def prepare_destination(path, overwrite=False):
    """Absolute file path that is safe to write. Raises FileOpError otherwise."""
    if path is None or not str(path).strip():
        raise FileOpError('empty path')
    dest = os.path.abspath(os.path.expanduser(str(path)))
    if os.path.isdir(dest):
        raise FileOpError('destination is a directory')
    parent = os.path.dirname(dest)
    if not parent or not os.path.isdir(parent):
        raise FileOpError('destination folder does not exist')
    if os.path.exists(dest):
        if os.path.islink(dest):
            if os.path.isdir(dest):
                raise FileOpError('destination is a directory')
        elif not os.path.isfile(dest):
            raise FileOpError('destination is not a file')
        if not overwrite:
            raise FileOpError('destination already exists')
    return dest


def safe_write_bytes(path, data, overwrite=False):
    """Write bytes via a temp file in the destination folder, then replace.

    The destination folder must already exist. Directories are never replaced.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise FileOpError('data must be bytes')
    dest = prepare_destination(path, overwrite=overwrite)
    parent = os.path.dirname(dest)
    fd, tmp = tempfile.mkstemp(prefix='.tabmenu-copy-', dir=parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(bytes(data))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, dest)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return dest


def safe_copy_file(src, dest, overwrite=False):
    """Byte-copy a regular file. Does not copy a path onto itself."""
    if not src or not str(src).strip():
        raise FileOpError('empty source path')
    source = os.path.abspath(os.path.expanduser(str(src)))
    if not os.path.isfile(source):
        raise FileOpError('source is not a file')
    target = os.path.abspath(os.path.expanduser(str(dest)))
    if os.path.normcase(source) == os.path.normcase(target):
        raise FileOpError('source and destination are the same file')
    with open(source, 'rb') as handle:
        data = handle.read()
    return safe_write_bytes(target, data, overwrite=overwrite)


def safe_delete_file(path):
    """Delete one regular file or a symlink to a file. Never deletes a directory."""
    if path is None or not str(path).strip():
        raise FileOpError('empty path')
    target = os.path.abspath(os.path.expanduser(str(path)))
    if not os.path.lexists(target):
        raise FileOpError('file does not exist')
    if os.path.isdir(target):
        raise FileOpError('refusing to delete a directory')
    if os.path.islink(target):
        os.remove(target)
        return target
    if not os.path.isfile(target):
        raise FileOpError('not a regular file')
    os.remove(target)
    return target


def first_path(value):
    """dlg_file may return a string, a list, or None."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else ''
    return value or ''


_CODEC_ALIASES = {
    'utf8': ('utf-8', None),
    'utf-8': ('utf-8', None),
    'utf8_bom': ('utf-8', b'\xef\xbb\xbf'),
    'utf-8_bom': ('utf-8', b'\xef\xbb\xbf'),
    'utf16le': ('utf-16-le', None),
    'utf-16le': ('utf-16-le', None),
    'utf16le_bom': ('utf-16-le', b'\xff\xfe'),
    'utf-16le_bom': ('utf-16-le', b'\xff\xfe'),
    'utf16be': ('utf-16-be', None),
    'utf-16be': ('utf-16-be', None),
    'utf16be_bom': ('utf-16-be', b'\xfe\xff'),
    'utf-16be_bom': ('utf-16-be', b'\xfe\xff'),
    'utf32le': ('utf-32-le', None),
    'utf-32le': ('utf-32-le', None),
    'utf32le_bom': ('utf-32-le', b'\xff\xfe\x00\x00'),
    'utf-32le_bom': ('utf-32-le', b'\xff\xfe\x00\x00'),
    'utf32be': ('utf-32-be', None),
    'utf-32be': ('utf-32-be', None),
    'utf32be_bom': ('utf-32-be', b'\x00\x00\xfe\xff'),
    'utf-32be_bom': ('utf-32-be', b'\x00\x00\xfe\xff'),
    'iso88591': ('iso-8859-1', None),
    'iso8859-1': ('iso-8859-1', None),
    'iso88592': ('iso-8859-2', None),
    'iso885915': ('iso-8859-15', None),
    'mac': ('mac_roman', None),
}


def resolve_encoding(encoding):
    """Return (python_codec, bom_bytes_or_None) for a CudaText encoding short name."""
    name = (encoding or '').strip()
    if not name:
        return 'utf-8', None
    key = name.lower().replace(' ', '')
    if key in _CODEC_ALIASES:
        return _CODEC_ALIASES[key]
    try:
        import codecs
        codecs.lookup(name)
    except LookupError:
        raise FileOpError('unsupported encoding: %s' % encoding)
    return name, None


def encode_document(text, encoding, newline='keep'):
    """Encode editor text. newline is 'keep', 'lf', 'crlf', or 'cr'.

    'keep' writes the newlines already in text. The other modes first normalize
    any mix of CR/LF to the requested ending. A BOM is prepended for *_bom
    encodings when the encoded bytes do not already start with one.
    """
    if text is None:
        text = ''
    if newline == 'crlf':
        text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    elif newline == 'lf':
        text = text.replace('\r\n', '\n').replace('\r', '\n')
    elif newline == 'cr':
        text = text.replace('\r\n', '\n').replace('\n', '\r')
    elif newline != 'keep':
        raise FileOpError('unknown newline %r' % (newline,))
    codec, bom = resolve_encoding(encoding)
    try:
        data = text.encode(codec)
    except LookupError:
        raise FileOpError('unsupported encoding: %s' % encoding)
    except UnicodeEncodeError as exc:
        raise FileOpError('encoding %s cannot represent this text (%s)' % (encoding, exc.reason))
    if bom and not data.startswith(bom):
        data = bom + data
    return data


def platform_from_suffix(suffix):
    """Map CudaText PROC_GET_OS_SUFFIX to windows, macos, haiku, or linux.

    An empty suffix is Windows. Anything else (including a Linux suffix) is linux.
    """
    if suffix is None:
        suffix = ''
    suffix = str(suffix)
    if suffix == '':
        return 'windows'
    if suffix == '__mac':
        return 'macos'
    if suffix == '__haiku':
        return 'haiku'
    return 'linux'


def path_to_file_uri(path):
    absolute = os.path.abspath(path)
    return 'file://' + quote(absolute, safe='/')


def _attempt(argv, check=None, cwd=None, wait=False):
    item = {'argv': list(argv), 'wait': wait}
    if check:
        item['check'] = check
    if cwd:
        item['cwd'] = cwd
    return item


def reveal_attempts(platform, path):
    """Commands that select path in the OS file manager, in the order to try.

    Linux tries the FileManager1 D-Bus method first, then xdg-open on the folder.
    """
    path = os.path.abspath(path)
    folder = os.path.dirname(path) or path
    if platform == 'windows':
        return [_attempt(['explorer', '/select,' + path])]
    if platform == 'macos':
        return [_attempt(['open', '-R', path])]
    if platform == 'linux':
        uri = path_to_file_uri(path)
        return [
            _attempt(
                [
                    'dbus-send',
                    '--session',
                    '--type=method_call',
                    '--print-reply',
                    '--dest=org.freedesktop.FileManager1',
                    '/org/freedesktop/FileManager1',
                    'org.freedesktop.FileManager1.ShowItems',
                    'array:string:"%s"' % uri,
                    'string:""',
                ],
                check='dbus-send',
                wait=True,
            ),
            _attempt(
                [
                    'gdbus',
                    'call',
                    '--session',
                    '--dest',
                    'org.freedesktop.FileManager1',
                    '--object-path',
                    '/org/freedesktop/FileManager1',
                    '--method',
                    'org.freedesktop.FileManager1.ShowItems',
                    "['%s']" % uri,
                    "''",
                ],
                check='gdbus',
                wait=True,
            ),
            _attempt(['xdg-open', folder], check='xdg-open'),
        ]
    return []


def open_folder_attempts(platform, folder):
    folder = os.path.abspath(folder)
    if platform == 'windows':
        return [_attempt(['explorer', folder])]
    if platform == 'macos':
        return [_attempt(['open', folder])]
    if platform == 'linux':
        return [_attempt(['xdg-open', folder], check='xdg-open')]
    if platform == 'haiku':
        return [_attempt(['open', folder])]
    return []


def terminal_attempts(platform, folder):
    """Candidate terminals for folder. The first one whose program exists wins.

    Entries without 'check' are always available (cmd.exe on Windows).
    """
    folder = os.path.abspath(folder)
    if platform == 'windows':
        return [
            _attempt(['wt.exe', '-d', folder], check='wt.exe', cwd=folder),
            _attempt(['wt', '-d', folder], check='wt', cwd=folder),
            _attempt(['cmd.exe', '/c', 'start', '', 'cmd.exe', '/K'], cwd=folder),
        ]
    if platform == 'macos':
        return [_attempt(['open', '-a', 'Terminal', folder], cwd=folder)]
    if platform == 'linux':
        # Prefer terminals that take an explicit directory. A generic
        # x-terminal-emulator often ignores the process cwd when one window
        # is already open.
        specs = (
            ('gnome-terminal', ['--working-directory', folder]),
            ('kgx', ['--working-directory', folder]),
            ('konsole', ['--workdir', folder]),
            ('xfce4-terminal', ['--working-directory', folder]),
            ('mate-terminal', ['--working-directory', folder]),
            ('tilix', ['--working-directory', folder]),
            ('kitty', ['--directory', folder]),
            ('alacritty', ['--working-directory', folder]),
            ('wezterm', ['start', '--cwd', folder]),
            ('x-terminal-emulator', []),
            ('xterm', []),
        )
        return [
            _attempt([name] + args, check=name, cwd=folder)
            for name, args in specs
        ]
    return []


def first_available(attempts, is_available):
    """First attempt whose 'check' program exists. Missing 'check' is always usable."""
    for attempt in attempts:
        name = attempt.get('check')
        if name and not is_available(name):
            continue
        return attempt
    return None


def available_attempts(attempts, is_available):
    """Every attempt that can be launched, in order."""
    chosen = []
    for attempt in attempts:
        name = attempt.get('check')
        if name and not is_available(name):
            continue
        chosen.append(attempt)
    return chosen
