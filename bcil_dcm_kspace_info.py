#!/usr/bin/python3
# coding:utf-8
import warnings
import re
import decimal
from typing import Optional, NoReturn, Union
import pydicom
import os
from pydicom.errors import InvalidDicomError
from collections import namedtuple
import bcil_dcm_convert_logger


class BcilDcmKspaceInfo:

    path: Optional[str] = None
    ds: Optional[pydicom.dataset.FileDataset] = None
    input: Optional[tuple] = None
    output: Optional[tuple] = None
    ascii_data = None
    mri_identifier = None

    input_keys: list = [
        "real_dwell_time",
        "acquisition_matrix_text",
        "bandwidth_per_pixel_phase_encode",
        "phase_encoding_direction_positive",
        "gradient",
        "parallel_factor",
        "multiband_factor",
        "system",
        "fl_reference_amplitude",
        "uc_flip_angle_mode",
        "phase_partial_fourier",
        "slice_partial_fourier",
        "in_plane_phase_encodeing_direction",
        "image_orientation_patient",
    ]
    output_keys: list = [
        "mri_identifier",
        "gradient",
        "system",
        "dwelltime_read",
        "dwelltime_phase",
        "read_direction",
        "phase_direction",
        "slice_direction",
        "fl_reference_amplitude",
        "parallel_factor",
        "multiband_factor",
        "uc_flip_angle_mode",  # extended only
        "phase_partial_fourier",
        "slice_partial_fourier",
    ]

    def __init__(self, file_path: str):

        self.path = str(os.path.abspath(file_path))
        if os.path.exists(self.path) and os.path.isfile(self.path):
            try:
                self.ds = pydicom.read_file(self.path)
            except Exception as e:
                print(self.path + " failre. " + str(e))
                exit(1)

        # console logger
        self.logger = bcil_dcm_convert_logger.get_stream_logger(
            identifier=bcil_dcm_convert_logger.get_random_id("", 15), name="bcil_dcm_kspace_info")

    def setup_file_logger(self, file_log_path) -> NoReturn:
        self.logger = bcil_dcm_convert_logger.disposal_logger(self.logger)  # console logger clear
        # file logger
        self.logger = bcil_dcm_convert_logger.get_file_logger(
            path=file_log_path, identifier=bcil_dcm_convert_logger.get_random_id("", 15), name="bcil_dcm_kspace_info")
        self.logger.info("bcil_dcm_kspace_info.py file=" + self.path)

    def main(self) -> NoReturn:
        try:
            if self.ds is None:
                self.logger.critical("Error: invalid path." + self.path)
                exit(1)

            manufacturer = self.ds["0x00080070"].value if "0x00080070" in self.ds else None
            if 'SIEMENS' not in manufacturer.upper():
                # Siemensのみ対応
                self.logger.error("Error: data is not from Siemens MRI")
                exit(0)

            self.set_mri_identifier()
            self.set_input_val()
            self.gen_output_tuple()

        except Exception as e:
            self.logger.error(str(e))
        finally:
            self.logger = bcil_dcm_convert_logger.disposal_logger(self.logger)  # logger clear

    def set_mri_identifier(self) -> NoReturn:
        # mriの種類を判定する。
        self.mri_identifier = ""  # XA以外
        if "SoftwareVersions" in self.ds and "XA" in self.ds.SoftwareVersions:
            if "MediaStorageSOPClassUID" in self.ds.file_meta:
                if self.ds.file_meta.MediaStorageSOPClassUID == "1.2.840.10008.5.1.4.1.1.4.1":
                    self.mri_identifier = "extended"  # Enhanced MR Image IOD
                elif self.ds.file_meta.MediaStorageSOPClassUID == "1.2.840.10008.5.1.4.1.1.4":
                    self.mri_identifier = "interoperatabillity"
                elif self.ds.file_meta.MediaStorageSOPClassUID == "1.2.840.10008.5.1.4.1.1.4.3":
                    self.mri_identifier = "extended"  # Enhanced MR Color Image IOD

    def set_input_val(self) -> NoReturn:
        bcil_kspace_info_input = namedtuple("bcil_kspace_info_input", " ".join(self.input_keys))

        if self.mri_identifier == "extended":
            self.set_ascii_txt(["0x52009229", "0x002110fe", "0x00211019"])

            real_dwell_time = self.get_ascii_val("real_dwell_time", "sRXSPEC.alDwellTime[0]")
            acquisition_matrix_text = \
                self.get_ds_val("acquisition_matrix_text", ["0x52009230", "0x002111fe", "0x00211158"])
            bandwidth_per_pixel_phase_encode = \
                self.get_ds_val("bandwidth_per_pixel_phase_encode", ["0x52009230", "0x002111fe", "0x00211153"])
            phase_encoding_direction_positive = \
                self.get_ds_val("phase_encoding_direction_positive", ["0x52009230", "0x002111fe", "0x0021111c"])
            gradient = self.get_ds_val("gradient", ["0x52009229", "0x002110fe", "0x00211033"])

            parallel_factor = self.get_ascii_val("parallel_factor", "sPat.lAccelFactPE")
            multiband_factor = self.get_ascii_val("multiband_factor", "sWipMemBlock.alFree[13]")
            system = self.get_ds_val("system", ["SoftwareVersions"])
            fl_reference_amplitude = \
                self.get_ascii_val("fl_reference_amplitude", "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude")
            uc_flip_angle_mode = self.get_ascii_val("uc_flip_angle_mode", "ucFlipAngleMode")
            phase_partial_fourier = self.get_ascii_val("phase_partial_fourier", "sKSpace.ucPhasePartialFourier")
            slice_partial_fourier = self.get_ascii_val("slice_partial_fourier", "sKSpace.ucSlicePartialFourier")
            in_plane_phase_encodeing_direction = \
                self.get_ds_val("in_plane_phase_encodeing_direction", ["0x52009229", "0x00189125", "0x00181312"])
            image_orientation_patient = \
                self.get_ds_val("image_orientation_patient", ["0x52009230", "0x00209116", "0x00200037"], "list")

        elif self.mri_identifier == "interoperatabillity":
            self.set_ascii_txt(["0x00211019"])

            real_dwell_time = self.get_ds_val("real_dwell_time", ["0x00211142"])
            acquisition_matrix_text = self.get_ds_val("acquisition_matrix_text", ["0x00211158"])
            bandwidth_per_pixel_phase_encode = self.get_ds_val("bandwidth_per_pixel_phase_encode", ["0x00211153"])
            phase_encoding_direction_positive = self.get_ds_val("phase_encoding_direction_positive", ["0x0021111c"])
            gradient = self.get_ds_val("gradient", ["0x00211033"])

            parallel_factor = self.get_ascii_val("parallel_factor", "sPat.lAccelFactPE")
            multiband_factor = self.get_ds_val("multiband_factor", ["0x00211156"])
            system = self.get_ds_val("system", ["SoftwareVersions"])
            fl_reference_amplitude = \
                self.get_ascii_val("fl_reference_amplitude", "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude")
            uc_flip_angle_mode = self.get_ascii_val("uc_flip_angle_mode", "ucFlipAngleMode")
            phase_partial_fourier = self.get_ascii_val("phase_partial_fourier", "sKSpace.ucPhasePartialFourier")
            slice_partial_fourier = self.get_ascii_val("slice_partial_fourier", "sKSpace.ucSlicePartialFourier")
            in_plane_phase_encodeing_direction = \
                self.get_ds_val("in_plane_phase_encodeing_direction", ["InPlanePhaseEncodingDirection"])
            image_orientation_patient = \
                self.get_ds_val("image_orientation_patient", ["ImageOrientationPatient"], "list")

        else:
            self.set_ascii_txt(["0x00291020"])

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from nibabel.nicom.csareader import CSAReadError
                import nibabel.nicom.csareader as c
                try:
                    err_str = "Warning: not found {}. no {}: {}"
                    csa_img_data = c.get_csa_header(self.ds)
                    if csa_img_data:
                        real_dwell_time = c.get_scalar(csa_img_data, "RealDwellTime")
                        if real_dwell_time is None:
                            self.logger.warning(err_str.format("real_dwell_time", "RealDwellTime", "csa_img_data"))

                        acquisition_matrix_text = c.get_acq_mat_txt(csa_img_data)
                        if acquisition_matrix_text is None:
                            self.logger.warning(err_str.format("acquisition_matrix_text", "AcquisitionMatrixText", "csa_img_data"))

                        bandwidth_per_pixel_phase_encode = c.get_scalar(csa_img_data, "BandwidthPerPixelPhaseEncode")
                        if bandwidth_per_pixel_phase_encode is None:
                            self.logger.warning(err_str.format("bandwidth_per_pixel_phase_encode", "BandwidthPerPixelPhaseEncode", "csa_img_data"))

                        phase_encoding_direction_positive = c.get_scalar(csa_img_data, "PhaseEncodingDirectionPositive")
                        if phase_encoding_direction_positive is None:
                            self.logger.warning(err_str.format("phase_encoding_direction_positive", "PhaseEncodingDirectionPositive", "csa_img_data"))
                    else:
                        real_dwell_time = acquisition_matrix_text = bandwidth_per_pixel_phase_encode = phase_encoding_direction_positive = None
                        self.logger.warning(
                            "Warning: not found csa_img_data. cannot get real_dwell_time, acquisition_matrix_text, "
                            "bandwidth_per_pixel_phase_encode, phase_encoding_direction_positive")

                    csa_srs_data = c.get_csa_header(self.ds, 'series')
                    if csa_srs_data:
                        gradient = c.get_scalar(csa_srs_data, "CoilForGradient2")
                        if gradient is None:
                            self.logger.warning(err_str.format("gradient", "CoilForGradient2", "csa_srs_data"))
                    else:
                        gradient = None
                        self.logger.warning("Warning: not found csa_srs_data. cannot get gradient")

                except CSAReadError as e:
                    self.logger.error("Error: CSAReadError, " + str(e))
                    exit(1)

                parallel_factor = self.get_ascii_val("parallel_factor", "sPat.lAccelFactPE")
                multiband_factor = self.get_ascii_val("multiband_factor", "sWipMemBlock.alFree[13]")
                system = self.get_ascii_val("system", "sProtConsistencyInfo.tBaselineString")
                fl_reference_amplitude = \
                    self.get_ascii_val("fl_reference_amplitude", "sTXSPEC.asNucleusInfo[0].flReferenceAmplitude")
                uc_flip_angle_mode = None
                phase_partial_fourier = self.get_ascii_val("phase_partial_fourier", "sKSpace.ucPhasePartialFourier")
                slice_partial_fourier = self.get_ascii_val("slice_partial_fourier", "sKSpace.ucSlicePartialFourier")
                in_plane_phase_encodeing_direction = \
                    self.get_ds_val("in_plane_phase_encodeing_direction", ["InPlanePhaseEncodingDirection"])
                image_orientation_patient = \
                    self.get_ds_val("image_orientation_patient", ["ImageOrientationPatient"], "list")

        self.input = bcil_kspace_info_input(
            real_dwell_time,
            acquisition_matrix_text,
            bandwidth_per_pixel_phase_encode,
            phase_encoding_direction_positive,
            gradient,
            parallel_factor,
            multiband_factor,
            system,
            fl_reference_amplitude,
            uc_flip_angle_mode,
            phase_partial_fourier,
            slice_partial_fourier,
            in_plane_phase_encodeing_direction,
            image_orientation_patient
        )

    def get_ascii_val(self, name: str, key: str) -> Optional[str]:
        if self.ascii_data is not None and key in self.ascii_data:
            return str(self.ascii_data[key])
        self.logger.warning("Warning: not found {}. no {} in ascii text.".format(name, key))
        return None

    def get_ds_val(self, name: str, keys: list, type_str: str = "str") -> Union[list, str]:
        count = 1
        t = self.ds.copy()
        for key in keys:
            if key in t:
                if type(t[key].value) == pydicom.sequence.Sequence:
                    t = t[key].value[0]
                else:
                    t = t[key].value
                count += 1
            else:
                search = list(map(
                    lambda s: "(" + s[2:6] + "," + s[6:] + ")" if len(s) == 10 and s[:2] == "0x" else s, keys))
                self.logger.warning("Warning: not found {}. no {} in dcm header .".format(name, "-".join(search)))
                return None
        if type_str == "list":
            return list(t)
        else:
            return str(t)

    def gen_output_tuple(self) -> tuple:
        bcil_kspace_info_output = namedtuple("bcil_kspace_info_output", " ".join(self.output_keys))

        mri_identifier = self.mri_identifier

        gradient = self.input.gradient
        system = self.input.system
        dwelltime_read = self.gen_dwell_time_read()
        dwelltime_phase = self.gen_dwell_time_phase()

        d = self.gen_directions()
        read_direction = d["Read.direction"]
        phase_direction = d["Phase.direction"]
        slice_direction = d["Slice.direction"]

        fl_reference_amplitude = self.input.fl_reference_amplitude
        parallel_factor = self.input.parallel_factor
        multiband_factor = self.input.multiband_factor
        uc_flip_angle_mode = self.input.uc_flip_angle_mode
        phase_partial_fourier = self.gen_partial_fourier("phase_partial_fourier", self.input.phase_partial_fourier)
        slice_partial_fourier = self.gen_partial_fourier("slice_partial_fourier", self.input.slice_partial_fourier)

        self.output = bcil_kspace_info_output(
            mri_identifier,
            gradient,
            system,
            dwelltime_read,
            dwelltime_phase,
            read_direction,
            phase_direction,
            slice_direction,
            fl_reference_amplitude,
            parallel_factor,
            multiband_factor,
            uc_flip_angle_mode,
            phase_partial_fourier,
            slice_partial_fourier,
        )

    def gen_dwell_time_read(self) -> str:
        dtr = None
        if self.input.real_dwell_time is None:
            self.logger.warning("Warning: cannot get dwell_time_read. (required: real_dwell_time)")
            return None
        try:
            dtr = str(decimal.Decimal(int(self.input.real_dwell_time)) / decimal.Decimal(1000000000))
            dtr = dtr.rstrip('0')
        except Exception as e:
            self.logger.warning("Warning: cannot get dwell_time_read. " + str(e))
        return dtr

    def gen_dwell_time_phase(self) -> str:
        dtp = None
        err_str = "Warning: cannot get dwell_time_phase. "
        if self.input.acquisition_matrix_text is None or self.input.bandwidth_per_pixel_phase_encode is None:
            self.logger.warning(err_str + "(required: acquisition_matrix_text, bandwidth_per_pixel_phase_encode)")
            return dtp
        try:
            ast_num = self.input.acquisition_matrix_text.find("*")
            am_num = self.input.acquisition_matrix_text[:ast_num].rstrip('p')
            dtp = str(1 / (float(self.input.bandwidth_per_pixel_phase_encode) * float(am_num)))

        except (ValueError, TypeError) as e:
            self.logger.error(err_str + str(e))
            dtp = None
        return dtp

    def gen_partial_fourier(self, name: str, val: Optional[str]) -> Optional[str]:

        if val is None:
            self.logger.warning("Warning: cannot get {}. no value.".format(name))
            return

        partial_fourier_dict = {
            "16": "OFF",
            "8": " 7/8",
            "4": " 6/8",
            "2": " 5/8",
            "1": " 4/8",
        }
        if val in partial_fourier_dict:
            return partial_fourier_dict[val]

        self.logger.warning("Warning: cannot get {}. value invalid {}. (1 or 2 or 4 or 8 or 16 valid. )".format(name, val))
        return None

    def gen_directions(self) -> dict:
        res = {
            "Read.direction": None,
            "Phase.direction": None,
            "Slice.direction": None,
        }

        err_str = "Warning: cannot get directions. "

        # check
        if self.input.in_plane_phase_encodeing_direction is None or self.input.image_orientation_patient is None or self.input.phase_encoding_direction_positive is None:
            self.logger.warning(err_str + "(required: in_plane_phase_encodeing_direction, "
                                          "image_orientation_patient, phase_encoding_direction_positive)")
            return res

        if int(self.input.phase_encoding_direction_positive) == 1:
            l_phase_encoding_direction_sign = 1
        elif int(self.input.phase_encoding_direction_positive) == 0:
            l_phase_encoding_direction_sign = -1
        else:
            self.logger.warning(
                err_str + "phase_encoding_direction_positive value invalid, "
                          "{} ( 1 or -1 or 0 is valid.)".format(self.input.phase_encoding_direction_positive))
            return res

        ###############################
        # phase direction
        ###############################
        if self.input.in_plane_phase_encodeing_direction == "ROW":
            d_phase_encoding_vector = self.input.image_orientation_patient[0:3]
        elif self.input.in_plane_phase_encodeing_direction == "COL" or \
                self.input.in_plane_phase_encodeing_direction[:3] == "COL":
            d_phase_encoding_vector = self.input.image_orientation_patient[3:6]
        else:
            self.logger.warning(err_str + "image_orientation_patient value invalid, {} ( COL or ROW is valid.)".
                                format(self.input.in_plane_phase_encodeing_direction))
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
            (self.input.image_orientation_patient[1] * self.input.image_orientation_patient[5]) -
            (self.input.image_orientation_patient[2] * self.input.image_orientation_patient[4]),
            (self.input.image_orientation_patient[2] * self.input.image_orientation_patient[3]) -
            (self.input.image_orientation_patient[0] * self.input.image_orientation_patient[5]),
            (self.input.image_orientation_patient[0] * self.input.image_orientation_patient[4]) -
            (self.input.image_orientation_patient[1] * self.input.image_orientation_patient[3])
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

    def set_ascii_txt(self, place: list) -> NoReturn:

        raw_string = self.get_ds_val("ascii_text", place)
        if raw_string is not None:
            try:
                m = re.findall(r"((### ASCCONV BEGIN)(.*?)(###\\n))(.*?)(\\n### ASCCONV END ###)", raw_string)
                if len(m) == 0 or m[0][4] is not None:

                    tmp = m[0]  # 1つめにHITしたものを利用します。
                    ascconv = re.sub(r'\\n', "\n", tmp[4], 0, re.MULTILINE)
                    ascconv = re.sub(r'\\t', "", ascconv, 0, re.MULTILINE)

                    result = {}
                    for line in ascconv.splitlines():
                        tmp = line.split(r"=")
                        if len(tmp) == 2:
                            result[tmp[0].strip(" ").strip('"')] = tmp[1].strip(" ").strip('"')
                    self.ascii_data = result
            except Exception as e:
                self.logger.error("Error: cannot get ascii text. " + str(e))


