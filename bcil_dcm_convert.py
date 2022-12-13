#!/usr/bin/python3
# coding:utf-8
from bcil_dcm_kspace_info import BcilDcmKspaceInfo
import glob
import logging
import os
import pandas as pd
import platform
import pydicom
from pydicom.errors import InvalidDicomError
import re
import shutil
import subprocess
import sys
import tqdm
from typing import Optional, Final, NoReturn
import zipfile
import datetime


class BcilDcmConvert:

    init_error = True

    __version__: Final[str] = "3.0.0"
    last_update: Final[str] = "20220405001"

    DCM_2_NIIX_CMD: Final[str] = "dcm2niix"
    DCM_2_NAMING_RULE: Final[str] = "%s_%p"

    def __init__(self,
                 dcm_dir: str,
                 save_parent_dir: str,
                 create_nifti: bool = True,
                 overwrite: int = 0,
                 subject_name: Optional[str] = None,
                 display_progress: bool = False,
                 gz: bool = False,
                 unzip_dir: [str] = None):

        # args
        # *unzip dir
        if unzip_dir is not None and len(unzip_dir) > 0:
            self.unzip_dir = self.input_path_check(unzip_dir, "unzip_dir")
            self.unzip_dir = self.unzip_dir + "bcil_dcm_convert_tmp" + os.sep
        else:
            self.unzip_dir = os.getcwd() + os.sep + "bcil_dcm_convert_tmp" + os.sep

        # *save parent dir
        parent_dir = self.input_path_check(save_parent_dir, "save_parent_dir")

        # *src dicom dir
        if zipfile.is_zipfile(dcm_dir):
            self.dcm_dir = self.unzip_dcm_dir(dcm_dir)
        else:
            self.dcm_dir = self.input_path_check(dcm_dir, "dcm_dir")

        # subject name alias
        self.dir_name = os.path.basename(os.path.dirname(self.dcm_dir))
        if subject_name is not None and len(subject_name) > 0:
            self.dir_name = subject_name
        subject_dir_full_path = parent_dir + self.dir_name + os.sep

        self.create_nifti = create_nifti
        self.overwrite = overwrite
        self.un_display_progress = not display_progress
        self.gz = gz

        # path
        self.save_data_dir_path: Final[str] = subject_dir_full_path + "RawData"
        self.study_csv_path: Final[str] = self.save_data_dir_path + os.sep + "Studyinfo.csv"
        self.series_csv_path: Final[str] = self.save_data_dir_path + os.sep + "Seriesinfo.csv"
        self.dicom_list_path: Final[str] = self.save_data_dir_path + os.sep + "DICOMlist.txt"
        self.nifti_dir_path: Final[str] = self.save_data_dir_path + os.sep + "NIFTI"
        self.ex_dicom_dir_path: Final[str] = self.save_data_dir_path + os.sep + "DICOM"
        save_log_dir_path: Final[str] = subject_dir_full_path + "logs"
        self.op_log_path: Final[str] = save_log_dir_path + os.sep + "convert.log"

        # log
        if not os.path.exists(save_log_dir_path):
            os.makedirs(save_log_dir_path, exist_ok=True)
            os.chmod(save_log_dir_path, 0o755)
        self.logger = None
        self.setup_logger()

        # flg
        self.init_error = False

    @staticmethod
    def input_path_check(path: str, path_name: str) -> str:
        abs_path = str(os.path.abspath(path))
        if not os.path.isdir(abs_path) or not os.path.exists(abs_path):
            print(path_name + " not found. (" + path + ")")
            exit()
        abs_path += "" if abs_path.endswith(os.sep) else os.sep
        return abs_path

    def unzip_dcm_dir(self, dcm_dir: str) -> str:
        try:
            with zipfile.ZipFile(dcm_dir, 'r') as zf:
                if not os.path.exists(self.unzip_dir):
                    os.makedirs(self.unzip_dir, exist_ok=True)
                zf.extractall(self.unzip_dir)
            return self.unzip_dir + os.path.splitext(os.path.basename(dcm_dir))[0] + os.sep
        except Exception as e:
            print("unzip failure. (" + dcm_dir + ") exceiption:" + e)
            exit()

    def main(self) -> bool:

        if self.init_error is True:
            self.logger.debug("init error.")
            exit()

        self.logger.debug("### main start ###")

        # overwrite check
        if (self.overwrite == 0) and os.path.exists(self.save_data_dir_path):
            self.logger.error(self.save_data_dir_path + ": already exist. do not overwrite.")
            exit()

        # read dcm
        self.logger.debug("##### get_dcm_list #####")
        dcm_list = self.get_dcm_list()
        self.logger.debug("##### read_dcm_header #####")
        (study_df, series_df, used_dcm_list) = self.read_dcm_header(dcm_list)

        # mkdir
        if not os.path.exists(self.save_data_dir_path):
            os.makedirs(self.save_data_dir_path, exist_ok=True)
            os.chmod(self.save_data_dir_path, 0o755)

        # save files
        self.logger.debug("##### save files #####")
        series_df = self.save_ex_dcm(series_df)
        if self.create_nifti is True:
            series_df = self.save_nifti(series_df)
        self.save_study_csv(study_df)
        self.save_series_csv(series_df)
        self.save_dicom_file_name_list(used_dcm_list)

        self.logger.debug("##### permission_modify #####")
        self.permission_modify()

        # unzip dir
        self.logger.debug("##### delete unzip dir #####")
        self.delete_unzip_dir()

        self.logger.debug("### main end ###")
        return True

    #############################################

    def get_dcm_list(self) -> list:
        # search dcm files > create file list
        regex = r".*\.(ima|dcm|dic|dc3|dicom)"
        search_src = self.dcm_dir + r"**"
        files = [f for f in glob.glob(search_src, recursive=True) if re.search(regex, f, re.IGNORECASE)]
        add_files = [f for f in glob.glob(search_src, recursive=True) if re.search(r"\d{8}$", f)]
        if (0 == len(files)) and (0 == len(add_files)):
            self.logger.error((self.dcm_dir + ": dcm file 0. (skip subject)"))
            exit()
        files.extend(add_files)
        files.sort()
        return files

    def read_dcm_header(self, dcm_list: list) -> tuple:

        study_dict = {
            "Patient Name": [],
            'Patient ID': [],
            "Patient's Birth date": [],
            "Patient's Sex": [],
            "Patient's Age": [],
            "Patient's Size": [],
            "Patient's Weight": [],
            "Patient's Position": [],
            'Study Date': [],
            'Study Description': [],
            'Requesting physician': [],
            'Station': [],
            'Manufacturer': [],
            "Model": [],
            'Institution': [],
            'System': [],
            "Gradient": [],
            "PatAUSJID": [],
            'StudyUID': [],
        }
        series_dict = {
            'Series Number': [],  # SeriesNumber
            'Time': [],  # SeriesTime
            'Description': [],  # SeriesDescription
            'Protocol': [],  # ProtocolName
            'Scanning Sequence': [],
            'Sequence Name': [],

            'TR[msec]': [],  # RepetitionTime
            'TE[msec]': [],  # EchoTime
            'TI[msec]': [],  # InversionTime
            'FA[degree]': [],  # FlipAngle

            'Matrix(phase*read)': [],
            'Pixel size[mm]': [],  # PixelSpacing
            'Slice thickness[mm]': [],
            'Number of averages': [],
            'Image Type': [],
            'DwelltimeRead': [],
            'DwelltimePhase': [],
            'Read.direction': [],
            'Phase.direction': [],
            'Slice.direction': [],
            "Patient Position": [],
            "flReferenceAmplitude": [],
            "Parallel factor": [],
            "Multi-band factor": [],
            "PhasePartialFourier": [],
            "SlicePartialFourier": [],

            'Example DICOM': [],
            'Series UID': [],  # SeriesInstanceUID
            'Study UID': [],
            'NIFTI in RawData': [],
            'NIFTI in BIDS': [],
        }
        used_dcm_list = []

        for index, file in tqdm.tqdm(enumerate(dcm_list), disable=self.un_display_progress, total=len(dcm_list),
                                     desc="read DCM [" + self.dir_name + "]", leave=True, ascii=True):
            if os.path.isdir(file):
                continue
            try:
                ds = pydicom.read_file(file)
            except InvalidDicomError:
                self.logger.debug(file + ':skip(can not read)')
                continue

            if 'PixelData' not in ds:
                self.logger.debug(file + ':skip(no image)')
                continue

            used_dcm_list.append(file)
            series_number = str(ds["0x00200011"].value)
            series_uid = str(ds["0x0020000e"].value)
            study_uid = str(ds["0x0020000d"].value)

            if series_uid in series_dict["Series UID"]:
                # series_uid が既出の場合は次へスキップ
                continue

            station_name = str(ds["0x00081010"].value) if "0x00081010" in ds else None
            manufacturer = str(ds["0x00080070"].value) if "0x00080070" in ds else None
            patient_position = str(ds["0x00185100"].value) if "0x00185100" in ds else None

            # csa data
            if 'SIEMENS' in manufacturer.upper():
                print(file)
                bdki = BcilDcmKspaceInfo(ds)
                directions = bdki.get_directions()
                system = bdki.get_system()
                gradient = bdki.get_coil_for_gradient2()
                dwelltime_read = bdki.get_dwell_time_read() or None
                dwelltime_phase = bdki.get_dwell_time_phase() or None
                read_direction = directions["Read.direction"] if "Read.direction" in directions else None
                phase_direction = directions["Phase.direction"] if "Phase.direction" in directions else None
                slice_direction = directions["Slice.direction"] if "Slice.direction" in directions else None
                fl_reference_amplitude = bdki.get_fl_reference_amplitude() or None
                parallel_factor = bdki.get_parallel_factor() or None
                multi_band_factor = bdki.get_multiband_factor() or None
                mri_identifier = bdki.get_mri_identifier() or ""  # "", vida, extend, interoperatabillity
                uc_flip_angleMode = bdki.get_uc_flip_angle_mode() or None
                phase_partial_fourier = bdki.get_phase_partial_fourier() or None
                slice_partial_fourier = bdki.get_slice_partial_fourier() or None
                if bdki.errors:
                    for er in bdki.errors:
                        self.logger.warning(file + ": " + er)
                del bdki
            else:
                system = None
                gradient = None
                dwelltime_read = None
                dwelltime_phase = None
                read_direction = None
                phase_direction = None
                slice_direction = None
                fl_reference_amplitude = None
                parallel_factor = None
                multi_band_factor = None
                mri_identifier = ""
                uc_flip_angleMode = None
                phase_partial_fourier = None
                slice_partial_fourier = None

            # series
            ttt = ds["0x00211153"].value if "0x00211153" in ds else "none"
            print(mri_identifier + "  " + file + "  " + str(ttt))

            variable_data = ""
            if mri_identifier == "extended":
                variable_data = self.get_variable_data_extended(ds)
                if uc_flip_angleMode == "16":
                    variable_data["FA"] = ""
            elif mri_identifier == "interoperatabillity":
                variable_data = self.get_variable_data_interoperatabillity(ds)
            else:
                variable_data = self.get_variable_data(ds)

            image_type_ary = ds["0x00080008"].value if "0x00080008" in ds else []

            series_dict["Series Number"].append(series_number)
            series_dict["Time"].append(ds["0x00080031"].value if "0x00080031" in ds else None)
            series_dict["Description"].append(ds["0x0008103e"].value if "0x0008103e" in ds else None)
            series_dict["Protocol"].append(ds["0x00181030"].value if "0x00181030" in ds else None)
            series_dict["Scanning Sequence"].append(variable_data['Scanning_Sequence'])
            series_dict["Sequence Name"].append(variable_data['Sequence_Name'])
            series_dict["TR[msec]"].append(variable_data['TR'])
            series_dict["TE[msec]"].append(variable_data['TE'])
            series_dict["TI[msec]"].append(variable_data['TI'])
            series_dict["FA[degree]"].append(variable_data['FA'])
            series_dict["Matrix(phase*read)"].append(variable_data['Matrix'])
            series_dict["Pixel size[mm]"].append(variable_data['Pixel_size'])
            series_dict["Slice thickness[mm]"].append(variable_data['Slice_thickness'])
            series_dict["Number of averages"].append(variable_data['Number_of_averages'])
            series_dict["Image Type"].append(' '.join(map(str, image_type_ary)))
            series_dict["DwelltimeRead"].append(dwelltime_read or "None")
            series_dict["DwelltimePhase"].append(dwelltime_phase or "None")
            series_dict["Patient Position"].append(patient_position or "None")
            series_dict["Read.direction"].append(read_direction or "None")
            series_dict["Phase.direction"].append(phase_direction or "None")
            series_dict["Slice.direction"].append(slice_direction or "None")
            series_dict["flReferenceAmplitude"].append(fl_reference_amplitude or "None")
            series_dict["Parallel factor"].append(parallel_factor or "None")
            series_dict["Multi-band factor"].append(multi_band_factor or "None")
            series_dict["PhasePartialFourier"].append(phase_partial_fourier or "None")
            series_dict["SlicePartialFourier"].append(slice_partial_fourier or "None")

            series_dict["Example DICOM"].append(file)
            series_dict["Series UID"].append(series_uid)
            series_dict["Study UID"].append(study_uid)
            series_dict["NIFTI in RawData"].append(None)
            series_dict["NIFTI in BIDS"].append(None)

            # study
            if study_uid not in study_dict["StudyUID"]:
                study_dict["Patient Name"].append(ds["0x00100010"].value if "0x00100010" in ds else None)
                study_dict["Patient ID"].append(ds["0x00100020"].value if "0x00100020" in ds else None)
                study_dict["Patient's Birth date"].append(ds["0x00100030"].value if "0x00100030" in ds else None)
                study_dict["Patient's Sex"].append(ds["0x00100040"].value if "0x00100040" in ds else None)
                study_dict["Patient's Age"].append(ds["0x00101010"].value if "0x00101010" in ds else None)
                study_dict["Patient's Size"].append(ds["0x00101020"].value if "0x00101020" in ds else None)
                study_dict["Patient's Weight"].append(ds["0x00101030"].value if "0x00101030" in ds else None)
                study_dict["Patient's Position"].append(patient_position)
                study_dict["Study Date"].append(ds["0x00080020"].value if "0x00080020" in ds else None)
                study_dict["Study Description"].append(ds["0x00081030"].value if "0x00081030" in ds else None)
                study_dict["Requesting physician"].append(ds["0x00321032"].value if "0x00321032" in ds else None)
                study_dict["Station"].append(station_name)
                study_dict["Manufacturer"].append(manufacturer)
                study_dict["Model"].append(ds["0x00081090"].value if "0x00081090" in ds else None)
                study_dict["Institution"].append(ds["0x00080080"].value if "0x00080080" in ds else None)
                study_dict["System"].append(system)
                study_dict["Gradient"].append(gradient)
                study_dict["StudyUID"].append(study_uid)
                study_dict["PatAUSJID"].append(ds["0xC0D30011"].value if "0xC0D30011" in ds else None)

        # study UID unique check
        self.unique_study_check(study_dict)

        return (
            pd.DataFrame.from_dict(study_dict).astype(str),
            pd.DataFrame.from_dict(series_dict).astype(str),
            used_dcm_list
        )

    @staticmethod
    def get_variable_data(ds):
        variable_data = {
            'Sequence_Name': ds["0x00180024"].value if "0x00180024" in ds else None,
            'TR': ds["0x00180080"].value if "0x00180080" in ds else "",
            'TE': ds["0x00180081"].value if "0x00180081" in ds else "",
            'TI': ds["0x00180082"].value if "0x00180082" in ds else "",
            'FA': ds["0x00181314"].value if "0x00181314" in ds else "",
            'Slice_thickness': ds["0x00180050"].value if "0x00180050" in ds else None,
            'Number_of_averages': ds["0x00180083"].value if "0x00180083" in ds else None,
            'Matrix': None,
            'Scanning_Sequence': "",
            'Pixel_size': "",
        }
        # Matrix
        if "0x0051100b" in ds and ds["0x0051100b"].value != "":
            matrix_val = ds["0x0051100b"].value
            if type(matrix_val) is bytes:
                matrix_val = matrix_val.decode("utf-8")
            elif type(matrix_val) is not str:
                matrix_val = str(matrix_val)  # GE?
            matrix_val = matrix_val.replace("[", "").replace("]", "")
            matrix_val = re.sub('[a-z]', '', matrix_val)
            variable_data['Matrix'] = matrix_val

        # Scanning Sequence
        if "0x00180020" in ds:
            variable_data['Scanning_Sequence'] = ''.join(map(str, ds["0x00180020"].value))
        # Pixel size
        if "0x00280030" in ds:
            variable_data['Pixel_size'] = ' '.join(map(str, ds["0x00280030"].value))

        return variable_data

    @staticmethod
    def get_variable_data_extended(ds):
        variable_data = {
            'Sequence_Name': ds["0x00189005"].value if "0x00189005" in ds else None,
            'TR': "",
            'TE': "",
            'TI': "",
            'FA': "",
            'Slice_thickness': None,
            'Number_of_averages': None,
            'Matrix': None,
            'Scanning_Sequence': "",
            'Pixel_size': "",
        }
        if "0x52009229" in ds:
            csa9229 = ds["0x52009229"].value[0]
            if "0x00189112" in csa9229:
                hdr00189112 = csa9229["0x00189112"].value[0]
                variable_data['TR'] = hdr00189112["0x00180080"].value if "0x00180080" in hdr00189112 else ""
                variable_data['FA'] = hdr00189112["0x00181314"].value if "0x00181314" in hdr00189112 else ""
            if "0x00189115" in csa9229:
                hdr00189115 = csa9229["0x00189115"].value[0]
                variable_data['TI'] = hdr00189115["0x00189079"].value if "0x00189079" in hdr00189115 else ""

        if "0x52009230" in ds:
            csa9230 = ds["0x52009230"].value[0]
            if "0x00289110" in csa9230:
                hdr00289110 = csa9230["0x00289110"].value[0]
                pixel_size_ary = hdr00289110["0x00280030"].value if "0x00280030" in hdr00289110 else ""
                variable_data['Pixel_size'] = ' '.join(map(str, pixel_size_ary))
                variable_data['Slice_thickness'] = hdr00289110["0x00180050"].value if "0x00180050" in hdr00289110 else None
            if "0x00189119" in csa9230:
                hdr00189119 = csa9230["0x00189119"].value[0]
                variable_data['Number_of_averages'] = hdr00189119["0x00180083"].value if "0x00180083" in hdr00189119 else None
            if "0x00189114" in csa9230:
                hdr00189114 = csa9230["0x00189114"].value[0]
                variable_data['TE'] = hdr00189114["0x00189082"].value if "0x00189082" in hdr00189114 else ""

        # Scanning Sequence
        if "0x00189008" in ds:
            if ds["0x00189008"].value == "GRADIENT":
                variable_data['Scanning_Sequence'] = variable_data['Scanning_Sequence'] + "GR "
            if ds["0x00189008"].value == "SPIN":
                variable_data['Scanning_Sequence'] = variable_data['Scanning_Sequence'] + "SE "
        if "0x00189018" in ds:
            if ds["0x00189018"].value == "YES":
                variable_data['Scanning_Sequence'] = variable_data['Scanning_Sequence'] + "EPI "

        # Matrix
        row = ds["0x00280010"].value if "0x00280010" in ds else None
        col = ds["0x00280011"].value if "0x00280011" in ds else None
        if row and row:
            matrix = str(row) + "*" + str(col) if row < col else str(col) + "*" + str(row)
            variable_data['Matrix'] = matrix
        return variable_data

    @staticmethod
    def get_variable_data_interoperatabillity(ds):
        variable_data = {
            'Sequence_Name': ds["0x00180024"].value if "0x00180024" in ds else None,
            'TR': ds["0x00180080"].value if "0x00180080" in ds else "",
            'TE': ds["0x00180081"].value if "0x00180081" in ds else "",
            'TI': ds["0x00180082"].value if "0x00180082" in ds else "", ### わからんやつ
            'FA': ds["0x00181314"].value if "0x00181314" in ds else "",
            'Slice_thickness': ds["0x00180050"].value if "0x00180050" in ds else None,
            'Number_of_averages': ds["0x00180083"].value if "0x00180083" in ds else None,
            'Matrix': None,
            'Scanning_Sequence': "",
            'Pixel_size': "",
        }
        # Matrix
        row = ds["0x00280010"].value if "0x00280010" in ds else None
        col = ds["0x00280011"].value if "0x00280011" in ds else None
        if row and row:
            matrix = str(row) + "*" + str(col) if row < col else str(col) + "*" + str(row)
            variable_data['Matrix'] = matrix

        # Scanning Sequence
        if "0x00180020" in ds:
            variable_data['Scanning_Sequence'] = '-'.join(map(str, ds["0x00180020"].value))
        # Pixel size
        if "0x00280030" in ds:
            variable_data['Pixel_size'] = ' '.join(map(str, ds["0x00280030"].value))

        return variable_data

    def save_ex_dcm(self, series_df: pd.DataFrame) -> pd.DataFrame:

        if not os.path.exists(self.ex_dicom_dir_path):
            os.makedirs(self.ex_dicom_dir_path, exist_ok=True)

        for index, item in series_df.iterrows():
            save_file_path = item['Example DICOM'].replace(self.dcm_dir, self.ex_dicom_dir_path + os.sep)
            os.makedirs(os.path.dirname(save_file_path), exist_ok=True)
            try:
                shutil.copy(item['Example DICOM'], save_file_path)
            except shutil.SameFileError as e:
                self.logger.error("save_example_dicom: failure: " + str(e))
                continue
            finally:
                # new_path = self.ex_dicom_dir_path + os.sep + os.path.basename(item['Example DICOM'])
                series_df.at[index, "Example DICOM"] = save_file_path

        return series_df

    def save_nifti(self, series_df: pd.DataFrame) -> pd.DataFrame:

        with tqdm.tqdm(disable=self.un_display_progress,
                       desc="converting DCM to NIFTI", total=100, leave=True, ascii=True) as nip:

            if os.path.exists(self.nifti_dir_path) is False:
                os.makedirs(self.nifti_dir_path, exist_ok=True)
            nip.update(1)

            cmd_ary = [
                self.DCM_2_NIIX_CMD,
                "-f",
                self.DCM_2_NAMING_RULE,
                "-w",
                "1" if (self.overwrite != 0) else "0",
                "-o", self.nifti_dir_path
            ]
            if self.gz is True:
                cmd_ary.append("-z")
                cmd_ary.append("y")
            cmd_ary.append(self.dcm_dir)
            try:
                subprocess.run(cmd_ary, stdout=subprocess.PIPE)
            except Exception as e:
                self.logger.error(("dcm2niix: failure:" + str(e)))

            nip.update(99)

        # 処理追加
        nifti_files = glob.glob(self.nifti_dir_path + os.sep + "*.nii")
        nifti_files.extend(glob.glob(self.nifti_dir_path + os.sep + "*.nii.gz"))

        for nifti in nifti_files:
            series_number = nifti.replace(self.nifti_dir_path + os.sep, "").split("_")[0]
            search = series_df.loc[(series_df['Series Number'] == series_number)]
            if len(search) > 0:
                idx = search.index[0]
                if series_df.at[idx, 'NIFTI in RawData'] == "None":
                    series_df.at[idx, 'NIFTI in RawData'] = nifti
                else:
                    series_df.at[idx, 'NIFTI in RawData'] += r" " + nifti

        return series_df

    def permission_modify(self) -> bool:
        # permission check & mod
        for file in glob.glob(self.save_data_dir_path + os.sep + r'**', recursive=True):
            os.chmod(file, 0o755)
        os.chmod(self.op_log_path, 0o755)
        return True

    #############################################

    def setup_logger(self):
        self.logger = logging.getLogger("bcil_dcm_convert." + self.dir_name + "." + datetime.datetime.now().isoformat())
        self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(filename=self.op_log_path, mode='a')
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)8s %(message)s"))
        self.logger.addHandler(fh)

        self.logger.info("/*** " + __name__ + " start ***/")
        self.logger.info("CMD: " + " ".join(sys.argv))
        self.logger.info("OS: " + platform.platform())
        self.logger.info("python: " + sys.version.replace("\n", ""))
        self.logger.info(__name__ + ":" + self.__version__ + " last update." + self.last_update)
        if self.create_nifti is True:
            try:
                res = subprocess.run([self.DCM_2_NIIX_CMD, "-v"], stdout=subprocess.PIPE)
                self.logger.info("dcm2niix: " + str(res.stdout.splitlines()[-1]))
            except Exception as e:
                self.logger.error("dcm2niix failure: " + str(e))
                exit(1)

    def unique_study_check(self, study_dict: dict) -> NoReturn:

        if len(study_dict["StudyUID"]) > 1:
            self.logger.error("multiple study UID error.")
            self.logger.error("found " + len(study_dict["StudyUID"]) + " study UID.")
            for std_uid in study_dict["StudyUID"]:
                self.logger.error("study UID:" + std_uid)
            exit()

        # overwrite: append (new study UID != old study UID)
        default_study_uid = None
        if (self.overwrite == 2) and os.path.exists(self.study_csv_path):
            tmp = pd.read_csv(self.study_csv_path, header=None, index_col=0)
            default_study_uid = tmp[1]["StudyUID"]  # get csv study UID

        if (default_study_uid is not None) and (default_study_uid != study_dict["StudyUID"][0]):
            self.logger.error("multiple study UID error.")
            self.logger.error("in RawData study UID: " + default_study_uid)
            self.logger.error("in dcm source study UID[" + study_dict["StudyUID"][0])
            exit()

    def save_study_csv(self, study_df: pd.DataFrame) -> NoReturn:
        if (self.overwrite == 2) and (os.path.exists(self.study_csv_path)):
            # 追記の場合 重複を削除して追記する
            tmp = pd.read_csv(self.study_csv_path, header=None, index_col=0)
            tmp = tmp.where(tmp.notnull(), None)
            study_df = pd.concat([study_df, tmp.T]).drop_duplicates(subset=['StudyUID'])
        study_df.T.to_csv(self.study_csv_path, header=False)

    def save_series_csv(self, series_df: pd.DataFrame) -> NoReturn:
        if (self.overwrite == 2) and (os.path.exists(self.series_csv_path)):
            # 追記の場合 重複を削除して追記する
            tmp = pd.read_csv(self.series_csv_path, index_col=0)
            tmp = tmp.where(tmp.notnull(), None)
            series_df = pd.concat([series_df, tmp]).drop_duplicates(subset=['Series UID', 'Study UID'])
        series_df["Series Number"] = series_df["Series Number"].astype('uint')
        series_df = series_df.sort_values(["Series Number"])
        series_df.to_csv(self.series_csv_path, index=False)

    def save_dicom_file_name_list(self, used_dcm_list: list) -> NoReturn:
        if (self.overwrite == 2) and (os.path.exists(self.dicom_list_path)):
            f = open(self.dicom_list_path, 'r')
            tmp = f.readlines()
            f.close()
            tmp.extend(used_dcm_list)
            used_dcm_list = set(tmp)
        with open(self.dicom_list_path, mode='w') as txt_file:
            txt_file.write('\n'.join(used_dcm_list))

    def delete_unzip_dir(self) -> NoReturn:
        if os.path.exists(self.unzip_dir):
            shutil.rmtree(self.unzip_dir)


