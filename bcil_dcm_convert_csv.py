import pandas as pd
import numpy as np


class BaseCsvData:
    unique_col_name: str = ""
    setting: dict = {}

    data_dict: dict = {}
    d_type: dict = {}

    df = None

    def __init__(self):
        self.data_dict = dict([(k, []) for k, v in self.setting.items()])
        self.d_type = dict([(k, v["dtype"]) for k, v in self.setting.items()])
        self.fillna_str = dict([(k, {"None": v["fil_val"]}) for k, v in self.setting.items() if v["dtype"] == str])
        self.fillna_not_str = dict([(k, v["fil_val"]) for k, v in self.setting.items() if v["dtype"] != str])

    def add_row(self, column, value):
        if column in self.data_dict.keys():
            self.data_dict[column].append(value)

    def add_row_dict(self, column_value: dict):
        for column, value in column_value.items():
            self.add_row(column, value)

    def from_dict(self) -> pd.DataFrame:
        df = pd.DataFrame.from_dict(self.data_dict)
        df = df.astype(self.d_type)
        return df

    def fill_none(self, df:pd.DataFrame) -> pd.DataFrame:
        df = df.replace(self.fillna_str)
        df = df.fillna(self.fillna_not_str)
        return df

    def save_csv(self, path: str, df: pd.DataFrame):
        df = self.fill_none(df)
        if self.__class__.__name__ == "StudyCsvData":
            df = df.T
            df.to_csv(path, header=False, mode="w")
        else:
            df.to_csv(path, index=False, mode="w")

    def read_csv(self, path: str) -> pd.DataFrame:

        if self.__class__.__name__ == "StudyCsvData":
            csv_df = pd.read_csv(path, dtype=str, header=None, index_col=0).T.reset_index(drop=True)
        else:
            csv_df = pd.read_csv(path, dtype=str)
        type_init_list = {str: "None", int: 0, float: np.nan}
        rep_dict = {}
        for k, v in self.setting.items():
            rep_dict[k] = {v["fil_val"]: type_init_list[v["dtype"]]}
        csv_df = csv_df.replace(rep_dict)
        return csv_df

    def get_unique_col(self) -> list:
        return self.data_dict[self.unique_col_name][:]


class SeriesCsvData(BaseCsvData):
    unique_col_name: str = "Series UID"
    setting: dict = {
        'Series Number': {"dtype": int, "fil_val": 0, },
        'Time': {"dtype": str, "fil_val": "", },
        'Description': {"dtype": str, "fil_val": "", },
        'Protocol': {"dtype": str, "fil_val": "", },
        'Scanning Sequence': {"dtype": str, "fil_val": "", },
        'Sequence Name': {"dtype": str, "fil_val": "NONE", },
        'TR[msec]': {"dtype": float, "fil_val": "", },
        'TE[msec]': {"dtype": float, "fil_val": "", },
        'TI[msec]': {"dtype": float, "fil_val": "", },
        'FA[degree]': {"dtype": float, "fil_val": "NONE", },
        'Matrix(phase*read)': {"dtype": str, "fil_val": "NONE", },
        'Pixel size[mm]': {"dtype": str, "fil_val": "NONE", },
        'Slice thickness[mm]': {"dtype": float, "fil_val": "NONE", },
        'Number of averages': {"dtype": float, "fil_val": "NONE", },
        'Image Type': {"dtype": str, "fil_val": "", },
        'DwelltimeRead': {"dtype": str, "fil_val": "NONE", },
        'DwelltimePhase': {"dtype": str, "fil_val": "NONE", },
        'Read.direction': {"dtype": str, "fil_val": "NONE", },
        'Phase.direction': {"dtype": str, "fil_val": "NONE", },
        'Slice.direction': {"dtype": str, "fil_val": "NONE", },
        'Patient Position': {"dtype": str, "fil_val": "NONE", },
        'flReferenceAmplitude': {"dtype": float, "fil_val": "NONE", },
        'Parallel factor': {"dtype": str, "fil_val": "NONE", },
        'Multi-band factor': {"dtype": str, "fil_val": "NONE", },
        'PhasePartialFourier': {"dtype": str, "fil_val": "NONE", },
        'SlicePartialFourier': {"dtype": str, "fil_val": "NONE", },
        'Total Count of DICOMs': {"dtype": int, "fil_val": 0, },
        'Example DICOM': {"dtype": str, "fil_val": "NONE", },
        'Series UID': {"dtype": str, "fil_val": "NONE", },
        'Study UID': {"dtype": str, "fil_val": "NONE", },
        'NIFTI in RawData': {"dtype": str, "fil_val": "NONE", },
        'NIFTI in BIDS': {"dtype": str, "fil_val": "NONE", },
    }


class StudyCsvData(BaseCsvData):
    unique_col_name: str = "StudyUID"
    setting: dict = {
        "Patient Name": {"dtype": str, "fil_val": "NONE", },
        'Patient ID': {"dtype": str, "fil_val": "NONE", },
        "Patient's Birth date": {"dtype": str, "fil_val": "NONE", },
        "Patient's Sex": {"dtype": str, "fil_val": "NONE", },
        "Patient's Age": {"dtype": str, "fil_val": "NONE", },
        "Patient's Size": {"dtype": str, "fil_val": "NONE", },
        "Patient's Weight": {"dtype": str, "fil_val": "NONE", },
        "Patient's Position": {"dtype": str, "fil_val": "NONE", },
        'Study Date': {"dtype": str, "fil_val": "NONE", },
        'Study Description': {"dtype": str, "fil_val": "NONE", },
        'Requesting physician': {"dtype": str, "fil_val": "NONE", },
        'Station': {"dtype": str, "fil_val": "NONE", },
        'Manufacturer': {"dtype": str, "fil_val": "NONE", },
        "Model": {"dtype": str, "fil_val": "NONE", },
        'Institution': {"dtype": str, "fil_val": "NONE", },
        'System': {"dtype": str, "fil_val": "NONE", },
        "Gradient": {"dtype": str, "fil_val": "NONE", },
        "PatAUSJID": {"dtype": str, "fil_val": "NONE", },
        'StudyUID': {"dtype": str, "fil_val": "NONE", },
    }


class DcmCsvData(BaseCsvData):
    unique_col_name: str = "File path"
    setting: dict = {
        'Series Number': {"dtype": int, "fil_val": "NONE", },
        'Instance Number': {"dtype": int, "fil_val": "NONE", },
        'File path': {"dtype": str, "fil_val": "NONE", },
        'Series UID': {"dtype": str, "fil_val": "NONE", },
    }

