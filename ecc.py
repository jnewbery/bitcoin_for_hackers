from binascii import hexlify, unhexlify
from io import BytesIO
from random import randint

from helper import encode_base58, encode_base58_checksum, hash160, double_sha256


class FieldElement:

    def __init__(self, num, prime):
        self.num = num
        self.prime = prime
        if self.num >= self.prime or self.num < 0:
            error = 'Num {} not in field range 0 to {}'.format(
                self.num, self.prime - 1)
            raise RuntimeError(error)

    def __eq__(self, other):
        if other is None:
            return False
        return self.num == other.num and self.prime == other.prime

    def __ne__(self, other):
        if other is None:
            return True
        return self.num != other.num or self.prime != other.prime

    def __repr__(self):
        return 'FieldElement_{}({})'.format(self.prime, self.num)

    def __add__(self, other):
        num = (self.num + other.num) % self.prime
        return self.__class__(num=num, prime=self.prime)

    def __sub__(self, other):
        num = (self.num - other.num) % self.prime
        return self.__class__(num=num, prime=self.prime)

    def __mul__(self, other):
        num = (self.num * other.num) % self.prime
        return self.__class__(num=num, prime=self.prime)

    def __rmul__(self, coefficient):
        num = (self.num * coefficient) % self.prime
        return self.__class__(num=num, prime=self.prime)

    def __pow__(self, n):
        n = n % (self.prime - 1)
        num = pow(self.num, n, self.prime)
        return self.__class__(num=num, prime=self.prime)

    def __truediv__(self, other):
        other_inv = pow(other.num, self.prime - 2, self.prime)
        return self * self.__class__(num=other_inv, prime=self.prime)


class Point:

    def __init__(self, x, y, a, b):
        self.a = a
        self.b = b
        if x is None and y is None:
            # point at infinity
            self.x = None
            self.y = None
            return
        if y**2 != x**3 + self.a * x + self.b:
            raise RuntimeError('Not a point on the curve')
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y \
            and self.a == other.a and self.b == other.b

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y \
            or self.a != other.a or self.b != other.b

    def __repr__(self):
        if self.x is None:
            return 'Point(infinity)'
        else:
            return 'Point({},{})'.format(self.x, self.y)

    def __add__(self, other):
        # identity
        if self.x is None:
            return other
        if other.x is None:
            return self
        if self.x == other.x:
            if self.y != other.y:
                # point at infinity
                return self.__class__(x=None, y=None, a=self.a, b=self.b)
            # we're adding a point to itself
            s = (3 * self.x**2 + self.a) / (2 * self.y)
            x = s**2 - 2 * self.x
            y = s * (self.x - x) - self.y
            return self.__class__(x=x, y=y, a=self.a, b=self.b)
        else:
            s = (other.y - self.y) / (other.x - self.x)
            x = s**2 - self.x - other.x
            y = s * (self.x - x) - self.y
            return self.__class__(x=x, y=y, a=self.a, b=self.b)

    def __rmul__(self, coefficient):
        # naive way - see below for binary expansion method
        result = self.__class__(x=None, y=None, a=self.a, b=self.b)
        for i in range(coefficient):
            result += self
        return result


