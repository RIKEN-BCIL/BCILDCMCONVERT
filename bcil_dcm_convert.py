# !/usr/bin/env python3
# coding:utf-8
import os
import glob
import re
import shutil
from bcil_dcm_kspace_info import BcilDcmKspaceInfo
import pandas
import pydicom
from pydicom.errors import InvalidDicomError
import copy


class BcilDcmConvert:

    subject_dir_list = []
    save_parent_dir = ""
    nifti_convert = False
    overwrite = False

    err_mes = []

    LOG_SAVE_DIR = "logs"
    CSV_SAVE_DIR = "RawData"
    NII_SAVE_DIR = CSV_SAVE_DIR + os.sep + "NIFTI"
    STUDY_DICT = {
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
        "Model": [],  # ###### Model
        'Institution': [],  # ###### Institution
        'System': [],
        "Gradient": [],
        "PatAUSJID": [],
        'StudyUID': [],
    }
    SERIES_DICT = {
        '00.Number': [],  # SeriesNumber
        'Time': [],  # SeriesTime
        'Description': [],  # SeriesDescription
        'Protocol': [],  # ProtocolName
        'Scanning Sequence': [],
        'Sequence Name': [],

        'TR[msec]': [],  # RepetitionTime
        'TE[msec]': [],  # EchoTime
        'TI[msec]': [],  # InversionTime
        'FA[degree]': [],  # FlipAngle

        'Matrix': [],  # Rows & Columns
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
        'Example DICOM': [],
        'Series UID': [],  # SeriesInstanceUID
        'Study UID': [],
    }
    CSA_DICT = {
        "system": None,
        "gradient": None,
        "DwelltimeRead": "None",
        "DwelltimePhase": "None",
        "Read.direction": "None",
        "Phase.direction": "None",
        "Slice.direction": "None",
    }

    #
    STUDY_CSV_NAME = "Studyinfo.csv"
    SERIES_CSV_NAME = "Seriesinfo.csv"
    DCM_DIR_LIST_TXT_NAME = "DICOMDirlist.txt"
    DCM_DIR_TXT_NAME = "DICOMlist.txt"
    LOG_TXT_NAME = "log.txt"
    DCM_2_NIIX_CMD = ["dcm2niix"]
    DCM_2_NAMING_RULE = r"%s_%p"

    def __init__(self):
        self.subject_dir_list = []
        self.save_parent_dir = ""
        self.nifti_convert = False
        self.overwrite = False
        self.err_mes = []

    def set_params(self, subject_dir_list, save_parent_dir, nifti_convert, overwrite):
        self.subject_dir_list = subject_dir_list
        self.save_parent_dir = save_parent_dir
        self.nifti_convert = nifti_convert
        self.overwrite = overwrite

    def main(self):

        for subject_dir in self.subject_dir_list:

            dir_name = os.path.basename(os.path.dirname(subject_dir))
            save_path = self.save_parent_dir + dir_name + os.sep
            if not self.overwrite and os.path.isdir(save_path):
                self.err_mes.append(save_path + ": already exist (skip subject)")
                continue

            file_list = self.get_dicom_file_list(subject_dir)
            if not file_list:
                self.err_mes.append(subject_dir + ": dicom file 0. (skip subject)")
                continue

            h = self.read_dicom_headers(file_list)

            save_data_path = save_path + self.CSV_SAVE_DIR + os.sep
            if not os.path.isdir(save_data_path):
                os.makedirs(save_data_path, exist_ok=True)

            self.save_study_csv(save_data_path, h["study_data"])
            self.save_series_csv(save_data_path, h["series_data"])
            self.save_subject_dir_name(save_data_path, subject_dir)
            self.save_dicom_file_name_list(save_data_path, h["dcm_data"])

            log_data_path = save_path + self.LOG_SAVE_DIR + os.sep
            if not os.path.isdir(log_data_path):
                os.makedirs(log_data_path, exist_ok=True)
            self.save_logs(log_data_path, h["skip_data"])

            nii_data_path = save_path + self.NII_SAVE_DIR + os.sep
            if self.nifti_convert:
                self.save_nii(nii_data_path, subject_dir)

    def get_dicom_file_list(self, subject_dir):

        regex = r".*\.(ima|dcm|dic|dc3|dicom)"
        search_src = subject_dir + r"**"
        files = [f for f in glob.glob(search_src, recursive=True) if re.search(regex, f, re.IGNORECASE)]
        add_files = [f for f in glob.glob(search_src, recursive=True) if re.search(r"^\d{8}$", f)]
        if 0 == len(files) and 0 == len(add_files):
            return []

        files.extend(add_files)
        files.sort()
        return files

    def read_dicom_headers(self, file_list):

        study_dict = copy.copy(self.STUDY_DICT)
        series_dict = copy.copy(self.SERIES_DICT)
        log_list = []
        dcm_list = []

        for file in file_list:

            try:
                ds = pydicom.read_file(file)
            except InvalidDicomError:
                log_list.append(file + ':skip(can not read)')
                continue

            if 'PixelData' not in ds:
                log_list.append(file + ':skip(no image)')
                continue

            dcm_list.append(file)

            series_number = ds["0x00200011"].value
            series_uid = str(ds[0x0020000e].value)
            study_uid = ds[0x0020000d].value
            station_name = ds["0x00081010"].value if "0x00081010" in ds else None
            # instance_number = ds["0x00200013"].value if "0x00200013" in ds else None
            manufacturer = ds["0x00080070"].value if "0x00080070" in ds else None
            patient_position = ds["0x00185100"].value if "0x00185100" in ds else None

            # csa data
            csa_d = copy.copy(self.CSA_DICT)
            if manufacturer == "SIEMENS":
                if (not study_dict["StudyUID"] or not (study_uid in study_dict["StudyUID"])) or \
                        (not series_dict["Series UID"] or not (series_uid in series_dict["Series UID"])):
                    bdki = BcilDcmKspaceInfo(ds)
                    csa_d["system"] = bdki.get_system()
                    csa_d["gradient"] = bdki.get_coil_for_gradient2()
                    csa_d["DwelltimeRead"] = bdki.get_dwell_time_read() or "None"
                    csa_d["DwelltimePhase"] = bdki.get_dwell_time_phase() or "None"
                    directions = bdki.get_directions()
                    csa_d["Read.direction"] = directions["Read.direction"] or "None"
                    csa_d["Phase.direction"] = directions["Phase.direction"] or "None"
                    csa_d["Slice.direction"] = directions["Slice.direction"] or "None"
                    if bdki.errors:
                        err = map(lambda x: file + x, bdki.errors)
                        log_list.extend(err)
                    del bdki
            # study
            if not study_dict["StudyUID"] or not (study_uid in study_dict["StudyUID"]):
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
                study_dict["StudyUID"].append(study_uid)
                study_dict["PatAUSJID"].append(ds["0xC0D30011"].value if "0xC0D30011" in ds else None)

                study_dict["System"].append(csa_d["system"])
                study_dict["Gradient"].append(csa_d["gradient"])

            if not series_dict["Series UID"] or not (series_uid in series_dict["Series UID"]):
                series_dict["00.Number"].append(series_number)
                series_dict["Time"].append(ds["0x00080031"].value if "0x00080031" in ds else None)
                series_dict["Description"].append(ds["0x0008103e"].value if "0x0008103e" in ds else None)
                series_dict["Protocol"].append(ds["0x00181030"].value if "0x00181030" in ds else None)
                series_dict["Sequence Name"].append(ds["0x00180024"].value if "0x00180024" in ds else None)
                series_dict["TR[msec]"].append(ds["0x00180080"].value if "0x00180080" in ds else None)
                series_dict["TE[msec]"].append(ds["0x00180081"].value if "0x00180081" in ds else None)
                series_dict["TI[msec]"].append(ds["0x00180082"].value if "0x00180082" in ds else None)
                series_dict["FA[degree]"].append(ds["0x00181314"].value if "0x00181314" in ds else None)
                series_dict["Slice thickness[mm]"].append(ds["0x00180050"].value if "0x00180050" in ds else None)
                series_dict["Number of averages"].append(ds["0x00180083"].value if "0x00180083" in ds else None)
                series_dict["Patient Position"].append(patient_position)
                series_dict["Example DICOM"].append(file)
                series_dict["Series UID"].append(series_uid)
                series_dict["Study UID"].append(study_uid)

                rows = ds["0x00280010"].value if "0x00280010" in ds else ""
                columns = ds["0x00280011"].value if "0x00280011" in ds else ""
                series_dict["Matrix"].append(str(rows) + " " + str(columns))

                pixel_size_ary = ds["0x00280030"].value if "0x00280030" in ds else []
                series_dict["Pixel size[mm]"].append(' '.join(map(str, pixel_size_ary)))

                image_type_ary = ds["0x00080008"].value if "0x00080008" in ds else []
                series_dict["Image Type"].append(' '.join(map(str, image_type_ary)))

                scanning_sequence_ary = ds["0x00180020"].value if "0x00180020" in ds else []
                series_dict["Scanning Sequence"].append(''.join(map(str, scanning_sequence_ary)))

                series_dict["DwelltimeRead"].append(csa_d["DwelltimeRead"])
                series_dict["DwelltimePhase"].append(csa_d["DwelltimePhase"])
                series_dict["Read.direction"].append(csa_d["Read.direction"])
                series_dict["Phase.direction"].append(csa_d["Phase.direction"])
                series_dict["Slice.direction"].append(csa_d["Slice.direction"])

        return {
            "study_data": study_dict,
            "series_data": series_dict,
            "skip_data": log_list,
            "dcm_data": dcm_list
        }

    def save_study_csv(self, save_data_path, study_dict):
        path = save_data_path + self.STUDY_CSV_NAME
        study_df = pandas.DataFrame(study_dict)
        study_df.T.to_csv(path, header=False)

    def save_series_csv(self, save_data_path, series_dict):
        path = save_data_path + self.SERIES_CSV_NAME
        series_df = pandas.DataFrame(series_dict)
        series_df = series_df.sort_values(["00.Number"])
        series_df.to_csv(path, index=False, columns=series_dict)

    def save_subject_dir_name(self, save_data_path, subject_dir_path):
        path = save_data_path + self.DCM_DIR_LIST_TXT_NAME
        with open(path, mode='w') as txt_file:
            txt_file.write(subject_dir_path.rstrip(os.sep))

    def save_dicom_file_name_list(self, save_data_path, dcm_list):
        path = save_data_path + self.DCM_DIR_TXT_NAME
        with open(path, mode='w') as txt_file:
            txt_file.write('\n'.join(dcm_list))

    def save_logs(self, log_data_path, skip_dicom_list):
        path = log_data_path + self.LOG_TXT_NAME
        with open(path, mode='w') as txt_file:
            txt_file.write('\n'.join(skip_dicom_list))

    def save_nii(self, nii_data_path, subject_dir):

        import subprocess
        if os.path.isdir(nii_data_path):
            shutil.rmtree(nii_data_path)
        os.makedirs(nii_data_path, exist_ok=True)

        dcm2niix_path_ary = self.DCM_2_NIIX_CMD
        dcm_cmd = ':'.join(dcm2niix_path_ary)
        cmd = dcm_cmd + " -f " + self.DCM_2_NAMING_RULE + " -o " + nii_data_path + " " + subject_dir
        try:
            res = subprocess.check_output([cmd], shell=True)
        except:
            print("dcm2niix : failure")


