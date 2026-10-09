import struct

from eerie_uk.grib import strip_local_section


def _section(number, payload):
    return struct.pack(">IB", 5 + len(payload), number) + payload


def _message(*sections):
    body = b"".join(sections) + b"7777"
    return b"GRIB\x00\x00\x00\x02" + struct.pack(">Q", 16 + len(body)) + body


def test_strip_local_section_removes_section_2_and_fixes_length():
    with_local = _message(_section(1, b"a" * 16), _section(2, b"local"), _section(3, b"grid"))
    without = _message(_section(1, b"a" * 16), _section(3, b"grid"))
    assert strip_local_section(with_local) == without


def test_strip_local_section_leaves_other_messages_alone():
    without = _message(_section(1, b"a" * 16), _section(3, b"grid"))
    assert strip_local_section(without) == without
    assert strip_local_section(b"not a grib message") == b"not a grib message"
