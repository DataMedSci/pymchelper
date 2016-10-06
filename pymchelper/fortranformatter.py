PROC_MIN_FIELD_WIDTH = 46
PROC_DECIMAL_CHAR = '.'
PROC_NO_LEADING_BLANK = False

# based on https://bitbucket.org/brendanarnold/py-fortranformat


def _swapchar(s, ind, newch):
    """
    Helper function to make chars in a string mutableish
    """
    if 0 < ind >= len(s):
        raise IndexError('index out of range')
    return s[:ind] + newch + s[ind + 1:]


def _compose_nan_string(w, ftype):
    if ftype in ['B', 'O', 'Z']:
        return ''
    else:
        # Allow at least 'NaN' to be printed
        if w == 0:
            w = 4  # n.b. this is what is set in Gfortran 4.4.0
        if w < 3:
            return '*' * w
    return 'NaN'.rjust(w)


def _calculate_sign(state, negative_flag):
    s = ''
    if negative_flag:
        s = '-'
    elif state['incl_plus']:
        s = '+'
    else:
        s = ''
    return s


def _compose_inf_string(w, ftype, sign_bit):
    if ftype in ['B', 'O', 'Z']:
        return ''
    else:
        sign = '+'
        # Allow at least 'Inf' to be printed
        if w == 0:
            w = 4
        if w < 3:
            return '*' * w
        # Change sign if negative
        if sign_bit:
            sign = '-'
            # Require sign if negative, if no space then overflow
            if w == 3:
                return '*' * w
        # Output long version if long enough
        if w > 8:
            return (sign + 'Infinity').rjust(w)
        # Output shortened version with sign if long enough
        elif w > 3:
            return (sign + 'Inf').rjust(w)
        # Should only output short version with no sign if positive
        else:
            return 'Inf'


def _compose_float_string(w, e, d, state, val, ftype):
    """
    Adapted from code in glibfortran which is written in C so is somwhat
    'bit-pushy' in nature. Writes the value to an initial string (buffer)
    and then pulls the subsequent strings from that
    """
    if (d < 0) or (d is None):
        raise Exception('Unspecified precision')
    # Make sure they are ints
    d = int(round(d))
    if e is not None:
        e = int(round(e))
    if w is not None:
        w = int(round(w))
    # ==== write_float ==== (function)
    edigits = 4  # Largest number of exponent digits expected
    # Otherwise convert knowing what the required precision is (i.e. knowing d)
    ndigits = d
    if ndigits > (PROC_MIN_FIELD_WIDTH - 4 - edigits):
        ndigits = PROC_MIN_FIELD_WIDTH - 4 - edigits
    # ==== WRITE_FLOAT ==== (macro)
    # Determine sign of value
    if val == 0.0:
        sign_bit = '-' in str(val)
    else:
        sign_bit = val < 0
    # handle the nan and inf cases
    if type(val) is float and val != val:
        return _compose_nan_string(w, ftype)
    infinity = 1e1000000
    if val in (-infinity, infinity):
        return _compose_inf_string(w, ftype, sign_bit)
    tmp = abs(val)
    # Round the input if the input is less than 1
    zero_flag = (tmp == 0)
    # === DTOA === (macro)
    # write the tmp value to the string buffer
    # sprintf seems to allow negative number of decimal places,
    # need to correct for this
    if ndigits <= 0:
        fmt = "%+-#{:d}e".format(PROC_MIN_FIELD_WIDTH)
    else:
        fmt = "%+-#{:d}.{:d}e".format(PROC_MIN_FIELD_WIDTH, ndigits - 1)
    buff = fmt % tmp
    # === WRITE_FLOAT === (macro)
    return _output_float(w, d, e, state, ftype, buff, sign_bit, zero_flag, ndigits, edigits)


