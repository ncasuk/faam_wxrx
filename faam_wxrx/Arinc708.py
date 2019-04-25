"""
NAME
     Arinc708.py

DESCRIPTION
       Reads and translates a single Arinc708 bitstring from the FAAM weather
       radar. The original word block can not be used without processing, because
       the information is bit encoded.

       The Arinc708 protocol includes *no* time stamp.

REQUIREMENTS
        python-bitstring module - http://code.google.com/p/python-bitstring/

FURTHER INFO
        [1] http://en.wikipedia.org/wiki/Arinc_708
        [2] http://www.ballardtech.com/products.aspx/dir/protocol/ARINC_708/
        [3] http://www.faam.ac.uk/index.php/science-instruments/remote-sensing/288-doppler-radar

AUTHOR
       Written by Axel Wellpott (axll[at]faam[dot]ac[dot]uk)
"""

import numpy as np
import sys

try:
    import bitstring
except ImportError:
    message = """ The script needs the bitstring module
     http://code.google.com/p/python-bitstring/
"""
    sys.stdout.write(message)
    sys.exit(2)


_LABEL = '550'

_REC = np.zeros(1, dtype=[('label',             np.str_, 4),
                          ('control_accept',    np.byte),
                          ('slave',             np.byte),
                          ('mode_annunciation', np.byte),
                          ('faults',            np.byte),
                          ('stabilization',     np.byte),
                          ('operating_mode',    np.byte),
                          ('tilt',              np.float),
                          ('gain',              np.float),
                          ('range',             np.int16),
                          ('data_accept',       np.byte),
                          ('scan_angle',        np.float),
                          ('reflectivity',      np.byte, (512,))])

_REC.dtype.fields.keys()



