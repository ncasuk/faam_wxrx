'''
Created on 7 Nov 2011

@author: axel
'''

import bitstring
import os
import pprint
import sys

from faam_wxrx.Arinc708 import Arinc708
from faam_wxrx.Reader import Reader


def Validator( infile ):

    #infile = os.path.join( ROOT_PATH, fname )
    #val = Validator( infile )
    val.check_records( )
    val.close( )
    print( '\n' + 30 * '#' )
    print( infile )
    val.print_info()
    pprint.pprint( val.Errors )

    gix, bix = [], []
    valid, not_valid = 0, 0
    not_valid = 0
    for i in range( len( val.Records )):
        ar = Arinc708()
        try:
            tmp = ar.parse( val.Records[i][1] )
            gix.append( i )
            valid += 1
        except:
            not_valid += 1
            bix.append( i )
    print( 'valid:' + str( valid) )
    print( 'not_valid:' + str( not_valid ))
    print( 30 * '#' + '\n' )


wxrx_file = '/home/axel/wxrx_tmp/B655/COP13B.tmp'

Validator(wxrx_file)