def _output_float(w, d, e, state, ft, buff, sign_bit, zero_flag, ndigits, edigits):
    """
    TODO
    :param w:
    :param d:
    :param e:
    :param state:
    :param ft:
    :param buff:
    :param sign_bit:
    :param zero_flag:
    :param ndigits:
    :param edigits:
    :return:
    """
    # nbefore - number of digits before the decimal point
    # nzero - number of zeros after the decimal point
    # nafter - number of digits after the decimal point
    # nzero_real - number of zeros after the decimal point
    #               regardles of the precision

    # Some hacks to change None to -1 (C convention)
    if w is None:
        w = -1
    if e is None:
        e = -1
    nzero_real = -1
    sign = _calculate_sign(state, sign_bit)
    # Some debug
    if d != 0:
        assert (buff[2] in ['.', ','])
        assert (buff[ndigits + 2] == 'e')
    # Read in the exponent
    ex = int(buff[ndigits + 3:]) + 1
    # Handle zero case
    if zero_flag:
        ex = 0
        sign = _calculate_sign(state, False)
        # Handle special case
        if w == 0:
            w = d + 2
    # Get rid of the decimal and the initial sign i.e. normalise the digits
    digits = buff[1] + buff[3:]
    # Find out where to place the decimal point
    if ft in ['E', 'D']:
        i = state['scale']
        if (d <= 0) and (i == 0):
            raise Exception("Precision not greater " "than zero in format specifier 'E' or 'D'")
        if (i <= -d) or (i >= (d + 2)):
            raise Exception("Scale factor out of range " "in format specifier 'E' or 'D'")
        if not zero_flag:
            ex = ex - i
        if i < 0:
            nbefore = 0
            nzero = -i
            nafter = d + i
        elif i > 0:
            nbefore = i
            nzero = 0
            nafter = (d - i) + 1
        else:
            nbefore = 0
            nzero = 0
            nafter = d
        expchar = ft
    # Round the value
    if (nbefore + nafter) == 0:
        ndigits = 0
        if (nzero_real == d) and (int(digits[0]) >= 5):
            # We rounded to zero but shouldn't have
            nzero -= 1
            nafter = 1
            digits = '1' + digits[1:]
            ndigits = 1
    elif (nbefore + nafter) < ndigits:
        ndigits = nbefore + nafter
        i = ndigits
        if int(digits[i]) >= 5:
            # Propagate the carry
            i -= 1
            while i >= 0:
                digit = int(digits[i])
                if digit != 9:
                    digits = _swapchar(digits, i, str(digit + 1))
                    break
                else:
                    digits = _swapchar(digits, i, '0')
                i -= 1
            # Did the carry overflow?
            if i < 0:
                digits = '1' + digits
                if ft == 'F':
                    if nzero > 0:
                        nzero -= 1
                        nafter += 1
                    else:
                        nbefore += 1
                elif ft == 'EN':
                    nbefore += 1
                    if nbefore == 4:
                        nbefore = 1
                        ex += 3
                else:
                    ex += 1
    # Calculate the format of the exponent field
    if expchar is not None:
        # i = abs(ex)
        # while i >= 10:
        #     edigits = edigits + 1
        #     i = i / 10.0
        if e < 0:
            # Width not specified, must be no more than 3 digits
            if (ex > 999) or (ex < -999):
                edigits = -1
            else:
                edigits = 4
                if (ex > 99) or (ex < -99):
                    expchar = ' '
        else:
            assert (isinstance(ex, int))
            edigits = len(str(abs(ex)))
            # Exponenet width specified, check it is wide enough
            if edigits > e:
                edigits = -1
            else:
                edigits = e + 2
    else:
        edigits = 0
    # Zero values always output as positive,
    # even if the value was egative before rounding
    i = 0
    while i < ndigits:
        if digits[i] != '0':
            break
        i += 1
    if i == ndigits:
        # The output is zero so set sign accordingly
        sign = _calculate_sign(state, False)
    # Pick a field size if none was specified
    if w <= 0:
        w = nbefore + nzero + nafter + 1 + len(sign)
    # Work out how much padding is needed
    nblanks = w - (nbefore + nzero + nafter + edigits + 1)
    if sign != '':
        nblanks -= 1
    # Check value fits in specified width
    if (nblanks < 0) or (edigits == -1):
        return '*' * w
    # See if we have space for a zero before the decimal point
    if (nbefore == 0) and (nblanks > 0):
        leadzero = True
        nblanks -= 1
    else:
        leadzero = False
    out = ''
    # Pad to full field width
    if nblanks > 0:  # dtp->u.p.no_leading_blank
        out += ' ' * nblanks
    # Attach the sign
    out += sign
    # Add the lead zero if necessary
    if leadzero:
        out += '0'
    # Output portion before the decimal point padded with zeros
    if nbefore > 0:
        if nbefore > ndigits:
            out = out + digits[:ndigits] + (' ' * (nbefore - ndigits))
            digits = digits[ndigits:]
            ndigits = 0
        else:
            i = nbefore
            out += digits[:i]
            digits = digits[i:]
            ndigits -= i
    # Output the decimal point
    out += PROC_DECIMAL_CHAR
    # Output the leading zeros after the decimal point
    if nzero > 0:
        out += '0' * nzero
    # Output the digits after the decimal point, padded with zeros
    if nafter > 0:
        if nafter > ndigits:
            i = ndigits
        else:
            i = nafter
        zeros = '0' * (nafter - i)
        out = out + digits[:i] + zeros
        digits = digits[nafter:]
        ndigits -= nafter
    # Output the exponent
    if expchar is not None:
        if expchar != ' ':
            out += expchar
            edigits -= 1
        fmt = '%+0' + str(edigits) + 'd'
        tmp_buff = fmt % ex
        out += tmp_buff
    return out


def format_d(w, d, val):
    """
    TODO
    :param w:
    :param d:
    :param val:
    :return:
    """
    e = None
    ftype = 'D'
    state = {'blanks_as_zeros': False, 'incl_plus': False, 'position': 0, 'scale': 0, 'halt_if_no_vals': False}
    return _compose_float_string(w, e, d, state, val, ftype)


def format_e(w, d, val):
    """
    TODO
    :param w:
    :param d:
    :param val:
    :return:
    """
    e = None
    ftype = 'E'
    state = {'blanks_as_zeros': False, 'incl_plus': False, 'position': 0, 'scale': 0, 'halt_if_no_vals': False}
    return _compose_float_string(w, e, d, state, val, ftype)
