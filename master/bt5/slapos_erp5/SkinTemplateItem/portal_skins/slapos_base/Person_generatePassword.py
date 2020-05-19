"""
  This script generates a human readable random
  password in the form 'word'+digits+'word'.
  
  from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410076

  parameters: number of 'characters' , number of 'digits'
  Pradeep Kishore Gowda <pradeep at btbytes.com >
  License : GPL 
  Date : 2005.April.15
  Revision 1.2 
  ChangeLog: 
  1.1 - fixed typos 
  1.2 - renamed functions _apart & _npart to a_part & n_part as zope does not allow functions to 
  start with _
"""

import string, random
vowel_list = ['a','e','i','o','u']
consonant_list = [a for a in string.ascii_lowercase if a not in vowel_list]
digit_list = string.digits
symbol_list = ["$", "-", "_", "&"]


def a_part(slen):
  ret = ''
  for i in range(slen):
    if i%2 ==0:
      randid = random.randint(0,20) #number of consonants
      ret += consonant_list[randid]
    else:
      randid = random.randint(0,4) #number of vowels
      ret += vowel_list[randid]
  return ret

def n_part(slen):
  ret = ''
  for _ in range(slen):
    randid = random.randint(0,9) #number of digits
    ret += digit_list[randid]
  return ret

def s_part(slen):
  ret = ''
  for _ in range(slen):
    randid = random.randint(0,3) #number of digits
    ret += symbol_list[randid]
  return ret

fpl = alpha/2		
if alpha % 2 :
  fpl = int(alpha/2) + 1
lpl = alpha - fpl

begin = string.upper(a_part(fpl))
mid = n_part(numeric)
third = a_part(lpl)
end = s_part(symbol)

newpass = "%s%s%s%s" % (begin, mid, third, end)
return newpass
