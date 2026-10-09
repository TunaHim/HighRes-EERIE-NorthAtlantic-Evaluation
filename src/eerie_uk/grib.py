"""Decoder for the raw GRIB chunks the DKRZ cloud serves for IFS output.

The IFS collections declare the Zarr compressor ``gribscan.rawgrib``: each
chunk is one GRIB2 message. The EERIE messages carry an ECMWF local section
(section 2, local definition 43) written with an older layout than current
ecCodes expects, which makes ecCodes misread the rest of the message
("Invalid size 52 found for section_2"). The local section holds only MARS
bookkeeping, so it is dropped before decoding; the field values are untouched.
"""

from __future__ import annotations

import struct

import numcodecs
from numcodecs.abc import Codec
from numcodecs.compat import ndarray_copy

CODEC_ID = "gribscan.rawgrib"


def strip_local_section(message: bytes) -> bytes:
    """Return a GRIB2 message without its local-use section (section 2)."""
    if message[:4] != b"GRIB" or message[7] != 2:
        return message
    total = struct.unpack(">Q", message[8:16])[0]
    position = 16
    while position + 5 <= total:
        length = struct.unpack(">I", message[position : position + 4])[0]
        number = message[position + 4]
        if number == 2:
            body = message[16:position] + message[position + length : total]
            return message[:8] + struct.pack(">Q", total - length) + body
        if number > 2 or length == 0:
            break
        position += length
    return message


class RawGribCodec(Codec):
    """Read-only codec: one GRIB2 message in, its values out."""

    codec_id = CODEC_ID

    def encode(self, buf):
        raise NotImplementedError("the GRIB codec is read-only")

    def decode(self, buf, out=None):
        import eccodes

        handle = eccodes.codes_new_from_message(strip_local_section(bytes(buf)))
        try:
            data = eccodes.codes_get_array(handle, "values")
        finally:
            eccodes.codes_release(handle)
        return data if out is None else ndarray_copy(data, out)


def register() -> None:
    """Make the codec available to zarr (replaces gribscan's if present)."""
    numcodecs.register_codec(RawGribCodec)
