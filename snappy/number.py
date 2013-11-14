try:
    from sage.libs.pari.gen import pari, gen
    from sage.libs.pari.gen import prec_words_to_dec, prec_words_to_bits
except ImportError:
    from cypari.gen import pari, gen
    from cypari.gen import prec_words_to_dec, prec_words_to_bits
import re
strip_zeros = re.compile('(.*\..*?[0-9]{1})0*$')
left_zeros = re.compile('0\.0*')

class Number(object):
    """
    Python class which wraps PARI GENs of type t_INT, t_REAL or
    t_COMPLEX.

    A number has an optional accuracy attribute.  THE ACCURACY DOES
    NOT ACCOUNT FOR ROUNDOFF ERROR. By default, the accuracy of a
    Number is None.

    The optional accuracy attribute is set only for Numbers that are
    computed from tetrahedron shapes.  It represents the number of
    digits to the right of the decimal point that can be expected to
    be correct.  The accuracy of a shape is computed by the SnapPea
    kernel while performing Newton iterations to compute the shape.
    The value is the number of digits to the right of the decimal
    point for which the last two values computed by Newton's method
    agree.

    When doing arithmetic with SnapPy Numbers, the accuracy of a
    result is set to the smaller of the accuracies of the operands.

    When a number with accuracy is converted to a string, the value is
    rounded to a decimal number for which all digits to the right of
    the decimal point (including trailing zeros) have place value
    exceeds the accuracy. If the accuracy is None, all digits are
    included, except that trailing zeros are removed.
    """
    # When doctesting, we want our numerical results to print
    # with fixed (somewhat low) accuracy.  In all normal
    # circumstances this flag is set to None and then ignored
    _accuracy_for_testing = None

    def __init__(self, data, accuracy=None, precision=19):
        if isinstance(data, gen):
            self.gen = data
        else:
            old_precision = pari.set_real_precision(precision)
            self.gen = pari(data)
            pari.set_real_precision(old_precision)
        type = self.gen.type()
        if not type in ('t_INT', 't_REAL', 't_COMPLEX'):
            raise ValueError('Invalid initialization for a Number')
        if type == 't_INT':
            self.accuracy = 0
        else:
            self.accuracy = accuracy
        self.precision = precision
        self.bits = prec_words_to_bits(self.gen.real().sizeword())
    def _pari_(self):
        return self.gen
    def _get_acc_prec(self, other):
        return (min(self.accuracy, other.accuracy),
                min(self.precision, other.precision))
    def __call__(self):  # makes properties also work as methods
        return self
    def __repr__(self):
        gen = self.gen
        if gen.imag() == 0:
            return self._real_string(gen, self.accuracy)
        else:
            real_part = self._real_string(gen.real(), self.accuracy)
            imag_part = self._real_string(gen.imag(), self.accuracy)
            return ('%s + %s*I'%(real_part, imag_part)).replace('+ -','- ')
    def _real_string(self, gen, accuracy):
        if gen == 0:
            return '0'
        if self._accuracy_for_testing:
            accuracy = self._accuracy_for_testing
        if accuracy:
            # Trick PARI into rounding to the correct number of digits.
            # Simulates the printf %.Nf format, where N is the accuracy.
            int_part = gen.truncate().abs()
            if int_part == 0:
                # Deal with zeros to the right of the decimal point.
                try:
                    left_side = 2 - len(left_zeros.findall(str(gen))[0])
                except IndexError:  # no zeros
                    left_side = 0
            else:
                left_side = len(str(int_part))
            old_precision = pari.set_real_precision(left_side+accuracy)
            result = str(gen)
            pari.set_real_precision(old_precision)
        else:
            old_precision = pari.set_real_precision(self.precision)
            result = str(gen)
            try:
                result = strip_zeros.findall(result)[0]
            except IndexError:
                pass
            pari.set_real_precision(old_precision)
        return result
    def __float__(self):
        return float(self.gen)
    def __complex__(self):
        return complex(self.gen)
    def __int__(self):
        return int(float(self.gen))
    def __add__(self, other):
        return Number(self.gen.__add__(other), *self._get_acc_prec(other))
    def __sub__(self, other):
        return Number(self.gen.__sub__(other), *self._get_acc_prec(other))
    def __mul__(self, other):
        return Number(self.gen.__mul__(other), *self._get_acc_prec(other))
    def __div__(self, other):
        return Number(self.gen.__div__(other), *self._get_acc_prec(other))
    def __radd__(self, other):
        return Number(self.gen.__radd__(other), *self._get_acc_prec(other))
    def __rsub__(self, other):
        return Number(self.gen.__rsub__(other), *self._get_acc_prec(other))
    def __rmul__(self, other):
        return Number(self.gen.__rmul__(other), *self._get_acc_prec(other))
    def __rdiv__(self, other):
        return Number(self.gen.__rdiv__(other), *self._get_acc_prec(other))
    def __eq__(self, other):
        return self.gen.__eq__(other)
    def __ne__(self, other):
        return self.gen.__ne__(other)
    def __lt__(self, other):
        return self.gen.__lt__(other)
    def __gt__(self, other):
        return self.gen.__gt__(other)
    def __le__(self, other):
        return self.gen.__le__(other)
    def __ge__(self, other):
        return self.gen.__ge__(other)
    def __neg__(self):
        return Number(-self.gen, self.accuracy, self.precision)
    def __abs__(self):
        return Number(abs(self.gen), self.accuracy, self.precision)
    def __inv__(self):
        return Number(inv(self.gen), self.accuracy, self.precision)
    def __pow__(self, *args):
        return Number(self.gen.__pow__( *args), self.accuracy, self.precision)
    @property
    def real(self):
        return Number(self.gen.real(), self.accuracy, self.precision)
    @property
    def imag(self):
        return Number(self.gen.imag(), self.accuracy, self.precision)
    ### This is broken
    def dotdot(self, digits):
        """
        Return a string representation in which real and imaginary parts
        of the mantissa are truncated to the specified accuracy and
        followed by ellipses.
        """
        real_part = self._real_string(self.gen.real(), digits) + '...'
        if self.gen.imag == 0:
            return real_part
        else:
            imag_part = self._real_string(self.gen.imag(), digits) + '...'
            result = '%s + %s'%(real_part[:digits], imag_part)
            return result.replace('+ -', ' - ')
    def pari_type(self):
        return self.gen.type()
    def volume(self):
        """
        Return the volume of a tetrahedron with this shape
        """
        z = self.gen
        zz = 1/(1-z)
        zzz = 1 - 1/z
        A = z/z.abs()
        B = zz/zz.abs()
        C = zzz/zzz.abs()
        bits = self.bits
        volume = (   (A*A).dilog(precision=bits).imag()
                   + (B*B).dilog(precision=bits).imag()
                   + (C*C).dilog(precision=bits).imag()
                  )/2
        return Number(volume, self.accuracy, self.precision)
