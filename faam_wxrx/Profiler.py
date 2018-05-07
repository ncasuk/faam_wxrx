'''
Created on 3 Jan 2012

@author: axel
'''

import hotshot, hotshot.stats

def Profiler(limited=True):
    """Takes about 125 sec with the limited option."""
    
    prof = hotshot.Profile('arinc708.prof')
    prof.start()
    #execfile('/home/axel/workspace/FAAMy/wxrx/main.py')
    execfile('/home/axel/workspace/FAAMy/wxrx/processing.py')
    prof.close()
    stats = hotshot.stats.load('arinc708.prof')
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(40)
Profiler()

