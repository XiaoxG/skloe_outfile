#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import struct
import math
import warnings
import numpy as np
import pandas as pd
import scipy.io as sio

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
            warnings.warn(
                "File {0:s} does not exist. Breaking".format(filename))
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
            self.date = '{0:2s}/{1:2s}'.format(dateMonth, dateDay)
            #print('Segment number: {0:2d}; Channel number: {1:3d}; Sampling frequency: {2:4d}Hz.'.format(
            #    self.segN, self.chN, self.fs))

            # read the name of each channel
            read_fmt = self.chN * '16s'
            buf = struct.unpack(read_fmt, f_in.read(self.chN * 16))
            chName = [[] for i in range(self.chN)]
            chIdx = [[] for i in range(self.chN)]
            for idx, item in enumerate(buf):
                chName[idx] = buf[idx].decode('utf-8').rstrip()
                chIdx[idx] = 'Ch{0:02d}'.format(idx)
            # read the unit of each channel
            read_fmt = self.chN * '4s'
            buf = struct.unpack(read_fmt, f_in.read(self.chN * 4))
            chUnit = [[] for i in range(self.chN)]
            for idx, item in enumerate(buf):
                chUnit[idx] = buf[idx].decode('utf-8').rstrip()

            # read the coefficient of each channel
            read_fmt = '=' + self.chN * 'f'
            buf = f_in.read(self.chN * 4)
            chCoef = struct.unpack(read_fmt, buf)

            chInfo_dic = {'Name': chName,
                          'Unit': chUnit,
                          'Coef': chCoef}

            Column = ['Name', 'Unit', 'Coef']
            self.chInfo = pd.DataFrame(chInfo_dic, index=chIdx, columns=Column)

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

                seg_chn = seg_info[i_seg][1]
                samp_num[i_seg] = seg_info[i_seg][2] - 5

                # read the statiscal values of each channel
                read_fmt = '=' + seg_chn * 'h' + seg_chn * 'f' + seg_chn * 2 * 'h'
                buf = f_in.read(seg_chn * (2 * 3 + 4))
                seg_statistic[i_seg] = struct.unpack(read_fmt, buf)

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
        # segTime = [[] for i in range(self.segN)]
        startTime = ['' for i in range(self.segN)]
        stopTime = ['' for i in range(self.segN)]
        index = ['' for i in range(self.segN)]
        Duration = ['' for i in range(self.segN)]
        for n in range(self.segN):
            startTime[n] = '{0:02d}:{1:02d}:{2:02d}'.format(
                seg_info[n][6], seg_info[n][5], seg_info[n][4])
            stopTime[n] = '{0:02d}:{1:02d}:{2:02d}'.format(
                seg_info[n][10], seg_info[n][9], seg_info[n][8])
            index[n] = 'Seg{0:02d}'.format(n)
            Duration[n] = '{0:8.1f}s'.format(samp_num[n] / self.fs)
        segTime_dic = {'Start': startTime,
                       'Stop': stopTime,
                       'Duration': Duration,
                       'Note': note,
                       'N sample': samp_num}
        Column = ['Start', 'Stop', 'Duration', 'N sample', 'Note']
        segInfo = pd.DataFrame(segTime_dic, index=index, columns=Column)

        # convert the statistics into data matrix
        self.seg_statistic = [[] for i in range(self.segN)]
        for n in range(self.segN):
            seg_statistic_temp = np.reshape(
                np.array(seg_statistic[n], dtype='float64'), (4, self.chN)).transpose()
            for m in range(self.chN):
                seg_statistic_temp[m] *= chCoef[m]
            Column = ['Mean', 'STD', 'Max', 'Min']
            self.seg_statistic[n] = pd.DataFrame(
                seg_statistic_temp, index=chName, columns=Column)
            self.seg_statistic[n]['Unit'] = chUnit

        # convert the data_buf into data matrix
        self.data = [[] for i in range(self.segN)]
        for n in range(self.segN):
            data_temp = np.array(data_buf[n], dtype='float64')
            for m in range(self.chN):
                data_temp[:, m] *= chCoef[m]
            index = np.arange(1, segInfo['N sample'].iloc[n] + 1) / self.fs
            self.data[n] = pd.DataFrame(
                data_temp, index=index, columns=chName, dtype='float64')

        if self.s_seg == 'all':
            self.segInfo = segInfo
        else:
            self.data = [self.data[self.s_seg]]
            self.segInfo = segInfo[self.s_seg:self.s_seg + 1]
            self.segN = 1
            self.seg_statistic = [self.seg_statistic[self.s_seg]]

    def pInfo(self,
              printTxt=False,
              printExcel=False):
        print('-' * 50)
        print('Segment: {0:2d}; Channel: {1:3d}; Sampling frequency: {2:4d}Hz.'.format(
            self.segN, self.chN, self.fs))
        print(self.segInfo.to_string(justify='center'))
        print('-' * 50)
        path = os.getcwd()
        path += '/' + os.path.splitext(self.filename)[0]
        if printTxt:
            fname = path + '_Info.txt'
            self.segInfo.to_csv(path_or_buf=fname, sep='\t')
        if printExcel:
            fname = path + '_Info.xlsx'
            self.segInfo.to_excel(fname, sheet_name='Sheet01')

    def pChInfo(self,
                 printTxt=False,
                 printExcel=False):
        print('-' * 50)
        print(self.chInfo.to_string(justify='center'))
        print('-' * 50)
        if printTxt:
            path = os.getcwd()
            fname = path + '/' + \
                os.path.splitext(self.filename)[0] + 'ChInfo.txt'
            infoFile = open(fname, 'w')
            infoFile.write('Channel total: {0:3d} \n'.format(self.chN))
            formatters = {'Name': "{:16s}".format,
                          "Unit": "{:4s}".format,
                          "Coef": "{: .7f}".format}
            infoFile.write(self.chInfo.to_string(
                formatters=formatters, justify='center'))
            infoFile.close()
        if printExcel:
            file_name = path + '/' + \
                os.path.splitext(self.filename)[0] + '_ChInfo.xlsx'
            self.chInfo.to_excel(file_name, sheet_name='Sheet01')

    def out2dat(self,
                seg='all'):
        def writefile(self, idx):
            path = os.getcwd()
            file_name = path + '/' + \
                os.path.splitext(self.filename)[
                    0] + '_seg{0:02d}.txt'.format(idx)
            comments = '\t'.join(
                self.chInfo['Name']) + '\n' + '\t'.join(self.chInfo['Unit']) + '\n'
            hearder_fmt_str = 'File: {0:s}, Seg{1:02d}, fs:{2:4d}Hz\nDate: {3:5s} from: {4:8s} to {5:8s}\nNote:{6:s}\n'
            header2write = hearder_fmt_str.format(
                self.filename, idx, self.fs, self.date, self.segInfo['Start'].iloc[idx], self.segInfo['Stop'].iloc[idx], self.segInfo['Note'].iloc[idx])
            header2write += comments
            infoFile = open(file_name, 'w')
            infoFile.write(header2write)
            data_2write = self.data[idx].to_string(header=False,
                                                   index=False, justify='left', float_format='% .5E')
            infoFile.write(data_2write)
            infoFile.close()

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
            printTxt=False,
            printExcel=False):
        print('-' * 50)
        print('Segment total: {0:02d}'.format(self.segN))
        for idx, istatictis in enumerate(self.seg_statistic):
            print('')
            print('Seg{0:02d}'.format(idx))
            print(istatictis.to_string(float_format='% .3E', justify='center'))
            print('')
        print('-' * 50)
        path = os.getcwd()
        if printTxt:
            file_name = path + '/' + \
                os.path.splitext(self.filename)[0] + '_statistic.txt'
            infoFile = open(file_name, 'w')
            infoFile.write('Segment total: {0:02d}\n'.format(self.segN))
            for idx, istatictis in enumerate(self.seg_statistic):
                infoFile.write('\n')
                infoFile.write('Seg{0:02d}\n'.format(idx))
                infoFile.write(istatictis.to_string(
                    float_format='% .3E', justify='center'))
            infoFile.close()
        if printExcel:
            file_name = path + '/' + \
                os.path.splitext(self.filename)[0] + '_statistic.xlsx'
            for idx, istatictis in enumerate(self.seg_statistic):
                istatictis.to_excel(file_name, sheet_name='SEG{:02d}'.format(idx))
            
    def out2mat(self, s_seg=0):
        if isinstance(s_seg, int):
            if s_seg <= self.segN:
                data_dic = {'Data': self.data[s_seg].values,
                            'chInfo': self.chInfo,
                            'Date': self.date,
                            'Nseg': 1,
                            'fs': self.fs,
                            'chN': self.chN,
                            'Seg_sta': self.seg_statistic[s_seg],
                            'SegInfo': self.segInfo[s_seg:s_seg + 1],
                            'Readme': 'Generated by Skloe_OutFile from python'
                            }
                path = os.getcwd()
                fname = path + '/' + \
                    os.path.splitext(self.filename)[0] + 'seg{:2d}.mat'.format(s_seg)
                sio.savemat(fname, data_dic)
            else:
                 warnings.warn('seg exceeds the max.')
        else:
            warnings.warn('Input s_seg is illegal. (int or defalt)')

    # def plot(self, i_seg, i_ch):
    # def ts2spec():
    # def ts2statictics():
