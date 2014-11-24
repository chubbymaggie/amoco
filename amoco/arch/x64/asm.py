#!/usr/bin/env python

# This code is part of Amoco
# Copyright (C) 2006-2011 Axel Tillequin (bdcht3@gmail.com) 
# published under GPLv2 license

from .env import *
from amoco.cas.utils import *

from amoco.logger import Log
logger = Log(__name__)

#------------------------------------------------------------------------------
# utils :
def push(fmap,x):
  fmap[rsp] = fmap[rsp]-x.length
  fmap[mem(rsp,x.size)] = x

def pop(fmap,l):
  fmap[l] = fmap(mem(rsp,l.size))
  fmap[rsp] = fmap[rsp]+l.length

#------------------------------------------------------------------------------
def i_BSWAP(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  dst = i.operands[0]
  _t = fmap(dst)
  if i.misc['REX'] and i.misc['REX'][0]==1:
      fmap[dst[0 : 8]] = _t[56:64]
      fmap[dst[8 :16]] = _t[48:56]
      fmap[dst[16:24]] = _t[40:48]
      fmap[dst[24:32]] = _t[32:40]
      fmap[dst[32:40]] = _t[24:32]
      fmap[dst[40:48]] = _t[16:24]
      fmap[dst[48:56]] = _t[8 :16]
      fmap[dst[56:64]] = _t[0 : 8]
  else:
      fmap[dst[0 : 8]] = _t[24:32]
      fmap[dst[8 :16]] = _t[16:24]
      fmap[dst[16:24]] = _t[8 :16]
      fmap[dst[24:32]] = _t[0 : 8]

def i_NOP(i,fmap):
  fmap[rip] = fmap[rip]+i.length

def i_WAIT(i,fmap):
  fmap[rip] = fmap[rip]+i.length

# LEAVE instruction is a shortcut for 'mov rsp,ebp ; pop ebp ;'
def i_LEAVE(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[rsp] = fmap[rbp]
  pop(fmap,rbp)

def i_RET(i,fmap):
  pop(fmap,rip)

def i_HLT(i,fmap):
  ext('halt').call(fmap)

#------------------------------------------------------------------------------
def _ins_(i,fmap,l):
  counter = cx if i.misc['adrsz'] else rcx
  loc = mem(fmap(rdi),l*8)
  src = ext('IN%s'%fmap(dx),l*8).call(fmap)
  if i.misc['rep']:
      fmap[loc] = tst(fmap(counter)==0, fmap(loc), src)
      fmap[counter] = fmap(counter)-1
      fmap[rip] = tst(fmap(counter)==0, fmap[rip]+i.length, fmap[rip])
  else:
      fmap[loc] = src
      fmap[rip] = fmap[rip]+i.length
  fmap[rdi] = tst(fmap(df),fmap(rdi)-l,fmap(rdi)+l)

def i_INSB(i,fmap):
  _ins_(i,fmap,1)
def i_INSW(i,fmap):
  _ins_(i,fmap,2)
def i_INSD(i,fmap):
  _ins_(i,fmap,4)

#------------------------------------------------------------------------------
def _outs_(i,fmap,l):
  counter = cx if i.misc['adrsz'] else rcx
  src = fmap(mem(rsi,l*8))
  loc = ext('OUT%s'%fmap(dx),l*8).call(fmap)
  if i.misc['rep']:
      fmap[loc] = tst(fmap(counter)==0, fmap(loc), src)
      fmap[counter] = fmap(counter)-1
      fmap[rip] = tst(fmap(counter)==0, fmap[rip]+i.length, fmap[rip])
  else:
      fmap[loc] = src
      fmap[rip] = fmap[rip]+i.length
  fmap[rdi] = tst(fmap(df),fmap(rdi)-l,fmap(rdi)+l)

def i_OUTSB(i,fmap):
  _outs_(i,fmap,1)
def i_OUTSW(i,fmap):
  _outs_(i,fmap,2)
def i_OUTSD(i,fmap):
  _outs_(i,fmap,4)

#------------------------------------------------------------------------------
def i_INT3(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  ext('INT3').call(fmap)

def i_CLC(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[cf] = bit0

def i_STC(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[cf] = bit1

def i_CLD(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[df] = bit0

def i_STD(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[df] = bit1

def i_CMC(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[cf] = ~fmap(cf)

def i_CBW(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[ax] = fmap(al).signextend(16)

def i_CWDE(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[eax] = fmap(ax).signextend(32)

def i_CDQE(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  fmap[rax] = fmap(eax).signextend(64)

def i_CWD(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  x = fmap(ax).signextend(32)
  fmap[dx] = x[16:32]
  fmap[ax] = x[0:16]

def i_CDQ(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  x = fmap(eax).signextend(64)
  fmap[edx] = x[32:64]
  fmap[eax] = x[0:32]

def i_CQO(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  x = fmap(eax).signextend(128)
  fmap[rdx] = x[64:128]
  fmap[rax] = x[0:64]

def i_PUSHFQ(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  push(fmap,fmap(rflags)&0x0000000000fcffffL)

def i_POPFQ(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  pop(fmap,rflags)

#------------------------------------------------------------------------------
def _scas_(i,fmap):
  counter,d = ecx,edi if i.misc['adrsz'] else rcx,rdi
  a = {1:al, 2:ax, 4:eax, 8:rax}[l]
  src = mem(fmap(d),l*8)
  x, carry, overflow = SubWithBorrow(a,src)
  if i.misc['rep']:
      fmap[zf] = tst(fmap(counter)==0, fmap(zf), x==0)
      fmap[sf] = tst(fmap(counter)==0, fmap(sf), x<0)
      fmap[cf] = tst(fmap(counter)==0, fmap(cf), carry)
      fmap[of] = tst(fmap(counter)==0, fmap(of), overflow)
      fmap[counter] = fmap(counter)-1
      fmap[rip] = tst(fmap(counter)==0, fmap[rip]+i.length, fmap[rip])
  else:
      fmap[zf] = x==0
      fmap[sf] = x<0
      fmap[cf] = carry
      fmap[of] = overflow
      fmap[rip] = fmap[rip]+i.length
  fmap[d] = tst(fmap(df),fmap(d)-l,fmap(d)+l)

def i_SCASB(i,fmap):
  _scas_(i,fmap,1)
def i_SCASW(i,fmap):
  _scas_(i,fmap,2)
def i_SCASD(i,fmap):
  _scas_(i,fmap,4)
def i_SCASQ(i,fmap):
  _scas_(i,fmap,8)

#------------------------------------------------------------------------------
def _lods_(i,fmap,l):
  counter,s = (ecx,esi) if i.misc['adrsz'] else (rcx,rsi)
  loc = {1:al, 2:ax, 4:eax, 8:rax}[l]
  src = mem(fmap(s),l*8)
  if i.misc['rep']:
      fmap[loc] = tst(fmap(counter)==0, fmap(loc), src)
      fmap[counter] = fmap(counter)-1
      fmap[rip] = tst(fmap(counter)==0, fmap[rip]+i.length, fmap[rip])
  else:
      fmap[loc] = src
      fmap[rip] = fmap[rip]+i.length
  fmap[s] = tst(fmap(df),fmap(s)-l,fmap(s)+l)

def i_LODSB(i,fmap):
  _lods_(i,fmap,1)
def i_LODSW(i,fmap):
  _lods_(i,fmap,2)
def i_LODSD(i,fmap):
  _lods_(i,fmap,4)
def i_LODSQ(i,fmap):
  _lods_(i,fmap,8)

#------------------------------------------------------------------------------
def _stos_(i,fmap,l):
  if i.misc['adrsz']==32:
      counter,d = ecx,edi
  else:
      counter,d = rcx,rdi
  src = {1:al, 2:ax, 4:eax, 8:rax}[l]
  loc = mem(fmap(d),l*8)
  if i.misc['rep']:
      fmap[loc] = tst(fmap(counter)==0, fmap(loc), src)
      fmap[counter] = fmap(counter)-1
      fmap[rip] = tst(fmap(counter)==0, fmap[rip]+i.length, fmap[rip])
  else:
      fmap[loc] = src
      fmap[rip] = fmap[rip]+i.length
  fmap[d] = tst(fmap(df),fmap(d)-l,fmap(d)+l)

def i_STOSB(i,fmap):
  _stos_(i,fmap,1)
def i_STOSW(i,fmap):
  _stos_(i,fmap,2)
def i_STOSD(i,fmap):
  _stos_(i,fmap,4)
def i_STOSQ(i,fmap):
  _stos_(i,fmap,8)

#------------------------------------------------------------------------------
def _movs_(i,fmap,l):
  if i.misc['adrsz']==32:
      counter,d,s = ecx,edi,esi
  else:
      counter,d,s = rcx,rdi,rsi
  loc = mem(fmap(d),l*8)
  src = mem(fmap(s),l*8)
  if i.misc['rep']:
      fmap[loc] = tst(fmap(counter)==0, fmap(loc), src)
      fmap[counter] = fmap(counter)-1
      fmap[rip] = tst(fmap(counter)==0, fmap[rip]+i.length, fmap[rip])
  else:
      fmap[loc] = src
      fmap[rip] = fmap[rip]+i.length
  fmap[s] = tst(fmap(df),fmap(s)-l,fmap(s)+l)
  fmap[d] = tst(fmap(df),fmap(d)-l,fmap(d)+l)

def i_MOVSB(i,fmap):
  _movs_(i,fmap,1)
def i_MOVSW(i,fmap):
  _movs_(i,fmap,2)
def i_MOVSD(i,fmap):
  _movs_(i,fmap,4)
def i_MOVSQ(i,fmap):
  _movs_(i,fmap,8)

#------------------------------------------------------------------------------
def i_IN(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap[i.operands[0]]
  op2 = fmap[i.operands[1]]
  fmap[op1] = ext('IN%s'%op2).call(fmap)

def i_OUT(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap[i.operands[0]]
  op2 = fmap[i.operands[1]]
  fmap[op1] = ext('OUT%s'%op2).call(fmap)

#op1_src retreives fmap[op1] (op1 value): 
def i_PUSH(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap(i.operands[0])
  if op1.size==8: op1 = op1.signextend(64)
  push(fmap,op1)

#op1_dst retreives op1 location: 
def i_POP(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = i.operands[0]
  pop(fmap,op1)

def i_CALL(i,fmap):
  pc = fmap[rip]+i.length
  push(fmap,pc)
  op1 = fmap(i.operands[0])
  op1 = op1.signextend(pc.size)
  target = pc+op1 if not i.misc['absolute'] else op1
  if target._is_ext: target.call(fmap)
  else: fmap[rip] = target


def i_CALLF(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  pc = fmap[rip]+i.length

def i_JMP(i,fmap):
  pc = fmap[rip]+i.length
  op1 = fmap(i.operands[0])
  op1 = op1.signextend(pc.size)
  target = pc+op1 if not i.misc['absolute'] else op1
  if target._is_ext: target.call(fmap)
  else: fmap[rip] = target

def i_JMPF(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  pc = fmap[rip]+i.length

#------------------------------------------------------------------------------
def _loop_(i,fmap,cond):
  opdsz = 16 if i.misc['opdsz'] else 64
  src = i.operands[0].signextend(64)
  loc = fmap[rip]+src
  loc = loc[0:opdsz].zeroextend(64)
  counter = cx if i.misc['adrsz'] else ecx
  fmap[counter] = fmap(counter)-1
  fmap[rip] = tst(fmap(cond), loc, fmap[rip]+i.length)

def i_LOOP(i,fmap):
  cond = (counter!=0)
  _loop_(i,fmap,cond)

def i_LOOPE(i,fmap):
  cond = zf&(counter!=0)
  _loop_(i,fmap,cond)

def i_LOOPNE(i,fmap):
  cond = (~zf)&(counter!=0)
  _loop_(i,fmap,cond)

#------------------------------------------------------------------------------
def i_LSL(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length

def i_LTR(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length

#######################

def i_Jcc(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap(i.operands[0])
  op1 = op1.signextend(rip.size)
  fmap[rip] = tst(i.cond[1],fmap[rip]+op1,fmap[rip])

def i_RETN(i,fmap):
  src = i.operands[0].v
  pop(fmap,rip)
  fmap[rsp] = fmap(rsp)+src

def i_INT(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap(i.operands[0])
  push(fmap,fmap[rip])
  ext('INT%s'%op1).call(fmap)

def i_INC(i,fmap):
  op1 = i.operands[0]
  fmap[rip] = fmap[rip]+i.length
  a = fmap(op1)
  b = cst(1,a.size)
  x,carry,overflow = AddWithCarry(a,b)
  #cf not affected
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[of] = overflow
  fmap[op1] = x

def i_DEC(i,fmap):
  op1 = i.operands[0]
  fmap[rip] = fmap[rip]+i.length
  a = fmap(op1)
  b = cst(1,a.size)
  x,carry,overflow = SubWithBorrow(a,b)
  #cf not affected
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[of] = overflow
  fmap[op1] = x

def i_NEG(i,fmap):
  op1 = i.operands[0]
  fmap[rip] = fmap[rip]+i.length
  a = cst(0,op1.size)
  b = fmap(op1)
  x,carry,overflow = SubWithBorrow(a,b)
  fmap[cf] = b!=0
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[of] = overflow
  fmap[op1] = x

def i_NOT(i,fmap):
  op1 = i.operands[0]
  fmap[rip] = fmap[rip]+i.length
  fmap[op1] = ~fmap(op1)

def i_SETcc(i,fmap):
  op1 = fmap(i.operands[0])
  fmap[rip] = fmap[rip]+i.length
  fmap[op1] = tst(fmap(i.cond[1]),cst(1,op1.size),cst(0,op1.size))

def i_MOV(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  fmap[op1] = op2

def i_MOVBE(i,fmap):
  dst = i.operands[0]
  _t = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  if i.misc['opdsz']==16:
    fmap[dst[0 : 8]] = _t[8 :16]
    fmap[dst[8 :16]] = _t[0 : 8]
  else:
    fmap[dst[0 : 8]] = _t[56:64]
    fmap[dst[8 :16]] = _t[48:56]
    fmap[dst[16:24]] = _t[40:48]
    fmap[dst[24:32]] = _t[32:40]
    fmap[dst[32:40]] = _t[24:32]
    fmap[dst[40:48]] = _t[16:24]
    fmap[dst[48:56]] = _t[8 :16]
    fmap[dst[56:64]] = _t[0 : 8]

def i_MOVSX(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  fmap[op1] = op2.signextend(op1.size)

def i_MOVSXD(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  fmap[op1] = op2.signextend(op1.size)

def i_MOVZX(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  fmap[op1] = op2.zeroextend(op1.size)

def i_ADC(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a=fmap(op1)
  x,carry,overflow = AddWithCarry(a,op2,fmap(cf))
  fmap[zf]  = x==0
  fmap[sf]  = x<0
  fmap[cf]  = carry
  fmap[of]  = overflow
  fmap[op1] = x

def i_ADD(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a=fmap(op1)
  x,carry,overflow = AddWithCarry(a,op2)
  fmap[zf]  = x==0
  fmap[sf]  = x<0
  fmap[cf]  = carry
  fmap[of]  = overflow
  fmap[op1] = x

def i_SBB(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a=fmap(op1)
  x,carry,overflow = SubWithBorrow(a,op2,fmap(cf))
  fmap[zf]  = x==0
  fmap[sf]  = x<0
  fmap[cf]  = carry
  fmap[of]  = overflow
  fmap[op1] = x

def i_SUB(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a=fmap(op1)
  x,carry,overflow = SubWithBorrow(a,op2)
  fmap[zf]  = x==0
  fmap[sf]  = x<0
  fmap[cf]  = carry
  fmap[of]  = overflow
  fmap[op1] = x

def i_AND(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  if op2.size<op1.size:
    op2 = op2.signextend(op1.size)
  x=fmap(op1)&op2
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[cf] = bit0
  fmap[of] = bit0
  fmap[op1] = x

def i_OR(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  x=fmap(op1)|op2
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[cf] = bit0
  fmap[of] = bit0
  fmap[op1] = x

def i_XOR(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  x=fmap(op1)^op2
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[cf] = bit0
  fmap[of] = bit0
  fmap[op1] = x

def i_CMP(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap(i.operands[0])
  op2 = fmap(i.operands[1])
  x, carry, overflow = SubWithBorrow(op1,op2)
  fmap[zf] = x==0
  fmap[sf] = x<0
  fmap[cf] = carry
  fmap[of] = overflow

def i_TEST(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = fmap(i.operands[0])
  op2 = fmap(i.operands[1])
  x = op1&op2
  fmap[zf] = x==0
  fmap[sf] = x[x.size-1:x.size]
  fmap[cf] = bit0
  fmap[of] = bit0

def i_LEA(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  adr = op2.addr(fmap)
  if   op1.size>adr.size: adr = adr.zeroextend(op1.size)
  elif op1.size<adr.size: adr = adr[0:op1.size]
  fmap[op1] = adr

def i_XCHG(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  op1 = i.operands[0]
  op2 = i.operands[1]
  tmp = fmap(op1)
  fmap[op1] = fmap(op2)
  fmap[op2] = tmp

def i_SHR(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a = fmap(op1)
  if op2._is_cst:
    if op2.value==0: return
    if (a.size>op2.value):
      fmap[cf] = slc(a,op2.value-1,1)
    else:
      fmap[cf] = bit0
  else:
    fmap[cf] = top(1)
  #shr must ignore sign:
  a.sf = +1
  fmap[op1] = a>>op2
  #of is always MSB of a:
  fmap[of] = slc(a,a.size-1,1)

def i_SAR(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a = fmap(op1)
  if op2._is_cst:
    if op2.value==0: return
    if (a.size>op2.value):
      fmap[cf] = slc(a,op2.value-1,1)
      #of is cleared if 1 was shifted, undefined otherwise (see intel 4-278). 
      fmap[of] = tst(a[0:op2.value]<>0,bit0,top(1))
    else:
      fmap[cf] = slc(a,a.size-1,1)
      fmap[of] = tst(a<>0,bit0,top(1))
  else:
    fmap[cf] = top(1)
    fmap[of] = top(1)
  #sign of a is important because the result is filled with MSB(a)
  fmap[op1] = a>>op2

def i_SHL(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a = fmap(op1)
  if op2._is_cst:
    if op2.value==0: return
    if (a.size>op2.value):
      fmap[cf] = slc(a,a.size-op2.value,1)
    else:
      fmap[cf] = bit0
  else:
    fmap[cf] = top(1)
  x = a<<op2
  fmap[op1] = x
  #of is cleared if MSB(x)==cf, set otherwise.
  fmap[of] = tst(slc(x,x.size-1,1)==fmap[cf],bit0,bit1)

i_SAL = i_SHL

def i_ROL(i,fmap):
  raise NotImplementedError

def i_ROR(i,fmap):
  raise NotImplementedError

def i_RCL(i,fmap):
  raise NotImplementedError

def i_RCR(i,fmap):
  raise NotImplementedError

def i_CMOVcc(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  fmap[rip] = fmap[rip]+i.length
  a = fmap(op1)
  fmap[op1] = tst(fmap(i.cond[1]),op2,a)

def i_SHRD(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  op3 = fmap(i.operands[2])
  fmap[rip] = fmap[rip]+i.length
  # op3 is a cst:
  n = op3.value
  r = op1.size-n
  fmap[op1] = (fmap(op1)>>n) | (op2<<r)

def i_SHLD(i,fmap):
  op1 = i.operands[0]
  op2 = fmap(i.operands[1])
  op3 = fmap(i.operands[2])
  fmap[rip] = fmap[rip]+i.length
  n = op3.value
  r = op1.size-n
  fmap[op1] = (fmap(op1)<<n) | (op2>>r)

def i_IMUL(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  if len(i.operands)==1:
    src = fmap(i.operands[0])
    m,d = {8:(al,ah), 16:(ax,dx), 32:(eax,edx)}[src.size]
    r = m**src
  elif len(i.operands)==2:
    dst,src = i.operands
    m = d = dst
    r = dst**src
  else:
    dst,src,imm = i.operands
    m = d = dst
    r = src**imm.signextend(src.size)
  lo = r[0:src.size]
  hi = r[src.size:r.size]
  fmap[d]  = hi
  fmap[m]  = lo
  fmap[cf] = hi!=(lo>>31)
  fmap[of] = hi!=(lo>>31)

def i_MUL(i,fmap):
  fmap[rip] = fmap[rip]+i.length
  src = fmap(i.operands[0])
  m,d = {8:(al,ah), 16:(ax,dx), 32:(eax,edx)}[src.size]
  r = m**src
  lo = r[0:src.size]
  hi = r[src.size:r.size]
  fmap[d]  = hi
  fmap[m]  = lo
  fmap[cf] = hi!=0
  fmap[of] = hi!=0

def i_RDRAND(i,fmap):
   fmap[rip] = fmap[rip]+i.length
   dst = i.operands[0]
   fmap[dst] = top(dst.size)
   fmap[cf] = top(1)
   for f in (of,sf,zf,af,pf): fmap[f] = bit0

def i_RDTSC(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length
   fmap[rdx] = top(64)
   fmap[rax] = top(64)

def i_RDTSCP(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length
   fmap[rdx] = top(64)
   fmap[rax] = top(64)
   fmap[rcx] = top(64)

def i_BOUND(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length
   # #UD #BR exceptions not implemented

def i_LFENCE(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_MFENCE(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_SFENCE(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_MWAIT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_LGDT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_SGDT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_LIDT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_SIDT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_LLDT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_SLDT(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length

def i_LMSW(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length
   fmap[cr(0)[0:16]] = top(16)

def i_SMSW(i,fmap):
   logger.warning('%s semantic is not defined'%i.mnemonic)
   fmap[rip] = fmap[rip]+i.length
   dst = i.operands[0]
   fmap[dst] = top(16)

def i_BSF(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  x = fmap(src)
  fmap[zf] = x==0
  fmap[dst] = top(dst.size)

def i_BSR(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  x = fmap(src)
  fmap[zf] = x==0
  fmap[dst] = top(dst.size)

def i_POPCNT(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  dst,src = i.operands
  fmap[dst] = top(dst.size)
  fmap[cf] = bit0
  fmap[of] = bit0
  fmap[sf] = bit0
  fmap[af] = bit0
  fmap[zf] = fmap(src)==0
  fmap[rip] = fmap[rip]+i.length

def i_LZCNT(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  dst,src = i.operands
  fmap[dst] = top(dst.size)
  fmap[cf] = fmap[zf] = top(1)
  fmap[rip] = fmap[rip]+i.length

def i_TZCNT(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  dst,src = i.operands
  fmap[dst] = top(dst.size)
  fmap[cf] = fmap[zf] = top(1)
  fmap[rip] = fmap[rip]+i.length

def i_BT(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  fmap[cf] = top(1)

def i_BTC(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  fmap[cf] = top(1)
  fmap[dst] = top(dst.size)

def i_BTR(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  fmap[cf] = top(1)
  fmap[dst] = top(dst.size)

def i_BTS(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  fmap[cf] = top(1)
  fmap[dst] = top(dst.size)

def i_CLFLUSH(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # cache not supported

def i_INVD(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # cache not supported

def i_INVLPG(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # cache not supported

def i_CLI(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # interruptions not supported

def i_PREFETCHT0(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # interruptions not supported
def i_PREFETCHT1(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # interruptions not supported
def i_PREFETCHT2(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # interruptions not supported
def i_PREFETCHNTA(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # interruptions not supported
def i_PREFETCHW(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  # interruptions not supported

def i_LAR(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst,src = i.operands
  fmap[zf] = top(1)
  fmap[dst] = top(dst.size)

def i_STR(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length
  dst = i.operands[0]
  fmap[dst] = top(dst.size)

def i_RDMSR(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length

def i_RDPMC(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length

def i_RSM(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = fmap[rip]+i.length

def i_SYSENTER(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = top(32)
  fmap[rsp] = top(32)
  fmap[cs]  = top(16)
  fmap[ss]  = top(16)

def i_SYSEXIT(i,fmap):
  logger.warning('%s semantic is not defined'%i.mnemonic)
  fmap[rip] = top(32)
  fmap[rsp] = top(32)
  fmap[cs]  = top(16)
  fmap[ss]  = top(16)