class Arinc708(object):
    """Arinc708 class:

       The Arinc708 [1] word block is 1600 bits long consisting of a header (64 bits)
       and a data (1536 bits = 512 x 3 bits) section. The information is *bit*
       encoded and therefore the whole word block has to be parsed using the
       bitstring module.

       The computer reads the data in byte chunks and every binary representation of
       a  byte has to be reversed before the word block can be processed. This is done
       in the "__rearrange_bits__ " method.

       The original Arinc708 busword is not time stamped in any way. This is done
       post flight using the filesize-log, which monitors and logs the filesize of
       the weather radar data file in flight.

       [1] http://en.wikipedia.org/wiki/Arinc_708

       """

    # Define empty reflectivity as list of zeros
    __EMPTY_DATA = [0] * 512

    def __init__(self):
        pass

    def parse(self, busword):
        """Module parses one (1600 bit long) ARINC708 message."""
        # convert the bitstring to a binary string
        self.busword = busword.bin
        self.Record = _REC
        self.Record['label'] = str((busword[0:9]).oct)
        if not self.__isvalid__(busword):
            return None
        self.__rearrange_bits__(busword)
        self.Record['control_accept'] = self.__get_control_accept__()
        self.Record['slave'] = self.__get_slave__()
        self.Record['mode_annunciation'] = self.__get_mode_annunciation__()
        self.Record['faults'] = self.__get_faults__()
        self.Record['stabilization'] = self.__get_stabilization__()
        self.Record['operating_mode'] = self.__get_operating_mode__()
        self.Record['tilt'] = self.__get_tilt_data__()
        self.Record['gain'] = self.__get_gain_data__()
        self.Record['range'] = self.__get_range_data__()
        self.Record['data_accept'] = self.__get_data_accept__()
        self.Record['scan_angle'] = self.__get_scan_angle__()
        self.Record['reflectivity'] = self.__get_reflectivity__()
        return self.Record

    def __isvalid__(self, busword):
        """
        Check if the submitted bitstring is a valid ARINC708 busword.

        """
        if (len(busword) != 1600) or (str(self.Record['label'][0]) != _LABEL):
            return False
        else:
            return True

    def __rearrange_bits__(self, busword):
        """See page 2-12 in the manual."""
        wb_list = [self.busword[8*i:8*(i+1)][::-1] for i in range(200)]
        self.busword = ''.join(wb_list)

    def __get_slave__(self):
        return int(self.busword[11])

    def __get_stabilization__(self):
        """'Selected tilt angles are relative to Mother Earth. In aircrafts
        that do not have antenna stabilization, or when stab is turned off,
        tilt angles are relative to the longitudinal axis of the aircraft.
        However, all airliners, and virtually all corporate turbine aircraft,
        have stabilized antennas.'

        (source: http://www.pprune.org/archive/index.php/t-48016.html)

        """
        return int(self.busword[26])

    def __get_control_accept__(self):
        """0: Do not accept control
           1: IND 1 accept control
           2: IND 2 accept control
           3: All INDs accept control

           """
        return int(self.busword[8:10][::-1], 2)

    def __get_mode_annunciation__(self):
        keys = ('Antenna stability limits',
                'Sector scan',
                'Anti clutter',
                'Weather alert',
                'Turbulence alert')
        # TODO: at the moment we only return the key, but not the name
        result = int(self.busword[13:18][::-1])
        return result

    def __get_faults__(self):
        keys = ('Cooling fault',
                'Display fault',
                'Calibration fault [T-R]',
                'Altitude input fault',
                'Control fault',
                'Antenna fault',
                'Transmitter/receiver Fault')
        # TODO: at the moment we only return the key, but not the name
        result = int(self.busword[18:25][::-1])
        return result

    def __get_operating_mode__(self):
        """0: Standby,
           1: Weather [only],
           2: Map,
           3: Contour,
           4: Test,
           5: Turbulence [only],
           6: Weather & Turbulence,
           7: Reserved

        """
        return int(self.busword[26:29][::-1], 2)

    def __get_tilt_data__(self):
        return int(self.busword[29:36][::-1][0], 2) * (-16) + int(self.busword[29:36][::-1][1:], 2) * 0.25

    def __get_gain_data__(self):
        bstr = self.busword[36:42][::-1]
        # TODO: What to do with the Max and Cal values?
        return int(bstr)

    def __get_range_data__(self):
        """Range of radar beam in nm. (1nm = 1.825km)

        """
        code = {'000001':   5,
                '000010':  10,
                '000100':  20,
                '001000':  40,
                '010000':  80,
                '100000': 160,
                '111111': 315,
                '000000': 320}

        if self.busword[42:48][::-1] in code.keys():
            return code[self.busword[42:48][::-1]]
        else:
            return 9999

    def __get_data_accept__(self):
        """0: Do not accept data
           1: Accept data 1
           2: Accept data 2
           3: Accept any data

        """
        return int(self.busword[49:51][::-1], 2)

    def __get_scan_angle__(self):
        """
        Scanning Angle.

        """
        return int(self.busword[51:63][::-1], 2) * 0.087890625

    def __get_reflectivity__(self):
        """
        Weather condition encoding:
           0: No precipitation [<Z2]
           1: Light precipitation [Z2 to Z3]
           2: Moderate precipitation [Z3 to Z4]
           3: Heavy precipitation [Z4 to Z5]
           4: Very heavy precipitation [> Z5]
           5: Reserved
           6: Medium turbulence
           7: Heavy turbulence

        """
        # check whether there it is at least one '1'
        # in the busword; take a short-cut, if not
        if '1' in self.busword[64:]:
            data = [int(self.busword[ix:ix+3][::-1], 2) for ix in range(64, 1600, 3)]
        else:
            data = self.__EMPTY_DATA
        return data

    def __str__(self):
        cnt = 0
        outstring = '<%3s - %3s>  ' % (cnt+1, cnt+25)
        for d in self.Record['Reflectivity']:
            cnt += 1
            outstring += str(d)
            if cnt % 25 == 0:
                outstring += '\n' + '<%3s - %3s>  ' % (cnt+1, cnt+25)
            elif cnt % 5 == 0:
                outstring += '  '
            else:
                pass
        return outstring