if __name__ == '__main__':
    from argparse import ArgumentParser

    usage = \
        "\n\n" \
        "  ex). $ python3 bcil_dcm_kspace_info.py <DICOM path>\n" \
        "\n\n" \
        "".format(__file__)
    ap = ArgumentParser(usage=usage)
    ap.add_argument('dcm_path', type=str)
    args = ap.parse_args()

    try:
        k = BcilDcmKspaceInfo(args.dcm_path)
        k.main()

        print(args.dcm_path)
        print("{}: {}".format("mri_identifier", k.output.mri_identifier))
        print("{}: {}".format("Gradient", k.output.gradient))
        print("{}: {}".format("System", k.output.system))
        print("{}: {}".format("DwelltimeRead", k.output.dwelltime_read))
        print("{}: {}".format("DwelltimePhase", k.output.dwelltime_phase))

        print("{}: {}".format("Read.direction", k.output.read_direction))
        print("{}: {}".format("Phase.direction", k.output.phase_direction))
        print("{}: {}".format("Slice.direction", k.output.slice_direction))

        print("{}: {}".format("flReferenceAmplitude", k.output.fl_reference_amplitude))
        print("{}: {}".format("ParallelFactor", k.output.parallel_factor))
        print("{}: {}".format("MultibandFactor", k.output.multiband_factor))
        print("{}: {}".format("ucFlipAngleMode", k.output.uc_flip_angle_mode))
        print("{}: {}".format("PhasePartialFourier", k.output.phase_partial_fourier))
        print("{}: {}".format("SlicePartialFourier", k.output.slice_partial_fourier))

    except Exception as e:
        print(str(e))
        exit()
