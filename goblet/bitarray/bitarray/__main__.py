'''
Created on 2026/01/24

@author: sin
'''

class bitarray:
    UWIDTH = 6
    UMASK = (1 << (UWIDTH - 1)) - 1
    
    def __init__(self):
        self.bits = 0
    
    def __len__(self):
        val = self.bits
        counter = 0
        while val > 0 :
            val >>= self.UWIDTH
            counter += 1
        return counter
    
    def __getitem__(self, index):
        # supports single index or slice automatically because self._data does
        return self.UMASK & (self.bits >> (self.UWIDTH * index))
    
    def set(self, ix, val):
        val &= self.UMASK
        self.bits &= ~(self.UMASK << (self.UWIDTH * ix))
        self.bits |= (val << (self.UWIDTH * ix))
        
    def __setitem__(self, index, value):
        # validate values before storing
        if isinstance(index, slice):
            # allow assigning an iterable of ints for slices
            if not all(isinstance(x, int) for x in value):
                raise ValueError("slice assignment requires integers")
            self.set(index, value)
        else:
            if not isinstance(value, int):
                raise ValueError("only integers allowed")
            self.set(index, value)
    
    def __int__(self):
        return self.bits
    
    def __repr__(self):
        return 'bitarray(' + str(self)
    
    def __bin__(self):
        return bin(self.bits)
    
    def __str__(self):
        return str(tuple([self[i] for i in range(len(self))]))
    def intvalue(self):
        return self.bits

    def hex(self):
        return hex(self.bits)
    
    def bin(self):
        return bin(self.bits)

if __name__ == '__main__':
    a = bitarray()
    a[3] = 6
    a[4] = 9
    a[4] = 0xc
    a[9] = 2
    a[5] = 45
    print(a[1])
    print(a[3])
    print(a.hex())
    for i in range(len(a)):
        print(a[i])
