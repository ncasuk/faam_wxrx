'''
Created on 3 Jan 2012

@author: axel
'''

import bitstring
import os


INFO_TEMPLATE = '\n' + (20*'#') + '\n' +\
"""File path: {Filepath}
File name: {Filename}
File size: {self.file_size} bytes
Number of records: {self.NRecords}
Time: {time} secs
Avg. record length: {self.rec_length}""" + \
'\n' + 20*'#' + '\n'


#length of a single wxrx data record
_RECORD_LENGTH = 1744
_LABEL = '550'


class Reader(object):

    def __init__(self, infile, start=None, length=None):
        """Reader class for temporary weather-radar-data files.

        start and length units are records
        """
        self.Filename = infile
        self.file_size = os.stat(self.Filename).st_size
        self.Fulldata = bitstring.Bits(filename=infile)

        if start and length:
            self.Data = self.Fulldata[start * _RECORD_LENGTH:(start * _RECORD_LENGTH) + (length+1 * _RECORD_LENGTH)]
        else:
            self.Data = self.Fulldata

        self.Errors, self.Buswords, self.Records, self.sIndexList = [], [], [], []
        self._sIndex, self.NRecords = 0, 0

    def get_data(self):
        result = {}
        result['Errors'] = self.Errors
        result['Records'] = self.Records
        result['sIndexList'] = self.sIndexList
        result['NRecords'] = self.NRecords
        result['_sIndex'] = self._sIndex
        return result

    def __get_offset__(self, start_ix):
        i = 144
        if str(self.Data[start_ix+i:start_ix+i+9].oct) == _LABEL:
            return i
        i = 0
        while True:
            if start_ix+i+9 > len(self.Data):
                break
            if str(self.Data[start_ix+i:start_ix+i+9].oct) == _LABEL:
                return i
            else:
                i += 1

    def parse(self):
        #n = int(float(os.stat(self.Filename).st_size) / 200.)
        n = int(len(self.Data)/float(_RECORD_LENGTH))

        for i in range(0, n):
            if self._sIndex > (len(self.Data) - 2000):
                break
            rec = self.Data[self._sIndex:self._sIndex + 1600]
            if not str(rec[0:9].oct) == _LABEL:
                offset = self.__get_offset__(self._sIndex)
                self._sIndex += offset
                if offset != 144 and offset != 0:
                    self.Errors.append(('label error', i, offset))
            try:
                self.Buswords.append(self.Data[self._sIndex:self._sIndex+1600])
                self.sIndexList.append(self._sIndex)
            except:
                pass
            self._sIndex += 1600
            self.NRecords += 1

    def __str__(self):
        # TODO: add ERORR to the output
        if self.NRecords > 0:
            self.rec_length = str(float(self._sIndex) / float(self.NRecords))
        else:
            self.rec_length = 'unknown'
        return (INFO_TEMPLATE.format(Filename=os.path.basename(self.Filename),
                                     Filepath=os.path.dirname(self.Filename),
                                     time = self.NRecords/190.,
                                     self=self))
