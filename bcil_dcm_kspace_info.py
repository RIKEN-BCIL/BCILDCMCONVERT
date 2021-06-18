#!/usr/bin/env python3
# coding:utf-8
import warnings
import re
import decimal


class BcilDcmKspaceInfo:

    ds = None
    errors = []

    __real_dwell_time = None
    __acquisition_matrix_text = None
    __bandwidth_per_pixel_phase_encode = None
    __phase_encoding_direction_positive = None
    __coil_for_gradient2 = None

    __ascii_data = None

    def __init__(self, dicom_ds):
        self.ds = dicom_ds
        self.errors = []

        manufacturer = self.ds["0x0080070"].value if "0x0080070" in self.ds else None
        if manufacturer != "SIEMENS":
            self.errors.append("data is not from Siemens MRI")
            return

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from nibabel.nicom.csareader import CSAReadError
            import nibabel.nicom.csareader as c
            try:
                csa_img_data = c.get_csa_header(self.ds)
                if csa_img_data:
                    self.__real_dwell_time = c.get_scalar(csa_img_data, "RealDwellTime")
                    self.__acquisition_matrix_text = c.get_acq_mat_txt(csa_img_data)
                    self.__bandwidth_per_pixel_phase_encode = c.get_scalar(csa_img_data, "BandwidthPerPixelPhaseEncode")
                    self.__phase_encoding_direction_positive = c.get_scalar(csa_img_data, "PhaseEncodingDirectionPositive")

                csa_srs_data = c.get_csa_header(self.ds, 'series')
                if csa_srs_data:
                    self.__coil_for_gradient2 = c.get_scalar(csa_srs_data, "CoilForGradient2")

                self.__ascii_data = self.get_ascii_data()

            except CSAReadError:
                self.errors.append("CSA Header Info: acquisition error")
                return

    def get_dwell_time_read(self):
        if self.__real_dwell_time:
            dtr = str(decimal.Decimal(int(self.__real_dwell_time)) / decimal.Decimal(1000000000))
            return dtr.rstrip('0')
        self.errors.append("dwell_time_read: not in CSA Header")
        return None

    def get_dwell_time_phase(self):
        if self.__acquisition_matrix_text and self.__bandwidth_per_pixel_phase_encode:
            try:
                ast_num = self.__acquisition_matrix_text.find("*")
                am_num = self.__acquisition_matrix_text[:ast_num].rstrip('p')
                return 1 / (float(self.__bandwidth_per_pixel_phase_encode) * float(am_num))
            except (ValueError, TypeError) as e:
                self.errors.append("dwell_time_phase calc: " + e)
                self.errors.append("dwell_time_phase calc: AcquisitionMatrixText: " + self.__acquisition_matrix_text)
                self.errors.append(
                    "dwell_time_phase calc: BandwidthPerPixelPhaseEncode: " + self.__bandwidth_per_pixel_phase_encode)
                return None
        if self.__acquisition_matrix_text is None:
            self.errors.append("dwell_time_phase calc: AcquisitionMatrixText is empty")
        if self.__bandwidth_per_pixel_phase_encode is None:
            self.errors.append("dwell_time_phase calc: BandwidthPerPixelPhaseEncode is empty")
        return None

    def get_coil_for_gradient2(self):
        if self.__coil_for_gradient2:
            return self.__coil_for_gradient2
        self.errors.append("coil_for_gradient2: not in CSA Header")
        return None

    def get_directions(self):
        res = {
            "Read.direction": None,
            "Phase.direction": None,
            "Slice.direction": None,
        }
        # check
        if "0x00181312" not in self.ds:  # InPlanePhaseEncodingDirection
            self.errors.append("directions calc: InPlanePhaseEncodingDirection is empty")
            return res
        if "0x00200037" not in self.ds:  # ImageOrientationPatient
            self.errors.append("directions calc: ImageOrientationPatient is empty")
            return res
        if self.__phase_encoding_direction_positive is None:
            self.errors.append("directions calc: phase_encoding_direction_positive not in CSA Header")
            return res

        ph_pos = -1 if self.__phase_encoding_direction_positive == 0 else self.__phase_encoding_direction_positive
        iop6 = self.ds["0x00200037"].value

        ###############################
        # phase direction
        ###############################
        phase_ary = iop6[0]
        if self.ds["0x00181312"].value == "ROW":
            phase_ary = [iop6[0], iop6[1], iop6[2]]
        elif self.ds["0x00181312"].value == "COL":
            phase_ary = [iop6[3], iop6[4], iop6[5]]

        # 絶対値にする。
        abs_phase_ary = list(map(abs, phase_ary))
        max_abs_phase_val = max(abs_phase_ary)
        phase_index_list = [i for i, x in enumerate(abs_phase_ary) if x == max_abs_phase_val]
        phase_index = str((phase_index_list[0] + 1) * ph_pos)

        phase_dic = {
            "1":  {"val": "RL", "list": [-1, 0, 0]},
            "-1": {"val": "LR", "list": [1, 0, 0]},
            "2":  {"val": "AP", "list": [0, -1, 0]},
            "-2": {"val": "PA", "list": [0, 1, 0]},
            "3":  {"val": "HF", "list": [0, 0, 1]},
            "-3": {"val": "FH", "list": [0, 0, -1]},
        }

        ###############################
        # slice direction
        ###############################
        slice_ary = [
           (iop6[1] * iop6[5]) - (iop6[2] * iop6[4]),
           (iop6[2] * iop6[3]) - (iop6[0] * iop6[5]),
           (iop6[0] * iop6[4]) - (iop6[1] * iop6[3])
        ]
        abs_slice_ary = list(map(abs, slice_ary))
        max_abs_slice_val = max(abs_slice_ary)
        slice_index_list = [i for i, x in enumerate(abs_slice_ary) if x == max_abs_slice_val]
        slice_index = str(slice_index_list[0] + 1)
        slice_dic = {
            "1": {"val": "SAG", "list": [1, 0, 0]},
            "2": {"val": "COR", "list": [0, 1, 0]},
            "3": {"val": "AXI", "list": [0, 0, 1]},
        }

        ###############################
        # readout direction
        ###############################
        phase_tmp = phase_dic[phase_index]['list']
        slice_tmp = slice_dic[slice_index]['list']
        readout_ary = [
            (slice_tmp[1] * phase_tmp[2]) - (slice_tmp[2] * phase_tmp[1]),
            (slice_tmp[2] * phase_tmp[0]) - (slice_tmp[0] * phase_tmp[2]),
            (slice_tmp[0] * phase_tmp[1]) - (slice_tmp[1] * phase_tmp[0])
        ]
        sum_readout_ary = sum(readout_ary)
        abs_readout_ary = list(map(abs, readout_ary))
        max_abs_readout_val = max(abs_readout_ary)
        readout_index_list = [i for i, x in enumerate(abs_readout_ary) if x == max_abs_readout_val]
        readout_index = str((readout_index_list[0] + 1) * sum_readout_ary)
        readout_dic = {
            "1": {"val": "LR", "list": [1, 0, 0]},
            "-1":  {"val": "RL", "list": [-1, 0, 0]},
            "2": {"val": "PA", "list": [0, 1, 0]},
            "-2": {"val": "AP", "list": [0, -1, 0]},
            "3":  {"val": "HF", "list": [0, 0, 1]},
            "-3": {"val": "FH", "list": [0, 0, -1]},
        }

        # print("ro: '{}' {}".format(readout_dic[readout_index]["val"], readout_dic[readout_index]["list"]))
        # print("pe: '{}' {}".format(phase_dic[phase_index]["val"], phase_dic[phase_index]["list"]))
        # print("ss: '{}' {}".format(slice_dic[slice_index]["val"], slice_dic[slice_index]["list"]))
        return {
            "Read.direction": readout_dic[readout_index]["val"] or None,
            "Phase.direction": phase_dic[phase_index]["val"] or None,
            "Slice.direction": slice_dic[slice_index]["val"] or None,
        }

    def get_parallel_factor(self):
        if self.__ascii_data and "sPat.lAccelFactPE" in self.__ascii_data:
            return self.__ascii_data["sPat.lAccelFactPE"]
        self.errors.append("parallel factor: not in ascconv")
        return None

    def get_multiband_factor(self):
        if self.__ascii_data and "sWipMemBlock.alFree[13]" in self.__ascii_data:
            return self.__ascii_data["sWipMemBlock.alFree[13]"]
        self.errors.append("multiband factor: not in ascconv")
        return None

    def get_system(self):
        # ascii_data = self.get_ascii_data()
        if self.__ascii_data and "sProtConsistencyInfo.tBaselineString" in self.__ascii_data:
            return self.__ascii_data["sProtConsistencyInfo.tBaselineString"]
        self.errors.append("system: not in ascconv")
        return None

    def get_flReferenceAmplitude(self):
        if self.__ascii_data and "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude" in self.__ascii_data:
            return self.__ascii_data["sTXSPEC.asNucleusInfo[0].flReferenceAmplitude"]
        self.errors.append("sTXSPEC.asNucleusInfo[0].flReferenceAmplitude: not in ascconv")
        return None

    def get_ascii_data(self):
        if "0x00291020" not in self.ds:
            self.errors.append("00291020")
            return

        s = str(self.ds["0x00291020"].value)
        m = re.findall(r"((### ASCCONV BEGIN)(.*?)(###\\n))(.*?)(\\n### ASCCONV END ###)", s)
        if len(m) == 0 or m[0][4] is None:
            self.errors.append("ascconv: can not find")
            return

        tmp = m[0]  # 1つめにHITしたものを利用します。
        ascconv = re.sub(r'\\n', "\n", tmp[4], 0, re.MULTILINE)
        ascconv = re.sub(r'\\t', "", ascconv, 0, re.MULTILINE)

        result = {}
        for line in ascconv.splitlines():
            tmp = line.split(r"=")
            if len(tmp) == 2:
                result[tmp[0].strip(" ").strip('"')] = tmp[1].strip(" ").strip('"')
        return result