if __name__ == '__main__':

    from argparse import ArgumentParser
    usage = \
        "\n\n" \
        "  ex). $ python3 bcil_dcm_convert.py [option(s)] <saveDir> <dcmDir>\n" \
        "\n" \
        "\n" \
        "".format(__file__)

    ap = ArgumentParser(usage=usage)
    # required
    ap.add_argument(
        'saveDir', type=str, help='path to study dir (parent dir) in which a new subject directory will be saved')
    ap.add_argument(
        'dcmDir', type=str, help='path to subject dir including DICOM files')

    # optional
    ap.add_argument('-p', '--progress', dest='progress', action='store_true', help='show progress bar')
    ap.add_argument('-n', '--no_nii', dest='no_nii', action='store_true', help='do not convert to NIFTI')
    ap.add_argument('-s', dest='subject_name', type=str,
                    help="give an alias to the subject directory", metavar="subject name")
    w_help_txt = "<num>   overwrite options (0:do not overwrite, 1:replace, 2:append, default is 0)"
    ap.add_argument('-w', dest='overwrite_behavior', type=int, help=w_help_txt, default=0, metavar="overwrite option")
    ap.add_argument('-z', '--gz', dest='gz', action='store_true',
                    help='compress NIFTI volumes with .gz (default is not compressed, and saved as .nii)')  # gzオプション
    u_help_txt = "path to unzip dir. unzipped files will be deleted after processing. default is current dir"
    ap.add_argument('-u', dest='unzip_dir', type=str, help=u_help_txt, metavar="unzip_dir_path")
    args = ap.parse_args()

    ###########################

    bc = BcilDcmConvert(
        dcm_dir=args.dcmDir,
        save_parent_dir=args.saveDir,
        create_nifti=not args.no_nii,
        overwrite=args.overwrite_behavior,
        subject_name=args.subject_name,
        display_progress=args.progress,
        gz=args.gz,
        unzip_dir=args.unzip_dir,
    )
    if bc.main() is True:
        print("complete!")

