# utf-8 w/bom, utf-16-be-bom, utf-16-le-bom, utf-32-be-bom, utf-32-le-bom
BOM_MARKERS = [
    b"\xef\xbb\xbf",
    b"\xfe\xff",
    b"\xfe\xff",
    b"\xff\xfe",
    b"\x00\x00\xfe\xff",
    b"\xff\xfe\x00\x00",
]


def is_this_utf8(fp):
    what = ""
    is_utf8 = True
    f = open(fp, "rt")
    try:
        buff = f.read(4)
        first_byte = buff[:1].encode("utf-8")
        has_bom = first_byte in BOM_MARKERS
        if has_bom:
            is_utf8 = False  # only focus on plain utf-8
            what = 'utf* with BOM'
    except UnicodeDecodeError:
        is_utf8 = False
        what = "ascii"
    f.close()

    return is_utf8, what
