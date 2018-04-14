from ecdsa import SigningKey, SECP256k1
from ethereum.utils import privtoaddr, checksum_encode

class Ethereum:
    priv = None
    address = None
    def get_address(self, priv):
        return checksum_encode(privtoaddr(priv.to_string()))

    def generate_wallet(self):
        priv = SigningKey.generate(curve=SECP256k1)
        address = self.get_address(priv)
        return {'private_key': priv.to_string().hex(), 'address': address}