if __name__ == '__main__':

    from argparse import ArgumentParser
    import pydicom
    import os
    from pydicom.errors import InvalidDicomError

    usage = \
        "\n\n" \
        "  ex). $ python3 bcil_dcm_kspace_info.py <DICOM full path>\n" \
        "\n\n" \
        "".format(__file__)
    ap = ArgumentParser(usage=usage)
    ap.add_argument('dicomFullPath', type=str)
    args = ap.parse_args()

    if not os.path.exists(args.dicomFullPath):
        print(args.dicomFullPath + ' :not found')
        exit()

    if not os.path.isfile(args.dicomFullPath):
        print(args.dicomFullPath + ' :not file')
        exit()

    try:
        dcm_ds = pydicom.read_file(args.dicomFullPath)
        k = BcilDcmKspaceInfo(dcm_ds)
        print(args.dicomFullPath)
        print("{}: {}".format("Gradient", k.get_coil_for_gradient2() or "None"))
        print("{}: {}".format("System", k.get_system() or "None"))
        print("{}: {}".format("flReferenceAmplitude", k.get_flReferenceAmplitude() or "None"))
        print("{}: {}".format("DwelltimeRead", k.get_dwell_time_read() or "None"))
        print("{}: {}".format("DwelltimePhase", k.get_dwell_time_phase() or "None"))
        directions = k.get_directions()
        for key, val in directions.items():
            print("{}: {}".format(key, val or "None"))

        if k.errors:
            for val in k.errors:
                print("  failure > " + val)

    except InvalidDicomError:
        print(args.dicomFullPath + ' :can not read file')
        exit()
