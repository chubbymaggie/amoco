# -*- coding: utf-8 -*-

# This code is part of Amoco
# Copyright (C) 2012 Axel Tillequin (bdcht3@gmail.com)
# published under GPLv2 license

from collections import OrderedDict

class generation(OrderedDict):

    def __getall(self,k):
        return OrderedDict.get(self,k,[])

    def __setitem__(self,k,v):
        oldv = self.__getall(k)
        if k in self:
            del self[k]
        oldv.append(v)
        OrderedDict.__setitem__(self,k,oldv)

    def __getitem__(self,k):
        v = self.__getall(k)
        try:
            return v[-1]
        except IndexError:
            return None

    def get(self,k,default):
        r = self[k]
        if r is None: r=default
        return r

    def keygen(self,k,g):
        v = self.__getall(k)
        if g<0:
            r=0
        else:
            r=min(g,len(v)-1)
        return v[r]

    # order at generation g is conserved;
    def getgen(self,g):
        d = OrderedDict()
        for k in self.iterkeys():
            d[k] = self.keygen(k,g)
        return d

    def lastdict(self):
        d = dict()
        for k in self:
            d[k] = self[k]
        return d
