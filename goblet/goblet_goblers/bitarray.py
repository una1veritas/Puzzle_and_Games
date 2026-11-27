'''
Created on 2026/01/28

@author: sin
'''
import operator

class bitarray:
    BITWIDTH = 6
    BITMASK = (1 << BITWIDTH) - 1
    
    @staticmethod
    def set_bitwidth(width = 6):
        bitarray.BITWIDTH = width
        bitarray.BITMASK = (1 << bitarray.BITWIDTH) - 1
    
    ''' popcnt '''
    @staticmethod
    def bit1count(intval): 
        BITS_COUNT_TABLE = [ 0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, ]
        cnt = 0
        while intval > 0 :
            cnt += BITS_COUNT_TABLE[intval & 0x0f]
            intval >> 4
            cnt += BITS_COUNT_TABLE[intval & 0x0f]
            intval >> 4
        return cnt
    
    def __init__(self, initval = 0):
        if isinstance(initval, bitarray) :
            self.bits = initval.bits
        elif isinstance(initval, int) :
            self.bits = initval
        else:
            raise NotImplementedError('{initval} is invalid as initializer.')
    
    def __int__(self):
        return self.bits
    
    def __len__(self):
        val = self.bits
        counter = 0
        while val > 0 :
            val >>= self.BITWIDTH
            counter += 1
        return counter
    
    def __getitem__(self, index):
        if not isinstance(index, slice):
            ix = operator.index(index)  # accepts int-like objects
            return self.BITMASK & (self.bits >> (bitarray.BITWIDTH * ix))
        
        raise NotImplementedError('get item with slice is not implemented')
        # slice index -> return same type (copy) for safety
        # slice.indices normalizes start/stop/step and handles negatives/out-of-range
        start, stop, step = index.indices(len(self))
        
        newbits = 0
        for ix in range(start, stop, step) :
            val = self.BITMASK & (self.bits >> (bitarray.BITWIDTH * ix))
            newbits |= (val << (bitarray.BITWIDTH * ix))
        return bitarray(bitarray.BITWIDTH, newbits)
    
    def set(self, ix, val):
        val &= bitarray.BITMASK
        self.bits &= ~(self.BITMASK << (bitarray.BITWIDTH * ix))
        self.bits |= (val << (bitarray.BITWIDTH * ix))
        
    def __setitem__(self, index, value):
        # validate values before storing
        if not isinstance(index, slice):
            ix = operator.index(index)
            self.set(ix, value)
            return
        
        raise NotImplementedError('set item with slice is not implemented')
        # slice assignment
        start, stop, step = index.indices(len(self))
        indices = list(range(start, stop, step))
        vals = list(value)  # materialize the RHS
        if len(vals) != len(indices):
            raise ValueError(
                f"attempt to assign sequence of size {len(vals)} "
                f"to extended slice of size {len(indices)}"
            )
        for i, v in zip(indices, vals):
            self.set(i, v)
        return
    
    def __repr__(self):
        return 'bitarray(' + str(self)
    
    def __bin__(self):
        return bin(self.bits)
    
    def __str__(self):
        return str(tuple([self[i] for i in range(len(self))]))

    def rotright(self, start, stop, moves):
        part = [self[i] for i in range(start, stop)]
        #print(start, stop, moves,part)
        for ix in range(start, stop) :
            self[ix] = part[(ix + moves) % len(part)]
            #print(self, ix,  (ix + moves) % len(part))
        return
    
    def reverse(self, start, stop):
        part = [self[i] for i in range(start, stop)]
        #print(start, stop, moves,part)
        for ix in range(len(part)) :
            #print(ix, len(part) - 1  - ix, start + len(part) - 1  - ix, )
            self[start + ix] = part[len(part) - 1 - ix]
            #print(self, ix,  (ix + moves) % len(part))
        return
        
    def hex(self):
        return hex(self.bits)
    
    def bin(self):
        return bin(self.bits)
        

        