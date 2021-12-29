import os

# bytes pretty-printing, borrowed from https://stackoverflow.com/a/12912296
UNITS_MAPPING = [
    (1<<50, ' PB'),
    (1<<40, ' TB'),
    (1<<30, ' GB'),
    (1<<20, ' MB'),
    (1<<10, ' KB'),
    (1, (' byte', ' bytes')),
]


def pretty_size(bytes, units=UNITS_MAPPING):
    """Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix


def size_b(filename):
    """Return size of file under filename in bytes"""
    try:
        return os.path.getsize(filename)
    except FileNotFoundError:
        return 0


def print_tuple_size(list_of_tuples, max_items=100):
    """
    Pyinstaller deals in many cases with list of 3-elements tuples.
    Second element of such tuple is a path to a file.
    Here we loop over such list, sort it according to a file size (starting from the largest)
    and print it. We also print total size of all files in a tuple.
    """
    total_size = 0
    for item in sorted(list_of_tuples, key=lambda item: size_b(item[1]), reverse=True)[:max_items]:
        size_to_print = pretty_size(size_b(item[1]))
        total_size += size_b(item[1])
        print(f"item {item} {size_to_print}")
    total_size = pretty_size(total_size)
    print(f"total size {total_size}")


def print_header(name):
    """Nice printing of header sections"""
    print("-"*120)
    print(" "*60 + name)
    print("-"*120)