A = 0
B = 7
P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class S256Field(FieldElement):

    def __init__(self, num, prime=None):
        super().__init__(num=num, prime=P)

    def hex(self):
        return '{:x}'.format(self.num).zfill(64)

    def __repr__(self):
        return self.hex()

    def sqrt(self):
        return self**((P + 1) // 4)


class S256Point(Point):
    bits = 256

    def __init__(self, x, y, a=None, b=None):
        a, b = S256Field(A), S256Field(B)
        if x is None:
            super().__init__(x=None, y=None, a=a, b=b)
        elif type(x) == int:
            super().__init__(x=S256Field(x), y=S256Field(y), a=a, b=b)
        else:
            super().__init__(x=x, y=y, a=a, b=b)

    def __repr__(self):
        if self.x is None:
            return 'Point(infinity)'
        else:
            return '({},{})'.format(self.x, self.y)

    def __rmul__(self, coefficient):
        # current will undergo binary expansion
        current = self
        # result is what we return, starts at 0
        result = S256Point(None, None)
        # we double 256 times and add where there is a 1 in the binary
        # representation of coefficient
        for i in range(self.bits):
            if coefficient & 1:
                result += current
            current += current
            # we shift the coefficient to the right
            coefficient >>= 1
        return result

    def sec(self, compressed=True):
        if compressed:
            if self.y.num % 2 == 1:
                prefix = '03'
            else:
                prefix = '02'
            return unhexlify('{}{}'.format(prefix, self.x.hex()))
        else:
            return unhexlify('04{}{}'.format(self.x.hex(), self.y.hex()))

    def address(self, compressed=True, testnet=False):
        h160 = hash160(self.sec(compressed=compressed))
        if testnet:
            prefix = b'\x6f'
        else:
            prefix = b'\x00'
        raw = prefix + h160
        raw = raw + double_sha256(raw)[:4]
        return encode_base58(raw).decode('ascii')

    def verify(self, z, sig):
        if isinstance(z, str):
            # Hash string and convert to int
            z = int.from_bytes(hash160(z.encode()), 'big')
        u = z * pow(sig.s, N - 2, N) % N
        v = sig.r * pow(sig.s, N - 2, N) % N
        return (u * G + v * self).x.num == sig.r

    @classmethod
    def parse(self, sec_bin):
        '''returns a Point object from a compressed sec binary (not hex)
        '''
        if sec_bin[0] == 4:
            x = int(hexlify(sec_bin[1:33]), 16)
            y = int(hexlify(sec_bin[33:65]), 16)
            return S256Point(x=x, y=y)
        is_even = sec_bin[0] == 2
        x = S256Field(int(hexlify(sec_bin[1:]), 16))
        # right side of the equation y^2 = x^3 + 7
        alpha = x**3 + S256Field(B)
        # solve for left side
        beta = alpha.sqrt()
        if beta.num % 2 == 0:
            even_beta = beta
            odd_beta = S256Field(P - beta.num)
        else:
            even_beta = S256Field(P - beta.num)
            odd_beta = beta
        if is_even:
            return S256Point(x, even_beta)
        else:
            return S256Point(x, odd_beta)


G = S256Point(
    0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
    0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)


class Signature:

    def __init__(self, r, s):
        self.r = r
        self.s = s

    def __repr__(self):
        return '({:.4}.., {:.4}..)'.format(str(self.r), str(self.s))

    def der(self):
        rbin = self.r.to_bytes(32, byteorder='big')
        # if rbin has a high bit, add a 00
        if rbin[0] > 128:
            rbin = b'\x00' + rbin
        result = bytes([2, len(rbin)]) + rbin
        sbin = self.s.to_bytes(32, byteorder='big')
        # if sbin has a high bit, add a 00
        if sbin[0] > 128:
            sbin = b'\x00' + sbin
        result += bytes([2, len(sbin)]) + sbin
        return bytes([0x30, len(result)]) + result

    @classmethod
    def parse(cls, signature_bin):
        s = BytesIO(signature_bin)
        compound = s.read(1)[0]
        if compound != 0x30:
            raise RuntimeError("Bad Signature")
        length = s.read(1)[0]
        if length + 2 != len(signature_bin):
            raise RuntimeError("Bad Signature Length")
        marker = s.read(1)[0]
        if marker != 0x02:
            raise RuntimeError("Bad Signature")
        rlength = s.read(1)[0]
        r = int(hexlify(s.read(rlength)), 16)
        marker = s.read(1)[0]
        if marker != 0x02:
            raise RuntimeError("Bad Signature")
        slength = s.read(1)[0]
        s = int(hexlify(s.read(slength)), 16)
        if len(signature_bin) != 6 + rlength + slength:
            raise RuntimeError("Signature too long")
        return cls(r, s)


class PrivateKey:

    def __init__(self, secret):
        self.secret = secret
        self.point = secret * G

    def hex(self):
        return '{:x}'.format(self.secret).zfill(64)

    def sign(self, z):
        if isinstance(z, str):
            # Hash string and convert to int
            z = int.from_bytes(hash160(z.encode()), 'big')
        k = randint(0, 2**256)
        r = (k * G).x.num
        s = (z + r * self.secret) * pow(k, N - 2, N) % N
        if s * 2 > N:
            s = N - s
        return Signature(r, s)

    def wif(self, compressed=True, testnet=False):
        if testnet:
            prefix = b'\xef'
        else:
            prefix = b'\x80'
        if compressed:
            postfix = b'\x01'
        else:
            postfix = b''
        binary = self.secret.to_bytes(32, 'big')
        return encode_base58_checksum(prefix + binary + postfix)

    def __repr__(self):
        return str(self.secret)


class Keypair():
    def __init__(self):
        self.privkey = PrivateKey(randint(0, 2**256))
        self.pubkey = self.privkey.point

    def __repr__(self):
        return "privkey: 0x{:<7.7}..., pubkey: 0x{:<7.7}...".format(self.privkey.hex(), self.pubkey.sec().hex())
