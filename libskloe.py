#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import struct
import math
import warnings
import numpy as np
import scipy.io as sio
import pdb

class Skloe_OutFile():
    """
    *.out file class for SKLOE
    Method:
    1. out.read()       load the *.out file to Python
    2. out.pInfo()      print general info of the loaded file
    3. out.pChCoeff()   print the channel info (Name Unit Coeff.)
    4. out.out2dat()    convert data to .dat file
    5. out.out2mat()    convert data to .mat file
    """

    def __init__(self, filename, s_seg='all', debug=False):

        if os.path.exists(filename):
            self.filename = filename
        else:
            warnings.warn("File {0:s} does not exist. Breaking".format(filename))
        self.DEBUG = debug
        self.fs = 0
        self.chN = 0
        self.segN = 0
        if isinstance(s_seg, int):
            self.s_seg = s_seg
        elif isinstance(s_seg, str):
            if s_seg == 'all':
                self.s_seg = s_seg
            else:
                warnings.warn("Input s_seg is illegal. (int or defalt)")
        else:
            warnings.warn("Input s_seg is illegal. (int or defalt)")

        self.read()
  
    def read(self):
        """read the measured *.out file"""
        # read the data file
        print('Opening file {0}'.format(self.filename))
        with open(self.filename, 'rb') as f_in:
            # file head
            read_fmt = '=hhlhh2s2s240s'
            buf = f_in.read(256)
            if not buf:
                warnings.warn("Reading data file {0} failed, exiting...".format(
                    self.filename))
            tmp = struct.unpack(read_fmt, buf)
            index, self.chN, self.fs, self.segN = tmp[0], tmp[1], tmp[3], tmp[4]
            dateMonth, dateDay = tmp[5].decode('utf-8'), tmp[6].decode('utf-8')
            self.date = '{0:2s}/{1:2s}'.format(dateMonth,dateDay)
            #print('Segment number: {0:2d}; Channel number: {1:3d}; Sampling frequency: {2:4d}Hz.'.format(
            #    self.segN, self.chN, self.fs))

            # read the name of each channel
            read_fmt = self.chN * '16s'
            buf = struct.unpack(read_fmt, f_in.read(self.chN * 16))
            self.chName = [[] for i in range(self.chN)]
            for idx, item in enumerate(buf):
                self.chName[idx] = buf[idx].decode('utf-8').rstrip()

            # read the unit of each channel
            read_fmt = self.chN * '4s'
            buf = struct.unpack(read_fmt, f_in.read(self.chN * 4))
            self.chUnit = [[] for i in range(self.chN)]
            for idx, item in enumerate(buf):
                self.chUnit[idx] = buf[idx].decode('utf-8').rstrip()

            # read the coefficient of each channel
            read_fmt = '=' + self.chN * 'f'
            buf = f_in.read(self.chN * 4)
            self.chCoef = struct.unpack(read_fmt, buf)



            # read the id of each channel, if there are
            if (index < -1):
                read_fmt = '=' + self.chN * 'h'
                buf = f_in.read(self.chN * 2)
                chID = struct.unpack(read_fmt, buf)
            else:
                chID = []

            # samp_num[i] is the number of samples in segment i
            samp_num = [0 for i in range(self.segN)]
            # seg_info[i] is the information of the segment i
            # [seg_index, seg_chn, samp_num, ds, s, min, h, desc]
            seg_info = [[] for i in range(self.segN)]
            # seg_satistic[i] is the satistical values of the segment i
            # [mean[seg_chn], std[seg_chn], max[seg_chn], min[seg_chn]]
            seg_statistic = [[] for i in range(self.segN)]
            # data_buf[i] are the data of the segment i
            data_buf = [[] for i in range(self.segN)]

            # read data of each segment
            for i_seg in range(self.segN):
                # jump over the blank section
                p_cur = f_in.tell()
                f_in.seek(128 * math.ceil(p_cur / 128))

                # read segment informantion
                read_fmt = '=hhlBBBBBBBB240s'
                buf = f_in.read(256)
                seg_info[i_seg] = struct.unpack(read_fmt, buf)
                print(seg_info[i_seg]) if self.DEBUG else 0

                seg_chn = seg_info[i_seg][1]
                print(seg_chn == self.chN) if self.DEBUG else 0
                samp_num[i_seg] = seg_info[i_seg][2] - 5

                # read the statiscal values of each channel
                read_fmt = '=' + seg_chn * 'h' + seg_chn * 'f' + seg_chn * 2 * 'h'
                buf = f_in.read(seg_chn * (2 * 3 + 4))
                seg_statistic[i_seg] = struct.unpack(read_fmt, buf)
                print(seg_statistic[i_seg]) if self.DEBUG else 0
  
                # read the data in each channel
                for item in range(samp_num[i_seg]):
                    read_fmt = '=' + seg_chn * 'h'
                    buf = f_in.read(seg_chn * 2)
                    if not buf:
                        break
                    data_buf[i_seg].append(struct.unpack(read_fmt, buf))
        
        note = [[] for i in range(self.segN)]
        for n in range(self.segN):
            note[n] = seg_info[n][11].decode('utf-8').rstrip() 
        # read start and stop time
        segTime = [[] for i in range(self.segN)]
        for n in range(self.segN):
            startTime = '{0:02d}:{1:02d}:{2:02d}'.format(
                seg_info[n][6], seg_info[n][5], seg_info[n][4])
            stopTime = '{0:02d}:{1:02d}:{2:02d}'.format(
                seg_info[n][10], seg_info[n][9], seg_info[n][8])
            segTime[n] = [startTime, stopTime]

        # convert the statistics into data matrix
        self.seg_statistic = [[] for i in range(self.segN)]
        for n in range(self.segN):
            seg_statistic_tmp = np.array(seg_statistic[n], dtype='float64')
            self.seg_statistic[n] = np.reshape(seg_statistic_tmp,(self.chN,4))
            for m in range(self.chN):
                self.seg_statistic[n][m] *= self.chCoef[m]
        
        # convert the data_buf into data matrix
        self.data = [[] for i in range(self.segN)]
        for n in range(self.segN):
            self.data[n] = np.array(data_buf[n], dtype='float64')
            for m in range(self.chN):
                print(self.chCoef[m]) if self.DEBUG else 0
                self.data[n][:, m] *= self.chCoef[m]

        #self.segInfo = list(zip(self.chName, self.chUnit, self.chCoef))

        if self.s_seg == 'all':
            self.samp_num = samp_num
            self.note = note
            self.segTime = segTime
        else:
            self.samp_num = [samp_num[self.s_seg]]
            self.data = [self.data[self.s_seg]]
            self.note = [note[self.s_seg]]
            self.segTime = [segTime[self.s_seg]]
            self.segN = 1
            self.seg_statistic = [self.seg_statistic[self.s_seg]]
        # if self.s_seg == 'all':
        #     return self.segN, self.chN, self.fs, samp_num,\
        #         list(zip(self.chName, self.chUnit, self.chCoef)
        #              ), self.data
        # else:
        #     return self.segN, self.chN, self.fs, samp_num[self.s_seg],\
        #         list(zip(self.chName, self.chUnit, self.chCoef)
        #              ), self.data[self.s_seg]


    def pInfo(self, 
              printTxt=False):
        print('-' * 50)
        print('Segment: {0:2d}; Channel: {1:3d}; Sampling frequency: {2:4d}Hz.'.format(
                self.segN, self.chN, self.fs))
        for idx, timeSeg in enumerate(self.segTime):
            print('Seg{0:02d}: Date: {3:5s} from: {1:8s} to {2:8s}. Duration: {5:7.2f}s; Note:{4:s}'.format(
                idx, timeSeg[0], timeSeg[1], self.date, self.note[idx], self.samp_num[idx] / self.fs))
        print('-' * 50)
        if printTxt:
            path = os.getcwd()
            infoFile = open(path + '/' + os.path.splitext(self.filename)[0] + '_Info.txt', 'w')
            infoFile.write('Segment: {0:2d}; Channel: {1:3d}; Sampling frequency: {2:4d}Hz.\n'.format(
                            self.segN, self.chN, self.fs))
            for idx, timeSeg in enumerate(self.segTime):
                infoFile.write('Seg{0:02d}: Date: {3:5s} from: {1:8s} to {2:8s}. Duration: {5:7.2f}s; Note:{4:s}\n'.format(
                        idx, timeSeg[0], timeSeg[1], self.date, self.note[idx], self.samp_num[idx] / self.fs))
            infoFile.close()

    def pChCoeff(self, 
                printTxt=False):
        print('-' * 50)
        print('Channel total: {0:3d}'.format(self.chN))
        for idx, name in enumerate(self.chName):
            print('{0:03d} {1:16s} {2:4s} {3:16.7f}'.format(idx,name,self.chUnit[idx],self.chCoef[idx]))
        print('-' * 50)
        if printTxt:
            path = os.getcwd()
            infoFile = open(path + '/' + os.path.splitext(self.filename)[0] + 'ChCoeff.txt', 'w')
            infoFile.write('Channel total: {0:3d} \n'.format(self.chN))
            for idx, name in enumerate(self.chName):
                infoFile.write('{0:03d} {1:16s} {2:4s} {3:16.7f}\n'.format(
                    idx, name, self.chUnit[idx], self.chCoef[idx]))
            infoFile.close()
       
    def out2dat(self, 
                seg='all'):
        def writefile(self, idx):
            path = os.getcwd()
            file_name = path + '/' + os.path.splitext(self.filename)[0] + '_seg{0:02d}.txt'.format(idx)
            comments = '\t'.join(self.chName) + '\n' + '\t'.join(self.chUnit) + '\n'
            hearder_fmt_str = 'File: {0:s}, Seg{1:02d}, fs:{2:4d}Hz\nDate: {3:5s} from: {4:8s} to {5:8s}\nNote:{6:s}\n'
            header2write = hearder_fmt_str.format(self.filename, idx, self.fs, self.date, self.segTime[idx][0], self.segTime[idx][1], self.note[idx])
            header2write += comments
            data_2write = self.data[idx]
            np.savetxt(file_name, data_2write, fmt='% .5E', delimiter='\t',
                            newline='\n', header=header2write)

        if seg == 'all':
            for idx in range(self.segN):
                writefile(self, idx)
        elif isinstance(seg, int):
            if seg <= self.segN:
                writefile(self, seg)
            else:
                warnings.warn('seg exceeds the max.')
        else:
            warnings.warn('Input s_seg is illegal. (int or defalt)')
    
    def pst(self, 
            printTxt=False):
        print('-' * 50)
        print('Segment total: {0:02d}'.format(self.segN))
        for idx, istatictis in enumerate(self.seg_statistic):
            print('')
            print('Seg{0:02d}'.format(idx))
            for nch, iistatictis in enumerate(istatictis):
                fmt_str = 'Ch{0:02d} {1:16s} {2:6s} {3: .4E} {4: .4E} {5: .4E} {6: .4E}'
                print(fmt_str.format(
                    nch, self.chName[nch], self.chUnit[nch], iistatictis[0].item(), iistatictis[1].item(), iistatictis[2].item(), iistatictis[3].item()))
            print('')
        print('-' * 50)
        if printTxt:
            path = os.getcwd()
            file_name = path + '/' + os.path.splitext(self.filename)[0] + '_statistic.txt'
            infoFile = open(file_name, 'w')
            infoFile.write('Segment total: {0:02d}\n'.format(self.segN))
            for idx, istatictis in enumerate(self.seg_statistic):
                infoFile.write('\n')
                infoFile.write('Seg{0:02d}\n'.format(idx))
                for nch, iistatictis in enumerate(istatictis):
                    fmt_str = 'Ch{0:02d} {1:16s} {2:6s} {3: .4E} {4: .4E} {5: .4E} {6: .4E}\n'
                    infoFile.write(fmt_str.format(
                        nch, self.chName[nch], self.chUnit[nch], iistatictis[0].item(), iistatictis[1].item(), iistatictis[2].item(), iistatictis[3].item()))

    def out2mat(self,
                s_seg='all'):
        if s_seg == 'all':
            data_dic = {'Data':self.data,
                'Note':self.note,
                'chCoef':self.chCoef,
                'chName':self.chName,
                'chUnit':self.chUnit,
                'Date':self.date,
                'Nseg':self.segN,
                'SegTime':self.segTime,
                'fs':self.fs,
                'samp_num':self.samp_num,
                'chN':self.chN,
                'Readme':'Generated by Skloe_OutFile from python'
            }
            path = os.getcwd()
            fname = path + '/' + \
                os.path.splitext(self.filename)[0] + '.mat'
            sio.savemat(fname,data_dic)
        elif isinstance(s_seg, int):
            if s_seg <= self.segN:
                data_dic = {'Data': self.data[s_seg],
                            'Note': self.note[s_seg],
                            'chCoef': self.chCoef,
                            'chName': self.chName,
                            'chUnit': self.chUnit,
                            'Date': self.date,
                            'Nseg': 1,
                            'SegTime': self.segTime[s_seg],
                            'fs': self.fs,
                            'samp_num': self.samp_num[s_seg],
                            'chN': self.chN,
                            'Readme': 'Generated by Skloe_OutFile from python'
                            }
                path = os.getcwd()
                fname = path + '/' + \
                        os.path.splitext(self.filename)[0] + 'seg{0:2d}.mat'.format(s_seg)
                sio.savemat(fname, data_dic)
            else:
                 warnings.warn('seg exceeds the max.')
        else:
            warnings.warn('Input s_seg is illegal. (int or defalt)')


    # def plot(self, i_seg, i_ch):
    # def ts2spec():
    # def ts2statictics():
