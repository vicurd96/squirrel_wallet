from hashlib import sha256
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')
def check_bc(bc):
    bcbytes = decode_base58(bc, 25)
    if not bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]:
        raise ValidationError(_("Sorry, you introduced an invalid address."))
