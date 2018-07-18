import ctypes
import ctypes.util
import hashlib

#from .base58 import encode as base58_encode

alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
base_count = len(alphabet)


def encode(num):
    """ Returns num in a base58-encoded string """
    encode = ''

    if (num < 0):
        return ''

    while (num >= base_count):
        mod = num % base_count
        encode = alphabet[mod] + encode
        num = num // base_count

    if (num):
        encode = alphabet[num] + encode

    return encode


def decode(s):
    """ Decodes the base58-encoded string s into an integer """
    decoded = 0
    multi = 1
    s = s[::-1]
    for char in s:
        decoded += multi * alphabet.index(char)
        multi = multi * base_count

    return decoded


ssl_library = ctypes.cdll.LoadLibrary(ctypes.util.find_library("ssl"))

# Since "1" is a zero byte, it won’t be present in the output address.
addr_prefix = "1"

version = 0

def gen_ecdsa_pair():
    NID_secp160k1 = 708
    NID_secp256k1 = 714
    k = ssl_library.EC_KEY_new_by_curve_name(NID_secp256k1)

    if ssl_library.EC_KEY_generate_key(k) != 1:
        raise Exception("internal error?")

    bignum_private_key = ssl_library.EC_KEY_get0_private_key(k)
    size = (ssl_library.BN_num_bits(bignum_private_key)+7)//8
    storage = ctypes.create_string_buffer(size)
    ssl_library.BN_bn2bin(bignum_private_key, storage)
    private_key = storage.raw

    size = ssl_library.i2o_ECPublicKey(k, 0)
    storage = ctypes.create_string_buffer(size)
    ssl_library.i2o_ECPublicKey(
        k,
        ctypes.byref(ctypes.pointer(storage))
    )
    public_key = storage.raw

    ssl_library.EC_KEY_free(k)
    return public_key, private_key

def ecdsa_get_coordinates(public_key):
    x = bytes(public_key[1:33])
    y = bytes(public_key[33:65])
    return x, y

def generate_address(public_key):
    assert isinstance(public_key, bytes)

    x, y = ecdsa_get_coordinates(public_key)

    s = b"\x04" + x + y

    hasher = hashlib.sha256()
    hasher.update(s)
    r = hasher.digest()

    hasher = hashlib.new("ripemd160")
    hasher.update(r)
    r = hasher.digest()

    addr = base58_check(r, version=version)
    if addr_prefix:
        return "{}{}".format(addr_prefix, addr)
    else:
        return addr

def base58_check(src, version):
    src = bytes([version]) + src
    hasher = hashlib.sha256()
    hasher.update(src)
    r = hasher.digest()

    hasher = hashlib.sha256()
    hasher.update(r)
    r = hasher.digest()

    checksum = r[:4]
    s = src + checksum

    return encode(int.from_bytes(s, "big"))

def generate_wallet():
    public_key, private_key = gen_ecdsa_pair()

    return {'priv_key': base58_check(private_key, version=239+version), 'address': generate_address(public_key) }
