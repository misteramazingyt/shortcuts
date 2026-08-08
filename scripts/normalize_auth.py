#!/usr/bin/env python3
"""Normalize Apple ID auth data into the plain plist shortcut-sign expects.

appleid-key-dumper serialized the auth with NSKeyedArchiver (an object-graph
wrapper: $archiver / $objects / $top). shortcut-sign and iOS expect a *plain*
property list with the four signing fields at the top level, exactly like the
auth embedded in a real contact-signed shortcut:

    AppleIDCertificateChain   array of DER certificates
    SigningPublicKey          65-byte X9.63 EC public key
    SigningPublicKeySignature 256-byte RSA signature
    AppleIDValidationRecord   the validation record's data blob

A wrapped auth leaves the certificate chain unreachable, so the signature has
"no cert chain" and iOS rejects the shortcut as invalid. This unwraps it.

Usage:
    python3 normalize_auth.py <input-auth> <output-auth>

If the input is already a plain plist with these keys, it is copied through
unchanged, so a future fixed dumper needs no special-casing.
"""

import plistlib
import sys
from plistlib import UID

REQUIRED = {
    "AppleIDCertificateChain",
    "SigningPublicKey",
    "SigningPublicKeySignature",
    "AppleIDValidationRecord",
}


def _resolve(objs, node):
    """Resolve one NSKeyedArchiver node to a plain Python value."""
    if isinstance(node, UID):
        node = objs[node.data]
    if isinstance(node, dict):
        if "NS.data" in node:  # NSData / NSMutableData
            return bytes(_resolve(objs, node["NS.data"]))
        if "NS.objects" in node:  # NSArray
            return [_resolve(objs, u) for u in node["NS.objects"]]
        return node  # a custom object (e.g. the validation record)
    if isinstance(node, (bytes, bytearray)):
        return bytes(node)
    return node


def _validation_record_data(objs, node):
    """Pull the raw NSData out of an SFAppleIDValidationRecord object."""
    if isinstance(node, UID):
        node = objs[node.data]
    if isinstance(node, (bytes, bytearray)):
        return bytes(node)
    if isinstance(node, dict):
        # The record object stores its bytes under a "Data" ivar.
        for key in ("Data", "data", "NS.data"):
            if key in node:
                return bytes(_resolve(objs, node[key]))
    raise ValueError("could not locate validation record data")


def normalize(raw):
    plist = plistlib.loads(raw)

    # Already plain? Pass through.
    if isinstance(plist, dict) and REQUIRED.issubset(plist):
        return raw

    if not (isinstance(plist, dict) and "$objects" in plist and "$top" in plist):
        raise ValueError("auth is neither a plain plist nor an NSKeyedArchiver archive")

    objs = plist["$objects"]
    root = objs[list(plist["$top"].values())[0].data]
    keys = [_resolve(objs, u) for u in root["NS.keys"]]
    value_nodes = root["NS.objects"]

    out = {}
    for key, node in zip(keys, value_nodes):
        if key == "AppleIDValidationRecord":
            out[key] = _validation_record_data(objs, node)
        else:
            out[key] = _resolve(objs, node)

    missing = REQUIRED - set(out)
    if missing:
        raise ValueError(f"auth is missing fields after unwrap: {sorted(missing)}")

    return plistlib.dumps(out, fmt=plistlib.FMT_BINARY)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: normalize_auth.py <input-auth> <output-auth>")
    with open(sys.argv[1], "rb") as handle:
        raw = handle.read()
    result = normalize(raw)
    with open(sys.argv[2], "wb") as handle:
        handle.write(result)
    print(f"normalized auth -> {sys.argv[2]} ({len(result)} bytes)")


if __name__ == "__main__":
    main()
