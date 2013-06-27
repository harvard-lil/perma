class base:
    BASE2 = "01"
    BASE10 = "0123456789"
    BASE16 = "0123456789ABCDEF"
    BASE58 = "123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    BASE62 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"
 
    @staticmethod
    def convert(number,fromdigits,todigits):
        """ converts a "number" between two bases of arbitrary digits
 
       The input number is assumed to be a string of digits from the
       fromdigits string (which is in order of smallest to largest
       digit). The return value is a string of elements from todigits
       (ordered in the same way). The input and output bases are
       determined from the lengths of the digit strings. Negative
       signs are passed through.
 
       This is modified source from http://pastebin.com/f54dd69d6#
 
       decimal to binary
       >>> baseconvert(555,BASE10,BASE2)
       '1000101011'
 
       binary to decimal
       >>> convert('1000101011',BASE2,BASE10)
       '555'
 
       """
 
        if str(number)[0]=='-':
            number = str(number)[1:]
            neg=1
        else:
            neg=0
 
        # make an integer out of the number
        x=0
        for digit in str(number):
           x = x*len(fromdigits) + fromdigits.index(digit)
   
        # create the result in base 'len(todigits)'
        if x == 0:
            res = todigits[0]
        else:
            res=""
            while x>0:
                digit = x % len(todigits)
                res = todigits[digit] + res
                x = int(x / len(todigits))
            if neg:
                res = "-"+res
 
        return res