# This code is part of Amoco
# Copyright (C) 2006-2011 Axel Tillequin (bdcht3@gmail.com) 
# published under GPLv2 license

from amoco.logger import Log
logger = Log(__name__)

from .expressions import reg,cst,mem,comp,top
from amoco.cas.tracker import generation

class mapper(object):

    __slots__ = ['__map']

    # a mapper is inited with a list of instructions 
    # provided by a disassembler (see x86)
    def __init__(self,instrlist=None):
        self.__map  = generation()
        icache = []
        # if the __map needs to be inited before executing instructions
        # one solution is to prepend the instrlist with a function dedicated
        # to this init phase...
        for instr in instrlist or []:
            # call the instruction with this mapper:
            if not instr.misc['delayed']: instr(self)
            else: icache.append(instr)
        for instr in icache:
            instr(self)

    def __str__(self):
        return '\n'.join(["%s <- %s"%x for x in self])

    # list antecedent locations (used in the mapping)
    def inputs(self):
        pass

    # list image locations (modified in the mapping)
    def outputs(self):
        pass

    def clear(self):
        self.__map.clear()

    # compare self with mapper m:
    def __cmp__(self,m):
        d = cmp(self.__map.lastdict(),m.__map.lastdict())
        return d
        #if d<>0: return d
        #shall we compare also the order ?
        #return cmp(self.__order,m.__order)

    # iterate over ordered correspondances:
    def __iter__(self):
        for (loc,v) in self.__map.iteritems():
            yield (loc,v)

    # get a (plain) register value:
    def R(self,x):
        return self.__map.get(x,x)

    # get a memory location value (fetch) :
    def M(self,k):
        if k.a.base._is_ext: return k.a.base
        x = self.__map.get(k.a,k)
        if x.size<k.size:
            logger.warning('read memory out of bound')
            c = comp(k.size)
            c[0:x.size] = x
            c[x.size:k.size] = top(k.size-x.size)
            x = c
        return x[0:k.size]

    # just a convenient wrapper around M/R:
    def __getitem__(self,k):
        r = self.M(k) if k._is_mem else self.R(k)
        if k.size!=r.size: raise ValueError('size mismatch')
        return r[0:k.size]

    # define image v of antecedent k:
    def __setitem__(self,k,v):
        if k._is_ptr:
            self.__map[k] = v
            return
        if k.size<>v.size: raise ValueError('size mismatch')
        try:
            loc = k.addr(self)
        except TypeError:
            logger.error('setitem ignored (invalid left-value expression)')
            return
        if k._is_slc and not loc._is_reg:
            raise ValueError('memory location slc is not supported')
        elif k._is_mem:
            r = v
        else:
            r = self.R(loc)
            if r._is_reg:
                r = comp(loc.size)
                r[0:loc.size] = loc
            pos = k.pos if k._is_slc else 0
            r[pos:pos+k.size] = v
        self.__map[loc] = r

    def update(self,instr):
        instr(self)

    # eval of x in this map:
    # note the difference between a mapper[mem(x)] and mapper(mem(x)):
    # in the call form, x is first evaluated so that it uses "x_out"
    # whereas the item form uses "x_in".
    def __call__(self,x):
        return x.eval(self)

    def restruct(self):
        pass

    # return a new mapper instance where all input locations have
    # been replaced by there corresponding values in m.
    # example:
    # in self: eax <- ebx
    # in m   : ebx <- 4
    # =>
    # in mm  : eax <- 4
    def eval(self,m,compose=False):
        mm = mapper() if not compose else m.use()
        for loc,v in self:
            if loc._is_ptr:
                loc = m(loc)
            mm[loc] = m(v)
        return mm

    # composition operator (°) returns a new mapper
    # corresponding to function x -> self(m(x))
    def rcompose(self,m):
        return self.eval(m,compose=True)

    # self << m : composition (self°m)
    def __lshift__(self,m):
        return self.rcompose(m)

    # self >> m : composition (m°self)
    def __rshift__(self,m):
        return m.rcompose(self)

    def interact(self):
            pass

    def use(self,**kargs):
        m = mapper()
        for k,v in kargs.iteritems():
            m[reg(k)] = cst(v)
        return self.eval(m)
