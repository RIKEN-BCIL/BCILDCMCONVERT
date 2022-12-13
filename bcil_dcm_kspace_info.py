#!/usr/bin/python3
# coding:utf-8
import warnings
import re
import decimal
from typing import Optional
import pydicom


class BcilDcmKspaceInfo:

    __mri_identifier = ""

    __real_dwell_time = None
    __acquisition_matrix_text = None
    __bandwidth_per_pixel_phase_encode = None
    __phase_encoding_direction_positive = None
    __coil_for_gradient2 = None

    __ascii_data = None

    __parallel_factor = None
    __multiband_factor = None
    __system = None
    __fl_reference_amplitude = None

    __uc_flip_angle_mode = None
    __phase_partial_fourier = None
    __slice_partial_fourier = None

    __in_plane_phase_encodeing_direction = None
    __image_orientation_patient = None

    __partial_fourier_dict = {
        "16": "OFF",
        "8": " 7/8",
        "4": " 6/8",
        "2": " 5/8",
        "1": " 4/8",
    }

    def __init__(self, dicom_ds: pydicom.dataset.FileDataset):

        self.ds = dicom_ds
        self.errors = []

        manufacturer = self.ds["0x00080070"].value if "0x00080070" in self.ds else None
        if 'SIEMENS' not in manufacturer.upper():
            # Siemensのみ対応
            self.errors.append("data is not from Siemens MRI")
            return

        # mriの種類
        self.__mri_identifier = ""  # XA以外
        if "SoftwareVersions" in self.ds and "XA" in self.ds.SoftwareVersions:
            if "MediaStorageSOPClassUID" in self.ds.file_meta:
                if self.ds.file_meta.MediaStorageSOPClassUID == "1.2.840.10008.5.1.4.1.1.4.1":
                    self.__mri_identifier = "extended"  # Enhanced MR Image IOD
                    self.set_data_siemens_extended()
                elif self.ds.file_meta.MediaStorageSOPClassUID == "1.2.840.10008.5.1.4.1.1.4":
                    self.__mri_identifier = "interoperatabillity"
                    self.set_data_siemens_interoperatabillity()
                elif self.ds.file_meta.MediaStorageSOPClassUID == "1.2.840.10008.5.1.4.1.1.4.3":
                    self.__mri_identifier = "extended"  # Enhanced MR Color Image IOD
                    self.set_data_siemens_extended()
        if self.__mri_identifier == "":
            self.set_data_siemens()

    def set_data_siemens(self):
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

                if "0x00291020" not in self.ds:
                    self.errors.append("0x00291020 (### ASCCONV ###)" + " value not found")
                else:
                    self.__ascii_data = self.get_ascii_data(str(self.ds["0x00291020"].value))
                    if self.__ascii_data is not None:
                        if "sKSpace.ucPhasePartialFourier" in self.__ascii_data:
                            self.__phase_partial_fourier = self.__ascii_data["sKSpace.ucPhasePartialFourier"]
                        if "sKSpace.ucSlicePartialFourier" in self.__ascii_data:
                            self.__slice_partial_fourier = self.__ascii_data["sKSpace.ucSlicePartialFourier"]
                        if "sPat.lAccelFactPE" in self.__ascii_data:
                            self.__parallel_factor = self.__ascii_data["sPat.lAccelFactPE"]
                        if "sWipMemBlock.alFree[13]" in self.__ascii_data:
                            self.__multiband_factor = self.__ascii_data["sWipMemBlock.alFree[13]"]
                        if "sProtConsistencyInfo.tBaselineString" in self.__ascii_data:
                            self.__system = self.__ascii_data["sProtConsistencyInfo.tBaselineString"]
                        if "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude" in self.__ascii_data:
                            self.__fl_reference_amplitude = self.__ascii_data["sTXSPEC.asNucleusInfo[0].flReferenceAmplitude"]

            except CSAReadError:
                self.errors.append("CSA Header Info: acquisition error")
                return

        if "InPlanePhaseEncodingDirection" in self.ds:
            self.__in_plane_phase_encodeing_direction = self.ds.InPlanePhaseEncodingDirection
        if "ImageOrientationPatient" in self.ds:
            self.__image_orientation_patient = self.ds.ImageOrientationPatient

    def set_data_siemens_vida(self):
        self.__real_dwell_time = self.ds["0x00211142"].value if "0x00211142" in self.ds else None
        self.__acquisition_matrix_text = self.ds["0x00211158"].value if "0x00211158" in self.ds else None
        self.__bandwidth_per_pixel_phase_encode = self.ds["0x00211153"].value if "0x00211153" in self.ds else None
        self.__phase_encoding_direction_positive = self.ds["0x0021111c"].value if "0x0021111c" in self.ds else None

        self.__coil_for_gradient2 = self.ds["0x00211033"].value if "0x00211033" in self.ds else None

        self.__multiband_factor = self.ds["0x00211156"].value if "0x00211156" in self.ds else None
        self.__system = self.ds.SoftwareVersions

        self.__in_plane_phase_encodeing_direction = self.ds.InPlanePhaseEncodingDirection
        self.__image_orientation_patient = self.ds.ImageOrientationPatient

        if "0x00211019" not in self.ds:
            self.errors.append("0x00211019 (### ASCCONV ###)" + " value not found")
        else:
            self.__ascii_data = self.get_ascii_data(str(self.ds["0x00211019"].value))
            if self.__ascii_data is not None:
                if "sPat.lAccelFactPE" in self.__ascii_data:
                    self.__parallel_factor = self.__ascii_data["sPat.lAccelFactPE"]
                if "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude" in self.__ascii_data:
                    self.__fl_reference_amplitude = self.__ascii_data["sTXSPEC.asNucleusInfo[0].flReferenceAmplitude"]

    def set_data_siemens_extended(self):

        self.__system = self.ds.SoftwareVersions

        if "0x52009230" in self.ds:
            csa9230 = self.ds["0x52009230"].value[0]
            if "0x002111fe" in csa9230:
                hdr002111fe = csa9230["0x002111fe"].value[0]
                self.__phase_encoding_direction_positive = hdr002111fe["0x0021111c"].value if "0x0021111c" in hdr002111fe else None
                self.__acquisition_matrix_text = hdr002111fe["0x00211158"].value if "0x00211158" in hdr002111fe else None
                self.__bandwidth_per_pixel_phase_encode = hdr002111fe["0x00211153"].value if "0x00211153" in hdr002111fe else None

            if "0x00209116" in csa9230:
                hdr00209116 = csa9230["0x00209116"].value[0]
                self.__image_orientation_patient = hdr00209116["0x00200037"].value if "0x00200037" in hdr00209116 else None

        if "0x52009229" in self.ds:
            csa9229 = self.ds["0x52009229"].value[0]
            if "0x00189125" in csa9229:
                hdr00189125 = csa9229["0x00189125"].value[0]
                self.__in_plane_phase_encodeing_direction = hdr00189125["0x00181312"].value if "0x00181312" in hdr00189125 else None

            if "0x002110fe" in csa9229:
                hdr002110fe = csa9229["0x002110fe"].value[0]
                self.__coil_for_gradient2 = hdr002110fe["0x00211033"].value if "0x00211033" in hdr002110fe else None
                if "0x00211019" in hdr002110fe:
                    self.__ascii_data = self.get_ascii_data(str(hdr002110fe["0x00211019"].value))
                    if self.__ascii_data is not None:
                        self.__real_dwell_time = self.__ascii_data["sRXSPEC.alDwellTime[0]"]
                        self.__multiband_factor = self.__ascii_data["sWipMemBlock.alFree[13]"] if "sWipMemBlock.alFree[13]" in self.__ascii_data else None
                        if "sPat.lAccelFactPE" in self.__ascii_data:
                            self.__parallel_factor = self.__ascii_data["sPat.lAccelFactPE"]
                        if "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude" in self.__ascii_data:
                            self.__fl_reference_amplitude = self.__ascii_data["sTXSPEC.asNucleusInfo[0].flReferenceAmplitude"]
                        if "ucFlipAngleMode" in self.__ascii_data:
                            self.__uc_flip_angle_mode = self.__ascii_data["ucFlipAngleMode"]
                        if "sKSpace.ucPhasePartialFourier" in self.__ascii_data:
                            self.__phase_partial_fourier = self.__ascii_data["sKSpace.ucPhasePartialFourier"]
                        if "sKSpace.ucSlicePartialFourier" in self.__ascii_data:
                            self.__slice_partial_fourier = self.__ascii_data["sKSpace.ucSlicePartialFourier"]
                else:
                    self.errors.append("52009229>002110fe>00211019(### ASCCONV ###) value not found")

    def set_data_siemens_interoperatabillity(self):

        self.__real_dwell_time = self.ds["0x00211142"].value if "0x00211142" in self.ds else None
        self.__acquisition_matrix_text = self.ds["0x00211158"].value if "0x00211158" in self.ds else None
        self.__bandwidth_per_pixel_phase_encode = self.ds["0x00211153"].value if "0x00211153" in self.ds else None
        self.__phase_encoding_direction_positive = self.ds["0x0021111c"].value if "0x0021111c" in self.ds else None

        self.__coil_for_gradient2 = self.ds["0x00211033"].value if "0x00211033" in self.ds else None

        self.__multiband_factor = self.ds["0x00211156"].value if "0x00211156" in self.ds else None
        self.__system = self.ds.SoftwareVersions

        self.__in_plane_phase_encodeing_direction = self.ds.InPlanePhaseEncodingDirection
        self.__image_orientation_patient = self.ds.ImageOrientationPatient

        if "0x00211019" not in self.ds:
            self.errors.append("0x00211019 (### ASCCONV ###)" + " value not found")
        else:
            self.__ascii_data = self.get_ascii_data(str(self.ds["0x00211019"].value))
            if self.__ascii_data is not None:
                if "sPat.lAccelFactPE" in self.__ascii_data:
                    self.__parallel_factor = self.__ascii_data["sPat.lAccelFactPE"]
                if "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude" in self.__ascii_data:
                    self.__fl_reference_amplitude = self.__ascii_data["sTXSPEC.asNucleusInfo[0].flReferenceAmplitude"]
                if "ucFlipAngleMode" in self.__ascii_data:
                    self.__uc_flip_angle_mode = self.__ascii_data["ucFlipAngleMode"]
                if "sKSpace.ucPhasePartialFourier" in self.__ascii_data:
                    self.__phase_partial_fourier = self.__ascii_data["sKSpace.ucPhasePartialFourier"]
                if "sKSpace.ucSlicePartialFourier" in self.__ascii_data:
                    self.__slice_partial_fourier = self.__ascii_data["sKSpace.ucSlicePartialFourier"]

    # output ###
    def get_dwell_time_read(self) -> Optional[str]:
        if self.__real_dwell_time is None:
            self.errors.append("dwell_time_read: not found")
            return None

        dtr = str(decimal.Decimal(int(self.__real_dwell_time)) / decimal.Decimal(1000000000))
        return dtr.rstrip('0')

    def get_dwell_time_phase(self) -> Optional[str]:
        if self.__acquisition_matrix_text is None:
            self.errors.append("dwell_time_phase calc: AcquisitionMatrixText not found")
            return None

        if self.__bandwidth_per_pixel_phase_encode is None:
            self.errors.append("dwell_time_phase calc: BandwidthPerPixelPhaseEncode not found")
            return None

        try:
            ast_num = self.__acquisition_matrix_text.find("*")
            am_num = self.__acquisition_matrix_text[:ast_num].rstrip('p')
            return str(1 / (float(self.__bandwidth_per_pixel_phase_encode) * float(am_num)))

        except (ValueError, TypeError) as e:
            self.errors.append("dwell_time_phase calc: " + e)
            self.errors.append("dwell_time_phase calc: AcquisitionMatrixText: " + self.__acquisition_matrix_text)
            self.errors.append(
                "dwell_time_phase calc: BandwidthPerPixelPhaseEncode: " + self.__bandwidth_per_pixel_phase_encode)
            return None

    def get_coil_for_gradient2(self) -> Optional[str]:
        if self.__coil_for_gradient2 is None:
            self.errors.append("coil_for_gradient2: not found")
            return None

        return self.__coil_for_gradient2

    def get_parallel_factor(self) -> Optional[str]:
        if self.__parallel_factor is None:
            self.errors.append("parallel_factor: not found")
            return None

        return self.__parallel_factor

    def get_multiband_factor(self) -> Optional[str]:
        if self.__multiband_factor is None:
            self.errors.append("multiband_factor: not found")
            return None

        return self.__multiband_factor

    def get_system(self) -> Optional[str]:
        if self.__system is None:
            self.errors.append("system: not found")
            return None

        return self.__system

    def get_fl_reference_amplitude(self) -> Optional[str]:
        if self.__fl_reference_amplitude is None:
            self.errors.append("flReferenceAmplitude: not found")
            return None
        return self.__fl_reference_amplitude

    def get_uc_flip_angle_mode(self) -> Optional[str]:
        if self.__uc_flip_angle_mode is None:
            self.errors.append("ucFlipAngleMode: not found")
            return None
        return self.__uc_flip_angle_mode

    def get_phase_partial_fourier(self) -> Optional[str]:
        if self.__phase_partial_fourier is None:
            self.errors.append("phasePartialFourier: not found")
            return None
        if self.__phase_partial_fourier not in self.__partial_fourier_dict:
            self.errors.append("phasePartialFourier: Value not registered in dict")
            return None
        return self.__partial_fourier_dict[self.__phase_partial_fourier]

    def get_slice_partial_fourier(self) -> Optional[str]:
        if self.__slice_partial_fourier is None:
            self.errors.append("slicePartialFourier: not found")
            return None
        if self.__slice_partial_fourier not in self.__partial_fourier_dict:
            self.errors.append("slicePartialFourier: Value not registered in dict")
            return None
        return self.__partial_fourier_dict[self.__slice_partial_fourier]

    def get_ascii_data_val(self, key: str) -> Optional[str]:
        if self.__ascii_data is not None and key in self.__ascii_data:
            return self.__ascii_data[key]
        else:
            self.errors.append(key + "(ascii_data)): not found")

    def get_ascii_data(self, raw_string: str) -> Optional[dict]:

        m = re.findall(r"((### ASCCONV BEGIN)(.*?)(###\\n))(.*?)(\\n### ASCCONV END ###)", raw_string)
        if len(m) == 0 or m[0][4] is None:
            self.errors.append("ascconv: can not find")
            return None

        tmp = m[0]  # 1つめにHITしたものを利用します。
        ascconv = re.sub(r'\\n', "\n", tmp[4], 0, re.MULTILINE)
        ascconv = re.sub(r'\\t', "", ascconv, 0, re.MULTILINE)

        result = {}
        for line in ascconv.splitlines():
            tmp = line.split(r"=")
            if len(tmp) == 2:
                result[tmp[0].strip(" ").strip('"')] = tmp[1].strip(" ").strip('"')
        return result

    def get_directions(self) -> dict:
        res = {
            "Read.direction": None,
            "Phase.direction": None,
            "Slice.direction": None,
        }

        # check
        if self.__in_plane_phase_encodeing_direction is None:
            self.errors.append("directions calc: InPlanePhaseEncodingDirection : not found")
            return res

        if self.__image_orientation_patient is None:
            self.errors.append("directions calc: ImageOrientationPatient : not found")
            return res

        if self.__phase_encoding_direction_positive is None:
            self.errors.append("directions calc: phase_encoding_direction_positive : not found")
            return res

        if int(self.__phase_encoding_direction_positive) == 1:
            l_phase_encoding_direction_sign = 1
        elif int(self.__phase_encoding_direction_positive) == 0:
            l_phase_encoding_direction_sign = -1
        else:
            self.errors.append("directions calc: phase_encoding_direction_positive :  value error")
            return res

        ###############################
        # phase direction
        ###############################
        if self.__in_plane_phase_encodeing_direction == "ROW":
            d_phase_encoding_vector = self.__image_orientation_patient[0:3]
        elif self.__in_plane_phase_encodeing_direction == "COL" or self.__in_plane_phase_encodeing_direction[:3] == "COL":
            d_phase_encoding_vector = self.__image_orientation_patient[3:6]
        else:
            self.errors.append("directions calc: ImageOrientationPatient unexpected value")
            return res

        # abs
        abs_phase_ary = list(map(abs, d_phase_encoding_vector))
        max_abs_phase_val = max(abs_phase_ary)
        phase_index_list = [i for i, x in enumerate(abs_phase_ary) if x == max_abs_phase_val]
        phase_index = str((phase_index_list[0] + 1) * l_phase_encoding_direction_sign)

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
            (self.__image_orientation_patient[1] * self.__image_orientation_patient[5]) -
            (self.__image_orientation_patient[2] * self.__image_orientation_patient[4]),
            (self.__image_orientation_patient[2] * self.__image_orientation_patient[3]) -
            (self.__image_orientation_patient[0] * self.__image_orientation_patient[5]),
            (self.__image_orientation_patient[0] * self.__image_orientation_patient[4]) -
            (self.__image_orientation_patient[1] * self.__image_orientation_patient[3])
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

        return {
            "Read.direction": readout_dic[readout_index]["val"] or None,
            "Phase.direction": phase_dic[phase_index]["val"] or None,
            "Slice.direction": slice_dic[slice_index]["val"] or None,
        }

    def get_mri_identifier(self) -> Optional[str]:
        return self.__mri_identifier


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
        print("{}: {}".format("DwelltimeRead", k.get_dwell_time_read() or "None"))
        print("{}: {}".format("DwelltimePhase", k.get_dwell_time_phase() or "None"))
        directions = k.get_directions()
        for key, val in directions.items():
            print("{}: {}".format(key, val or "None"))
        print("{}: {}".format("flReferenceAmplitude", k.get_fl_reference_amplitude() or "None"))
        print("{}: {}".format("ParallelFactor", k.get_parallel_factor() or "None"))
        print("{}: {}".format("MultibandFactor", k.get_multiband_factor() or "None"))
        print("{}: {}".format("ucFlipAngleMode", k.get_uc_flip_angle_mode() or "None"))
        print("{}: {}".format("PhasePartialFourier", k.get_phase_partial_fourier() or "None"))
        print("{}: {}".format("SlicePartialFourier", k.get_slice_partial_fourier() or "None"))

        if k.errors:
            for val in k.errors:
                print("  failure > " + val)

    except InvalidDicomError:
        print(args.dicomFullPath + ' :can not read file')
        exit()