if __name__ == '__main__':

    from argparse import ArgumentParser

    usage = \
        "\n\n" \
        "  ex). $ python3 bcil_dcm_convert.py [option(s)] <Study directory to be saved> <Subject DICOM directory>\n" \
        "\n" \
        "\n" \
        "".format(__file__)

    ap = ArgumentParser(usage=usage)
    ap.add_argument('saveDir', type=str, help='save dir (!!parent dir!!) full path ')
    ap.add_argument('dcmDir', type=str, help='subject dir full path')

    o_help_txt = "overwrite Studyinfo.txt, Seriesinfo.txt, DICOMlist, DICOMDIrlist and NIFTI in <subject dir>"
    ap.add_argument('-o', dest='overwrite', action='store_true', help=o_help_txt)

    n_help_txt = 'do not convert to NIFTI'
    ap.add_argument('-n', dest='no_nii', action='store_true', help=n_help_txt)
    args = ap.parse_args()

    save_d = args.saveDir + os.sep if args.saveDir[-1:] != os.sep else args.saveDir
    dcm_d = args.dcmDir + os.sep if args.dcmDir[-1:] != os.sep else args.dcmDir

    if not os.path.isdir(dcm_d):
        print(dcm_d + ':not found')
        exit()
    if not os.path.isdir(save_d):
        print(args.saveDir + ':not found')
        exit()

    bc = BcilDcmConvert()
    bc.set_params([dcm_d], save_d, not args.no_nii, args.overwrite)
    bc.main()

    if bc.err_mes:
        print("##################################")
        print("\n".join(bc.err_mes))