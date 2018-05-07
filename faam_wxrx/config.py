'''
Created on 1 Feb 2012

@author: axel
'''

import os

_WXRX_ROOT_PATH = '/home/data/faam/wxrx'
_BADCMIRROR_ROOT_PATH = '/home/data/faam/badc'
_REV = 0


def get_core_file(fid):
    for root, subFolders, files in os.walk(FAAMy.ROOT_DATA_PATH):
        for file in files:
            if file.endswith('_'+fid+'.nc'):
                return os.path.join(root, file)
                break
    return


def setup(fid):
    FID = fid
    REV = _REV
    ROOT_PATH = os.path.join(_WXRX_ROOT_PATH, fid+'_wxrx')
    #CORE_FILE = dic[fid]['CORE_FILE']
    CORE_FILE = get_core_file(fid)
    return(FID, REV, ROOT_PATH, CORE_FILE)

