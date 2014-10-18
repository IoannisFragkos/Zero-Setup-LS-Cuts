#-------------------------------------------------------------------------------
# Name:        const.py
# Purpose:
#
# Author:      ifragkos
#
# Created:     17/10/2014
# Copyright:   (c) ifragkos 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

class _const:
    class ConstError(TypeError): pass
    def __setattr__(self,name,value):
        if self.__dict__.has_key(name):
            raise self.ConstError, "Can't rebind const(%s)"%name
        self.__dict__[name]=value
import sys
sys.modules[__name__]=_const()