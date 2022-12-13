#!/usr/bin/python3
# coding:utf-8
import dcm2bids.dcm2bids
from dcm2bids import Dcm2bids
from bcil_dcm_convert import BcilDcmConvert
import os
import glob
import hashlib
import pandas as pd


if __name__ == "__main__":

    # bids 実行
    try:
        args = dcm2bids.dcm2bids.get_arguments()
        if args.anonymizer:
            print(
                """
            The anonymizer option no longer exists from the script in this release
            It is still possible to deface the anatomical nifti images
            Please add "defaceTpl" key in the congifuration file
    
            For example, if you use the last version of pydeface, add:
            "defaceTpl": "pydeface --outfile {dstFile} {srcFile}"
            It is a template string and dcm2bids will replace {srcFile} and {dstFile}
            by the source file (input) and the destination file (output)
            """
            )
            exit(1)

        app = Dcm2bids(**vars(args))
        app.run()

    except Exception as e:
        print('***dcm2bids error***')
        print(e)

    try:
        print('***bcil_convert start***')
        app_dir = os.path.abspath(app.bidsDir)
        app_dir += "" if app_dir.endswith(os.sep) else os.sep

        if len(app.participant.session) > 0:  # セッションあり
            convert_save_dir = app_dir + app.participant.name + os.sep
            subject_name = app.participant.session
            tmp_dir = app_dir + "tmp_dcm2bids" + os.sep + app.participant.name + r"_" + app.participant.session
        else:  # セッションなし
            convert_save_dir = app_dir
            subject_name = app.participant.name
            tmp_dir = app_dir + "tmp_dcm2bids" + os.sep + app.participant.name

        dirs = app.dicomDirs
        del app

        for srcDir in dirs:
            num = 0

            bc = BcilDcmConvert(
                dcm_dir=srcDir + os.sep,
                save_parent_dir=convert_save_dir,
                create_nifti=True,
                subject_name=subject_name,
                overwrite=2,
                display_progress=False,
                gz=True,
            )
            bc.main()

        bids_nifti_hash_list = {}
        sub_dir = (convert_save_dir + subject_name + os.sep)

        # NIFTI in BIDS list
        bids_nifti_list = glob.glob(sub_dir + r"**" + os.sep + "*.nii")
        bids_nifti_list.extend(glob.glob(sub_dir + r"**" + os.sep + "*.nii.gz"))
        bids_nifti_list.extend(glob.glob(tmp_dir + os.sep + "*.nii"))
        bids_nifti_list.extend(glob.glob(tmp_dir + os.sep + "*.nii.gz"))

        for bids_nifti in bids_nifti_list:
            nf = open(bids_nifti, 'rb').read()
            h = hashlib.sha256(nf).hexdigest()
            bids_nifti_hash_list[h] = bids_nifti

        # NIFTI in RawData
        test = {}
        series = pd.read_csv(sub_dir + os.sep + r"RawData/Seriesinfo.csv", dtype=str)
        for index, item in series.iterrows():
            bids_nifti_ary = []
            raw_data_nifti_list = item['NIFTI in RawData'].split(" ")
            for raw_data_nifti in raw_data_nifti_list:
                nf = open(raw_data_nifti, 'rb').read()
                h = hashlib.sha256(nf).hexdigest()
                bids_nifti_ary.append(bids_nifti_hash_list[h])

            series.at[index, 'NIFTI in BIDS'] = " ".join(bids_nifti_ary)

        series.to_csv(sub_dir + os.sep + r"RawData/Seriesinfo.csv", index=False)

    except Exception as e:
        print('***bcil_convert error***')
        print(e)


