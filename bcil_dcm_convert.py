#!/usr/bin/python3
# coding:utf-8
from bcil_dcm_kspace_info import BcilDcmKspaceInfo
import glob
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
from typing import Optional, Final, NoReturn, List
import zipfile
import datetime
from collections import namedtuple, Counter

import bcil_dcm_convert_logger
from bcil_dcm_convert_csv import SeriesCsvData, StudyCsvData, DcmCsvData


class BcilDcmConvert:

    init_error = True

    __version__: Final[str] = "3.1.2"
    last_update: Final[str] = "20230805001"

    DCM_2_NIIX_CMD: Final[str] = "dcm2niix"
    DCM_2_NAMING_RULE: Final[str] = "%s_%d"

    def __init__(self,
                 dcm_dir_list: List[str],
                 save_parent_dir: str,
                 create_nifti: bool = True,
                 overwrite: int = 0,
                 subject_name: Optional[str] = None,
                 gz: bool = False,
                 working_folder: [str] = None):

        self.dcm_dir_list = dcm_dir_list
        self.create_nifti = create_nifti
        self.overwrite = overwrite
        self.subject_name = subject_name
        self.gz = gz

        # data
        self.series = SeriesCsvData()
        self.study = StudyCsvData()
        self.dcm = DcmCsvData()

        # save parent dir
        self.parent_d = self.file_path_check(save_parent_dir, "<Folder to save>")
        # work dir
        work_d = self.parent_d
        if working_folder is not None:
            work_d = self.file_path_check(working_folder, "\<Folder to tmp\>")
        self.work_base_path = self.gen_work_base_path(work_d)
        self.work_path = self.gen_bdc_path(self.work_base_path.subject_d)
        self.dst_path = None

        # log start
        self.logger = self.setup_logger()
        self.console_logger = bcil_dcm_convert_logger.get_stream_logger(identifier=self.work_base_path.bdc_id)

        # path
        self.mkdir(self.work_path.raw_data_d)
        self.mkdir(self.work_path.dicom_d)

    @staticmethod
    def file_path_check(path: str, path_name:str) -> str:
        p = str(os.path.abspath(path))
        if not os.path.isdir(p):
            print(path_name + " not found. (" + path + ")")
            exit(1)
        if not os.path.exists(p):
            print(path_name + " is file. (" + path + ")")
            exit(1)
        p += "" if p.endswith(os.sep) else os.sep
        return p

    def setup_logger(self) -> bcil_dcm_convert_logger.Logger:
        try:
            os.makedirs(self.work_path.log_d, exist_ok=True)
            os.chmod(self.work_path.log_d, 0o755)
        except Exception as e:
            print("Unable to create folder at specified location. (" + self.work_path.log_d + ") " + str(e))
            exit(1)

        lg = bcil_dcm_convert_logger.get_file_logger(
            path=self.work_path.log_txt, identifier=self.work_base_path.bdc_id)
        lg.info("############# START BCIL_DCM_CONVERT #############")
        lg.info("CMD: " + " ".join(sys.argv))
        lg.info("OS: " + platform.platform())
        lg.info("Python: " + sys.version.replace("\n", ""))
        lg.info("BCIL_DCM_CONVERT: " + self.__version__ + " last update." + self.last_update)
        lg.info("work_subject_folder: " + self.work_path.subject_d)
        if self.create_nifti is True:
            try:
                res = subprocess.run([self.DCM_2_NIIX_CMD, "-v"], stdout=subprocess.PIPE)
                lg.info("dcm2niix: " + res.stdout.splitlines()[-1].decode('UTF-8'))
            except Exception as e:
                self.close("Error : dcm2niix test failure: " + str(e))
        return lg

    def close(self, message: str, exit_number: int = 1) -> NoReturn:

        if self.console_logger is not None:
            if exit_number == 1:
                self.console_logger.critical(message)
            else:
                self.console_logger.info(message)
            self.console_logger = bcil_dcm_convert_logger.disposal_logger(self.console_logger)  # del logger
        if self.logger is not None:
            if exit_number == 1:
                self.logger.critical(message)
            else:
                self.logger.info(message)
            self.logger.info("############## END BCIL_DCM_CONVERT ##############")
            self.logger = bcil_dcm_convert_logger.disposal_logger(self.logger)  # del logger
        exit(exit_number)

    def warn(self, message: str) -> NoReturn:
        self.console_logger.warning(message)
        self.logger.warning(message)

    def mkdir(self, path: str) -> NoReturn:
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            os.chmod(path, 0o755)
        except Exception as e:
            self.close("Unable to create folder at specified location. (" + path + ") " + str(e))

    def rm_work_files(self):
        rm_dir_list = [
            self.work_path.dcm_list,
            self.work_path.dicom_d,
            self.work_path.raw_data_d,
            self.work_path.log_d,
            self.work_path.subject_d
        ]
        try:
            for f in rm_dir_list:
                if os.path.exists(f):
                    if os.path.isdir(f):
                        if len(os.listdir(f)) == 0:
                            os.rmdir(f)
                    else:
                        os.remove(f)
        except Exception as e:
            self.close("Unable to remove work files. (" + f + ") " + str(e))

    @staticmethod
    def gen_bdc_path(bdc_work_folder: str) -> tuple():
        list_str = "subject_d raw_data_d study_csv series_csv dcm_csv nifti_d dicom_d log_d log_txt dcm_list"
        bdc_path_list = namedtuple("bdc_path_list", list_str)
        subject_d = bdc_work_folder
        raw_data_d = os.path.join(subject_d, "RawData")
        study_csv = os.path.join(subject_d, "RawData", "Studyinfo.csv")
        series_csv = os.path.join(subject_d, "RawData", "Seriesinfo.csv")
        dcm_csv = os.path.join(subject_d, "RawData", "DICOMlist.csv")
        nifti_d = os.path.join(subject_d, "RawData", "NIFTI")
        dicom_d = os.path.join(subject_d, "RawData", "DICOM")
        log_d = os.path.join(subject_d, "logs")
        log_txt = os.path.join(subject_d, "logs", "bcil_dcm_convert.log")
        dcm_list = os.path.join(subject_d, "dcm_list.txt")
        return bdc_path_list(
            subject_d, raw_data_d, study_csv, series_csv, dcm_csv, nifti_d, dicom_d, log_d, log_txt, dcm_list)

    @staticmethod
    def gen_work_base_path(work_folder: str) -> tuple():
        work_folder + "bcil_dcm_convert_folder" + os.sep
        work_root = os.path.join(work_folder, "bcil_dcm_convert_folder")
        work_base_path_list = namedtuple("work_base_path_list", "bdc_id subject_d unzip_d link_d")
        bdc_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        subject_d = os.path.join(work_root, "tmp", bdc_id)
        unzip_d = os.path.join(work_root, bdc_id)
        link_d = os.path.join(work_root, "tmp", bdc_id + "_link")
        while os.path.exists(subject_d) or os.path.exists(unzip_d) or os.path.exists(link_d):
            bdc_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_d = os.path.join(work_root, "tmp", bdc_id)
            unzip_d = os.path.join(work_root, bdc_id)
            link_d = os.path.join(work_root, "tmp", bdc_id + "_link")
        try:
            os.makedirs(subject_d, exist_ok=True)
            os.chmod(subject_d, 0o755)
        except Exception as e:
            print("Unable to create folder at specified location. (" + subject_d + ") " + str(e))
            exit(1)
        return work_base_path_list(bdc_id, subject_d, unzip_d, link_d)

    def main(self) -> bool:

        if self.logger is None:
            self.close("Error : init error.")
            return False

        try:
            # check and unzip
            src_folders = self.check_src_dcm()
            # get dcm list
            file_count = self.create_dcm_list(src_folders)
            # read dcm
            naming_rule = self.read_dcm_header(file_count)
            self.dst_path = self.set_dist_path(naming_rule)

            # save sample dcm
            self.save_ex_dcm()
            # save nifti
            if self.create_nifti is True:
                self.save_nifti(src_folders)
            # save study csv
            self.logger.info("Saving: Studyinfo.csv")
            self.study.save_csv(self.work_path.study_csv, self.study.df)

            # save series csv
            self.logger.info("Saving: Seriesinfo.csv")
            self.series.save_csv(self.work_path.series_csv, self.series.df)

            # move tmp >> subject dir
            self.move_subject()

            self.rm_work_files()
            self.logger.debug("Changing: permission of files")
            self.permission_modify(self.dst_path.subject_d)

            self.logger.info("############## END BCIL_DCM_CONVERT ##############")

        finally:
            if self.console_logger is not None:
                self.console_logger = bcil_dcm_convert_logger.disposal_logger(self.console_logger)
            if self.logger is not None:
                self.logger = bcil_dcm_convert_logger.disposal_logger(self.logger)

        return True

    def check_src_dcm(self) -> List:
        # src dcm path check
        tmp = []
        for dcm_dir in self.dcm_dir_list:
            src = str(os.path.abspath(dcm_dir))
            if not os.path.exists(src):  # not found
                self.close("Error : <input subject's dcm folder or dcm.zip> not found. (" + dcm_dir + ")")
            if not os.path.isdir(src) and not zipfile.is_zipfile(src):
                self.close("Error : <input subject's dcm folder or dcm.zip> is not folder and not zip file. (" + dcm_dir + ")")
            tmp.append(src)

        # unzip (dir or zip)
        src_list = []
        for src in tmp:
            if zipfile.is_zipfile(src):  # zip file
                zn = os.path.splitext(os.path.basename(src))[0]
                unzip_path = self.get_unique_path_inc(self.work_base_path.unzip_d, zn) + os.sep
                self.mkdir(unzip_path)
                src_list.append(self.unzip_exec(src, unzip_path))
            else:  # directory
                src_list.append(src + ("" if src.endswith(os.sep) else os.sep))
        return src_list

    def unzip_exec(self, src_path: str, unzip_path: str) -> str:
        self.logger.info("Start : unzip ")
        self.logger.info(" " + src_path + " > " + unzip_path + "")
        try:
            with zipfile.ZipFile(src_path, "r") as zf:
                for file in tqdm.tqdm(desc="unzipping input DICOM.zip",
                                      leave=True, ascii=True, iterable=zf.namelist(), total=len(zf.namelist())):
                    zf.extract(member=file, path=unzip_path)
                self.logger.info("End: unzip (" + str(len(zf.namelist())) + " files.)")
            return unzip_path
        except Exception as e:
            self.close("Error : " + src_path + " > " + unzip_path + " failure. " + str(e))

    def create_dcm_list(self, src_list: List) -> int:

        self.logger.info("Start: get_dcm_list")
        count = 0
        with open(self.work_path.dcm_list, mode='w', encoding="utf-8") as out_f:
            for src in src_list:
                for folder in [src]:
                    for root, dirs, files in os.walk(top=folder):
                        s_files = sorted(files)
                        for file in s_files:
                            if file.endswith((".ima", ".dcm", ".dic", ".dc3", ".dicom", ".IMA", ".DCM", ".DIC", ".DC3", ".DICOM")) \
                                    or (file.isalnum() and len(file) == 8):  # 指定拡張子or拡張子なし8文字の英数ファイル名
                                file_full_path = os.path.join(root, file)
                                out_f.write(file_full_path + '\n')
                                count += 1
        self.logger.info("End: get_dcm_list (" + str(count) + " files.)")
        if count == 0:
            self.close("dcm file not found.", 0)
        return count

    def read_dcm_header(self, file_count: int) -> dict:

        self.logger.info("Start: read_dcm_header")
        read_count: int = 0

        # dcm csv setting
        dcm_csv = open(self.work_path.dcm_csv, mode='w', encoding="utf-8")
        dcm_csv_format = '{},{},{},{}\n'
        dcm_csv.write(dcm_csv_format.format("Series Number", "Instance Number", "File path", "Series UID"))  # header

        with open(self.work_path.dcm_list, mode='r', encoding="utf-8")as r:
            for line in tqdm.tqdm(r, desc="reading DICOM", total=file_count, leave=True, ascii=True):

                file = line.rstrip('\r\n')
                read_count += 1

                try:
                    ds = pydicom.read_file(file)
                except InvalidDicomError:
                    self.logger.warning("Warning : skip file (can not read) : " + file)
                    continue
                if 'PixelData' not in ds:
                    self.logger.warning("Warning : skip file (no image) : " + file)
                    continue

                series_number = ds["0x00200011"].value
                series_uid = str(ds["0x0020000e"].value)
                study_uid = str(ds["0x0020000d"].value)
                instance_num = ds["0x00200013"].value

                # dcm csv write
                dcm_csv.write(dcm_csv_format.format(series_number, instance_num, file, series_uid))

                if series_uid in self.series.get_unique_col():  # series_uid が既出の場合は次へスキップ
                    continue

                manufacturer = str(ds["0x00080070"].value) if "0x00080070" in ds else None
                patient_position = str(ds["0x00185100"].value) if "0x00185100" in ds else None

                # kspace info
                mri_identifier = gradient = system = dwelltime_read = dwelltime_phase = None
                read_direction = phase_direction = slice_direction = fl_reference_amplitude = None
                parallel_factor = multiband_factor = uc_flip_angle_mode = phase_partial_fourier = None
                slice_partial_fourier = None

                if 'SIEMENS' in manufacturer.upper():
                    k = BcilDcmKspaceInfo(file)
                    k.setup_file_logger(self.work_path.log_txt)
                    k.main()
                    (mri_identifier, gradient, system, dwelltime_read, dwelltime_phase,
                     read_direction, phase_direction, slice_direction, fl_reference_amplitude,
                     parallel_factor, multiband_factor, uc_flip_angle_mode, phase_partial_fourier,
                     slice_partial_fourier,) = k.output
                    del k

                # series
                if mri_identifier == "extended":
                    variable_data = self.get_variable_data_extended(ds)
                    if uc_flip_angle_mode == "16":
                        variable_data["FA"] = None
                elif mri_identifier == "interoperatabillity":
                    variable_data = self.get_variable_data_interoperatabillity(ds)
                else:
                    variable_data = self.get_variable_data(ds)

                self.series.add_row_dict({
                    "Series Number": series_number,
                    "Time": ds["0x00080031"].value if "0x00080031" in ds else None,
                    "Description": ds["0x0008103e"].value if "0x0008103e" in ds else None,
                    "Protocol": ds["0x00181030"].value if "0x00181030" in ds else None,
                    "Scanning Sequence": variable_data['Scanning_Sequence'],
                    "Sequence Name": variable_data['Sequence_Name'],
                    "TR[msec]": variable_data['TR'],
                    "TE[msec]": variable_data['TE'],
                    "TI[msec]": variable_data['TI'],
                    "FA[degree]": variable_data['FA'],
                    "Matrix(phase*read)": variable_data['Matrix'],
                    "Pixel size[mm]": variable_data['Pixel_size'],
                    "Slice thickness[mm]": variable_data['Slice_thickness'],
                    "Number of averages": variable_data['Number_of_averages'],
                    "Image Type": ' '.join(map(str, ds["0x00080008"].value if "0x00080008" in ds else [])),
                    "DwelltimeRead": dwelltime_read,
                    "DwelltimePhase": dwelltime_phase,
                    "Patient Position": patient_position,
                    "Read.direction": read_direction,
                    "Phase.direction": phase_direction,
                    "Slice.direction": slice_direction,
                    "flReferenceAmplitude": fl_reference_amplitude,
                    "Parallel factor": parallel_factor,
                    "Multi-band factor": multiband_factor,
                    "PhasePartialFourier": phase_partial_fourier,
                    "SlicePartialFourier": slice_partial_fourier,
                    "Total Count of DICOMs": 0,
                    "Example DICOM": file,
                    "Series UID": series_uid,
                    "Study UID": study_uid,
                    "NIFTI in RawData": None,
                    "NIFTI in BIDS": None,
                })

                # study
                study_uid_list = self.study.get_unique_col()
                if study_uid not in study_uid_list:
                    self.study.add_row_dict({
                        "Patient Name": ds["0x00100010"].value if "0x00100010" in ds else None,
                        "Patient ID": ds["0x00100020"].value if "0x00100020" in ds else None,
                        "Patient's Birth date": ds["0x00100030"].value if "0x00100030" in ds else None,
                        "Patient's Sex": ds["0x00100040"].value if "0x00100040" in ds else None,
                        "Patient's Age": ds["0x00101010"].value if "0x00101010" in ds else None,
                        "Patient's Size": ds["0x00101020"].value if "0x00101020" in ds else None,
                        "Patient's Weight": ds["0x00101030"].value if "0x00101030" in ds else None,
                        "Patient's Position": patient_position,
                        "Study Date": ds["0x00080020"].value if "0x00080020" in ds else None,
                        "Study Description": ds["0x00081030"].value if "0x00081030" in ds else None,
                        "Requesting physician": ds["0x00321032"].value if "0x00321032" in ds else None,
                        "Station": str(ds["0x00081010"].value) if "0x00081010" in ds else None,
                        "Manufacturer": manufacturer,
                        "Model": ds["0x00081090"].value if "0x00081090" in ds else None,
                        "Institution": ds["0x00080080"].value if "0x00080080" in ds else None,
                        "System": system,
                        "Gradient": gradient,
                        "StudyUID": study_uid,
                        "PatAUSJID": ds["0xC0D30011"].value if "0xC0D30011" in ds else None,
                    })

        dcm_csv.close()

        # study UID unique check
        self.unique_study_check(study_uid_list)

        # conv df
        self.study.df = self.study.from_dict()

        self.series.df = self.series.from_dict()
        self.series.df = self.series.df.sort_values(["Series Number", "TE[msec]"]).reset_index(drop=True)

        self.dcm.df = self.dcm.read_csv(self.work_path.dcm_csv).astype(self.dcm.d_type)
        self.dcm.df = self.dcm.df.sort_values(["Series Number", "Instance Number"]).reset_index(drop=True)
        self.dcm.save_csv(self.work_path.dcm_csv, self.dcm.df)  # 保存

        self.add_dcm_file_count()

        # naming_rule_list 最後の一枚から情報取得
        naming_rule_list = {}
        if self.subject_name is not None and len(self.subject_name) > 0 and "%" in self.subject_name:
            naming_rule_list = {
                r"%a": self.esc(str(ds["0x0051100f"].value)) if "0x0051100f" in ds else "",
                r"%i": self.esc(str(ds["0x00100020"].value)) if "0x00100020" in ds else "",
                r"%k": self.esc(str(ds["0x0020000d"].value)) if "0x0020000d" in ds else "",
                r"%m": self.esc(str(ds["0x00080070"].value)) if "0x00080070" in ds else "",
                r"%n": self.esc(str(ds["0x00100010"].value)) if "0x00100010" in ds else "",
                r"%x": self.esc(str(ds["0x00200010"].value)) if "0x00200010" in ds else "",
            }

        self.logger.info(
            "End: read_dcm_header (" + str(len(self.series.df)) + " series. " + str(read_count) + " files.)")
        return naming_rule_list

    @staticmethod
    def get_variable_data(ds: pydicom.dataset) -> list:
        variable_data = {
            'Sequence_Name': ds["0x00180024"].value if "0x00180024" in ds else None,
            'TR': ds["0x00180080"].value if "0x00180080" in ds else None,
            'TE': ds["0x00180081"].value if "0x00180081" in ds else None,
            'TI': ds["0x00180082"].value if "0x00180082" in ds else None,
            'FA': ds["0x00181314"].value if "0x00181314" in ds else None,
            'Slice_thickness': ds["0x00180050"].value if "0x00180050" in ds else None,
            'Number_of_averages': ds["0x00180083"].value if "0x00180083" in ds else None,
            'Matrix': None,
            'Scanning_Sequence': None,
            'Pixel_size': None,
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
    def get_variable_data_extended(ds: pydicom.dataset) -> list:
        variable_data = {
            'Sequence_Name': ds["0x00189005"].value if "0x00189005" in ds else None,
            'TR': None,
            'TE': None,
            'TI': None,
            'FA': None,
            'Slice_thickness': None,
            'Number_of_averages': None,
            'Matrix': None,
            'Scanning_Sequence': None,
            'Pixel_size': None,
        }
        if "0x52009229" in ds:
            csa9229 = ds["0x52009229"].value[0]
            if "0x00189112" in csa9229:
                hdr00189112 = csa9229["0x00189112"].value[0]
                variable_data['TR'] = hdr00189112["0x00180080"].value if "0x00180080" in hdr00189112 else None
                variable_data['FA'] = hdr00189112["0x00181314"].value if "0x00181314" in hdr00189112 else None
            if "0x00189115" in csa9229:
                hdr00189115 = csa9229["0x00189115"].value[0]
                variable_data['TI'] = hdr00189115["0x00189079"].value if "0x00189079" in hdr00189115 else None

        if "0x52009230" in ds:
            csa9230 = ds["0x52009230"].value[0]
            if "0x00289110" in csa9230:
                hdr00289110 = csa9230["0x00289110"].value[0]
                pixel_size_ary = hdr00289110["0x00280030"].value if "0x00280030" in hdr00289110 else None
                variable_data['Pixel_size'] = ' '.join(map(str, pixel_size_ary))
                variable_data['Slice_thickness'] = hdr00289110["0x00180050"].value if "0x00180050" in hdr00289110 else None
            if "0x00189119" in csa9230:
                hdr00189119 = csa9230["0x00189119"].value[0]
                variable_data['Number_of_averages'] = hdr00189119["0x00180083"].value if "0x00180083" in hdr00189119 else None
            if "0x00189114" in csa9230:
                hdr00189114 = csa9230["0x00189114"].value[0]
                variable_data['TE'] = hdr00189114["0x00189082"].value if "0x00189082" in hdr00189114 else None

        # Scanning Sequence
        ss_ary = []
        if "0x00189008" in ds:
            if ds["0x00189008"].value == "GRADIENT":
                ss_ary.append("GR")
            if ds["0x00189008"].value == "SPIN":
                ss_ary.append("SE")
        if "0x00189018" in ds:
            if ds["0x00189018"].value == "YES":
                ss_ary.append("EPI")
        if len(ss_ary) > 0:
            variable_data['Scanning_Sequence'] = " ".join(ss_ary)

        # Matrix
        row = ds["0x00280010"].value if "0x00280010" in ds else None
        col = ds["0x00280011"].value if "0x00280011" in ds else None
        if row and row:
            matrix = str(row) + "*" + str(col) if row < col else str(col) + "*" + str(row)
            variable_data['Matrix'] = matrix
        return variable_data

    @staticmethod
    def get_variable_data_interoperatabillity(ds: pydicom.dataset) -> list:
        variable_data = {
            'Sequence_Name': ds["0x00180024"].value if "0x00180024" in ds else None,
            'TR': ds["0x00180080"].value if "0x00180080" in ds else None,
            'TE': ds["0x00180081"].value if "0x00180081" in ds else None,
            'TI': ds["0x00180082"].value if "0x00180082" in ds else None,  ## 不明分
            'FA': ds["0x00181314"].value if "0x00181314" in ds else None,
            'Slice_thickness': ds["0x00180050"].value if "0x00180050" in ds else None,
            'Number_of_averages': ds["0x00180083"].value if "0x00180083" in ds else None,
            'Matrix': None,
            'Scanning_Sequence': None,
            'Pixel_size': None,
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

    def unique_study_check(self, study_uid_list: list) -> NoReturn:
        if len(study_uid_list) > 1:
            m = "Error : multiple study UID error. found " + str(len(study_uid_list)) + " study UID. ("
            m += ', '.join(study_uid_list) + ")"
            self.close(m)

    def add_dcm_file_count(self) -> NoReturn:

        last_data = {"series_number": None, "instance_numbers": []}
        for index, item in self.series.df.iterrows():
            dcm_row = self.dcm.df[
                (self.dcm.df['Series Number'] == item['Series Number']) & (self.dcm.df['Series UID'] == item['Series UID'])]
            # add count
            self.series.df.at[index, 'Total Count of DICOMs'] = len(dcm_row)
            # series numberが同じで series uidが異なるデータが存在する(QSM等)為 周回遅れで処理
            if last_data["series_number"] is not None and last_data["series_number"] != item['Series Number']:
                self.check_dcm_range(last_data)
                last_data["instance_numbers"] = []
            last_data["series_number"] = item['Series Number']
            last_data["instance_numbers"].extend(list(dcm_row["Instance Number"]))
        self.check_dcm_range(last_data)
        return True

    def check_dcm_range(self, data: dict) -> NoReturn:
        series_number = data["series_number"]
        instance_num_list = data["instance_numbers"]
        instance_num_list.sort()
        # first number check
        if instance_num_list[0] != 1:
            self.warn("series number: " + str(series_number) + ", start instance number: " + str(instance_num_list[0]))
        # duplication check
        dup = [k for k, v in Counter(instance_num_list).items() if v > 1]
        if len(dup) > 0:
            m = "series number: " + str(series_number) + ", instance number: " + ', '.join(map(str, dup))
            self.warn("Error: duplicate instance number. (" + m + ".)")
            instance_num_list = list(set(instance_num_list))  # 重複削除
        # missing check
        missing = []
        for i in range(instance_num_list[0], instance_num_list[-1] + 1):
            if i not in instance_num_list:
                missing.append(i)
        if len(missing) > 0:
            m = "series number: " + str(series_number) + ", instance number: " + ', '.join(map(str, missing))
            self.warn("Error: missing instance number. (" + m + ".)")

    def save_ex_dcm(self):
        self.logger.info("Saving: example dcm")
        for index, item in self.series.df.iterrows():
            save_file_path = self.get_unique_path_inc(self.work_path.dicom_d, str(item['Series Number']), ".dcm")
            try:
                shutil.copy(item['Example DICOM'], save_file_path)
            except Exception as e:
                self.warn("Error : save_example_dicom: " + str(e))
                continue

    def save_nifti(self, src_folders: List):

        self.logger.info("Start: dcm2niix")
        self.mkdir(self.work_path.nifti_d)

        # multi dcm src folder
        nifti_src_folder_path = src_folders[0]
        if len(src_folders) > 1:  # linkで対応
            self.mkdir(self.work_base_path.link_d)
            for src_folder in src_folders:
                dir_name = os.path.basename(os.path.dirname(src_folder))
                os.symlink(src_folder, self.get_unique_path_inc(self.work_base_path.link_d, dir_name))
            nifti_src_folder_path = self.work_base_path.link_d

        with tqdm.tqdm(desc="converting DICOM to NIFTI", total=100, leave=True, ascii=True) as nip:
            nip.update(1)
            cmd_ary = [
                self.DCM_2_NIIX_CMD,  # dcm2niix
                "-f", self.DCM_2_NAMING_RULE,  # filename
                "-w", "1" if (self.overwrite != 0) else "0",  # write behavior for name conflicts
                "-o", self.work_path.nifti_d  # output directory
            ]
            if self.gz is True:
                cmd_ary.extend(["-z", "y"])  # gz compress images
            cmd_ary.append(nifti_src_folder_path)  # <in_folder> src

            info_ary = []
            error_ary = []
            try:
                ret = subprocess.run(cmd_ary, capture_output=True, text=True, check=True)
                info_ary = list(filter(None, ret.stdout.split("\n")))
                error_ary = list(filter(None, ret.stderr.split("\n")))

            except subprocess.CalledProcessError as e:
                info_ary = list(filter(None, e.stdout.split("\n")))
                error_ary = list(filter(None, e.stderr.split("\n")))
            except Exception as e:
                self.logger.error("Error: dcm2niix: " + str(e))
            finally:
                nip.update(99)

            for message in info_ary:
                self.logger.info(message)
            for message in error_ary:
                self.logger.error(message)
                self.console_logger.error("dcm2niix: " + message)

        if len(src_folders) > 1:  # 複数srcの場合はリンク対応を削除する
            shutil.rmtree(nifti_src_folder_path)
        self.logger.info("End: dcm2niix")

        # series 更新
        nii_ext = ".nii.gz" if self.gz is True else ".nii"
        nifti_files = sorted(glob.glob(self.work_path.nifti_d + os.sep + "*" + nii_ext))
        nifti_list = {}
        for nf in nifti_files:
            num = os.path.basename(nf).split("_")[0]
            if num not in nifti_list:
                nifti_list[num] = []
            nifti_list[num].append(nf.replace(self.work_path.subject_d, self.dst_path.subject_d, 1))
        nifti_list = dict(sorted(nifti_list.items(), key=lambda x: int(x[0])))
        for num, file_list in nifti_list.items():
            search = self.series.df.loc[(self.series.df['Series Number'] == int(num))]
            self.series.df.at[search.index[0], 'NIFTI in RawData'] = ' '.join(file_list)

    @staticmethod
    def permission_modify(dir_path) -> bool:
        dir_path += "" if dir_path.endswith(os.sep) else os.sep
        # permission check & mod
        for file in glob.glob(dir_path + os.sep + r'**', recursive=True):
            os.chmod(file, 0o755)
        return True

    #############################################
    @staticmethod
    def get_unique_path_inc(parent_dir: str, file_name: str, ext: str = "") -> str:

        fn = file_name + ext
        if not os.path.exists(os.path.join(parent_dir, fn)):
            return os.path.join(parent_dir, fn)
        num = 2
        while os.path.exists(os.path.join(parent_dir, fn)):
            fn = file_name + "_" + str(num) + ext
            num = num + 1
        return os.path.join(parent_dir, fn)

    @staticmethod
    def esc(code: str, replace: Optional[str] = "_") -> Optional[str]:
        return code.translate(str.maketrans({'%': replace, ':': replace, ';': replace, '*': replace, '^': replace,
                                             '/': replace, '\\': replace, '`': replace, os.sep: replace,
                                             '>': replace, '<': replace, '?': replace, '"': replace,
                                             '&': replace, '$': replace, '(': replace, ')': replace, }))

    def set_dist_path(self, naming_rule: dict) -> tuple:
        
        if self.subject_name is not None and len(self.subject_name) > 0:
            tmp = self.subject_name
            if "%" in self.subject_name:
                for key, val in naming_rule.items():
                    tmp = tmp.replace(key, val)
            tmp = self.esc(tmp)
            folder_name = "NONE" if tmp == "" else tmp
        else:
            if zipfile.is_zipfile(self.dcm_dir_list[0]):
                folder_name = os.path.splitext(os.path.basename(self.dcm_dir_list[0]))[0]
            else:
                name_base = self.dcm_dir_list[0] + ("" if self.dcm_dir_list[0].endswith(os.sep) else os.sep)
                folder_name = os.path.basename(os.path.dirname(name_base))
        
        dst_d = os.path.join(self.parent_d, folder_name)
        if self.overwrite == 0 and os.path.exists(dst_d):
            # 上書き禁止で既に同じディレクトリがある場合は別名を発行して保存
            dst_d = self.get_unique_path_inc(self.parent_d, folder_name)
            m = "Warning: Do not overwrite is selected, but the file already exists. Save to another location: " + dst_d
            self.warn(m)
        return self.gen_bdc_path(dst_d)

    def move_subject(self):

        overwrite_mode = None
        if not os.path.exists(self.dst_path.raw_data_d):
            overwrite_mode = "create"
        elif self.overwrite == 1:
            overwrite_mode = "replace"
        elif self.overwrite == 2:
            if os.path.exists(self.dst_path.study_csv):
                dst_study_csv = self.study.read_csv(self.dst_path.study_csv).astype(self.study.d_type)
                if not self.study.df.equals(dst_study_csv):
                    self.close("Error: Studyinfo.csv does not match and cannot be merged. Results are in " +
                               self.work_path.subject_d)
            if not os.path.exists(self.dst_path.series_csv) or not os.path.exists(self.dst_path.dcm_csv):
                self.close("Error: Data is inaccurate and cannot be merged. Results are in " + self.work_path.subject_d)
            overwrite_mode = "append"

        self.logger.info("Start: move subject (" + overwrite_mode + ")" + self.work_path.subject_d + " > " + self.dst_path.subject_d)

        if overwrite_mode == "append":
            # ワークフォルダ内を更新する
            try:
                dst_series_csv = self.series.read_csv(self.dst_path.series_csv).astype(self.series.d_type)
                merge_series_csv = pd.concat([dst_series_csv, self.series.df])
                merge_series_csv = merge_series_csv.drop_duplicates(subset=['Series Number', 'Series UID'])
                merge_series_csv = merge_series_csv.sort_values(["Series Number", "TE[msec]"]).reset_index(drop=True)
                self.series.save_csv(self.dst_path.series_csv, merge_series_csv)  # 保存

                dst_dcm_csv = self.dcm.read_csv(self.dst_path.dcm_csv).astype(self.dcm.d_type)
                merge_dcm_csv = pd.concat([dst_dcm_csv, self.dcm.df])
                merge_dcm_csv = merge_dcm_csv.drop_duplicates(subset=["File path", 'Series Number'])
                merge_dcm_csv = merge_dcm_csv.sort_values(["Series Number", "Instance Number"]).reset_index(drop=True)
                self.dcm.save_csv(self.dst_path.dcm_csv, merge_dcm_csv)  # 保存

            except Exception as e:
                self.warn("append subject failre." + str(e))
            csv_files = []
        else:
            csv_files = [self.work_path.study_csv, self.work_path.series_csv, self.work_path.dcm_csv]

        # RawData以下
        self.mkdir(self.dst_path.raw_data_d)
        nifti_files = glob.glob(self.work_path.nifti_d + "/*", recursive=False)
        dcm_files = glob.glob(self.work_path.dicom_d + "/*", recursive=False)
        for file in csv_files + nifti_files + dcm_files:
            dst = file.replace(self.work_path.subject_d, self.dst_path.subject_d, 1)
            self.mkdir(os.path.dirname(dst))
            if os.path.exists(dst):
                self.warn("Overwrite: " + dst)
            try:
                shutil.move(file, dst)
            except Exception as e:
                self.warn("move subject failre." + str(e))

        # ログファイル
        self.logger = bcil_dcm_convert_logger.disposal_logger(self.logger)  # ファイルログ一旦停止
        if not os.path.exists(self.dst_path.log_d):
            shutil.move(self.work_path.log_d, self.dst_path.log_d)
        else:
            with open(self.work_path.log_txt, "r") as src_file, open(self.dst_path.log_txt, "a") as dst_file:
                for line in src_file.readlines():
                    dst_file.write(line)
            os.remove(self.work_path.log_txt)

        self.logger = bcil_dcm_convert_logger.get_file_logger(
            path=self.dst_path.log_txt,
            identifier=self.work_base_path.bdc_id
        )

        self.logger.info("End: move subject.")
        return True


if __name__ == '__main__':

    from argparse import ArgumentParser
    usage = \
        "\n" \
        "BCILDCMCONVERT converts DICOM from various MRI scanners to NIFTI volumes, " \
        "organizes the data into a study directory, and stores MRI scanning params useful for preprocessing " \
        "brain imaging data with HCP pipeline and FSL. (For details, see https://github.com/RIKEN-BCIL/BCILDCMCONVERT) " \
        "\n\n" \
        " Ex 1). Use an input of directory containing DICOM files\n" \
        " $ python3 bcil_dcm_convert.py [option(s)] <parent folder to save> <input subject's DICOM folder>\n" \
        "\n" \
        " Ex 2). Use zipped file as an input of DICOM files\n" \
        " $ python3 bcil_dcm_convert.py [option(s)] <parent folder to save> <input subject's DICOM.zip>\n" \
        "\n" \
        "\n" \
        "".format(__file__)

    ap = ArgumentParser(usage=usage)
    # required
    ap.add_argument(
        '<parent folder to save>',
        type=str,
        help='path to parent folder, to which an output subject\'s folder will be saved')
    ap.add_argument(
        '<input subject\'s DICOM folder or DICOM.zip>',
        type=str,
        help='path to input folder or zipped file containing a subject\'s DICOM file(s)',
        nargs="*")

    # optional
    ap.add_argument('-n', '--no_nii',
                    dest='no_nii', action='store_true', help='do not convert to NIFTI')
    ap.add_argument('-s',
                    dest='subject_name', type=str,
                    help=r"subject's folder name (%%a=antenna (coil) name, %%i=ID of patient, %%k=studyInstanceUID, %%m=manufacturer, %%n=name of patient, %%x=study ID)",
                    metavar="<subject folder name>")
    ap.add_argument('-w',
                    dest='overwrite_behavior', type=int,
                    help=" overwrite options (0: do not overwrite, 1: replace, 2: append, default is 0)",
                    default=0, metavar="overwrite option <num>", choices=[0, 1, 2])
    ap.add_argument('-z', '--gz',
                    dest='gz', action='store_true',
                    help='compress NIFTI volumes with .gz (default is not compressed, and saved as .nii)')  # gzオプション
    ap.add_argument('-d',
                    dest='working_folder', type=str,
                    help="path to working folder",
                    metavar="<working folder>")
    ap.add_argument('-v', '--version',
                    action='version', version=BcilDcmConvert.__version__,
                    help="print version number")
    args = ap.parse_args()

    ###########################

    bc = BcilDcmConvert(
        dcm_dir_list=args.__getattribute__("<input subject's DICOM folder or DICOM.zip>"),  #args.dcmDir,
        save_parent_dir=args.__getattribute__("<parent folder to save>"),  #args.saveDir,
        create_nifti=not args.no_nii,
        overwrite=args.overwrite_behavior,
        subject_name=args.subject_name,
        gz=args.gz,
        working_folder=args.working_folder,
    )
    if bc.main() is True:
        print("completed bcil_dcm_convert.py!")
    del bc