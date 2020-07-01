# BCILDCMCONVERT

Converts DICOM to NIFTI, organizes the data into a study directory, and reads MRI scanning params useful for preprocessing brain imaging.

### Installation and Usage
1. Systtem requirements: linux, python3, nibabel 3.1.0, nampy 1.16.4 pydicom 2.0.0, dcm2niix
2. Download BCILDCMCONVERT.zip and unzip
3. Run bcil_dcm_convert.py in the terminal

``` 
 usage:
 
 ex). $ python3 bcil_dcm_convert.py [option(s)] <Study dir> <Subject DICOM dir>
 
 Compulsory arguments:
     <Study dir>           : full path to study dir (parent dir) in which a new subject directory will be saved
     <Subject DICOM dir>   : full path to ubject dir including DICOM files 
 
 Optional arguments:
     -s  <Subject dirname> : subject dirname to be created in Study dir (by default, the dirname is automatically created)
     -o                    : overwrite Studyinfo.csv, Seriesinfo.csv, DICOMlist and NIFTI in <Subject dir>
```

Example outputs are \<subject dir\> of which structure is:

\<Study dir\>/\<Subject dir\>
 `--RawData
    |-- DICOMlist 
    |-- NIFTI 
    |   |-- DICOM_AAHead_Scout_20190628133307_1.json
    |   |-- DICOM_AAHead_Scout_20190628133307_1.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_1a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_1a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00001.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00001.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00001a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00001a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00002.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00002.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00002a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00002a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00003.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00003.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00003a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00003a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00004.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00004.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00004a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_2_i00004a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00001.json
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00001.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00001a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00001a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00002.json
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00002.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00002a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00002a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00003.json
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00003.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00003a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_3_i00003a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00001.json
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00001.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00001a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00001a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00002.json
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00002.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00002a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00002a.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00003.json
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00003.nii
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00003a.json
    |   |-- DICOM_AAHead_Scout_20190628133307_4_i00003a.nii
    |   |-- DICOM_AC-PC_setup_20190628133307_5.json
    |   |-- DICOM_AC-PC_setup_20190628133307_5.nii
    |   |-- DICOM_AC-PC_setup_20190628133307_5a.json
    |   |-- DICOM_AC-PC_setup_20190628133307_5a.nii
    |   |-- DICOM_ASL_ADNI_20190628133307_14.json
    |   |-- DICOM_ASL_ADNI_20190628133307_14.nii
    |   |-- DICOM_ASL_ADNI_20190628133307_14a.json
    |   |-- DICOM_ASL_ADNI_20190628133307_14a.nii
    |   |-- DICOM_ASL_ADNI_20190628133307_15.json
    |   |-- DICOM_ASL_ADNI_20190628133307_15.nii
    |   |-- DICOM_ASL_ADNI_20190628133307_15a.json
    |   |-- DICOM_ASL_ADNI_20190628133307_15a.nii
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_7.json
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_7.nii
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_7a.json
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_7a.nii
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_8.json
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_8.nii
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_8a.json
    |   |-- DICOM_BOLD_REST1_AP_20190628133307_8a.nii
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_10.json
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_10.nii
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_10a.json
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_10a.nii
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_11.json
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_11.nii
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_11a.json
    |   |-- DICOM_BOLD_REST1_PA_20190628133307_11a.nii
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_23.json
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_23.nii
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_23a.json
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_23a.nii
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_24.json
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_24.nii
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_24a.json
    |   |-- DICOM_BOLD_REST2_AP_20190628133307_24a.nii
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_26.json
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_26.nii
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_26a.json
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_26a.nii
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_27.json
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_27.nii
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_27a.json
    |   |-- DICOM_BOLD_REST2_PA_20190628133307_27a.nii
    |   |-- DICOM_DWI_AP_20190628133307_18.json
    |   |-- DICOM_DWI_AP_20190628133307_18.nii
    |   |-- DICOM_DWI_AP_20190628133307_18a.json
    |   |-- DICOM_DWI_AP_20190628133307_18a.nii
    |   |-- DICOM_DWI_AP_20190628133307_19.bval
    |   |-- DICOM_DWI_AP_20190628133307_19.bvec
    |   |-- DICOM_DWI_AP_20190628133307_19.json
    |   |-- DICOM_DWI_AP_20190628133307_19.nii
    |   |-- DICOM_DWI_AP_20190628133307_19a.bval
    |   |-- DICOM_DWI_AP_20190628133307_19a.bvec
    |   |-- DICOM_DWI_AP_20190628133307_19a.json
    |   |-- DICOM_DWI_AP_20190628133307_19a.nii
    |   |-- DICOM_DWI_PA_20190628133307_20.json
    |   |-- DICOM_DWI_PA_20190628133307_20.nii
    |   |-- DICOM_DWI_PA_20190628133307_20a.json
    |   |-- DICOM_DWI_PA_20190628133307_20a.nii
    |   |-- DICOM_DWI_PA_20190628133307_21.bval
    |   |-- DICOM_DWI_PA_20190628133307_21.bvec
    |   |-- DICOM_DWI_PA_20190628133307_21.json
    |   |-- DICOM_DWI_PA_20190628133307_21.nii
    |   |-- DICOM_DWI_PA_20190628133307_21a.bval
    |   |-- DICOM_DWI_PA_20190628133307_21a.bvec
    |   |-- DICOM_DWI_PA_20190628133307_21a.json
    |   |-- DICOM_DWI_PA_20190628133307_21a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e1.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e1.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e1a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e1a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e2.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e2.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e2a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e2a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e3.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e3.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e3a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e3a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e4.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e4.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e4a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e4a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e5.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e5.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e5a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e5a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e6.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e6.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e6a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e6a.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e7.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e7.nii
    |   |-- DICOM_QSM_3D_20190628133307_16_e7a.json
    |   |-- DICOM_QSM_3D_20190628133307_16_e7a.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e1_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e1_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e1_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e1_pha.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e2_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e2_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e2_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e2_pha.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e3_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e3_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e3_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e3_pha.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e4_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e4_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e4_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e4_pha.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e5_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e5_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e5_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e5_pha.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e6_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e6_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e6_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e6_pha.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e7_ph.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e7_ph.nii
    |   |-- DICOM_QSM_3D_20190628133307_17_e7_pha.json
    |   |-- DICOM_QSM_3D_20190628133307_17_e7_pha.nii
    |   |-- DICOM_SEField1_AP_20190628133307_6.json
    |   |-- DICOM_SEField1_AP_20190628133307_6.nii
    |   |-- DICOM_SEField1_AP_20190628133307_6a.json
    |   |-- DICOM_SEField1_AP_20190628133307_6a.nii
    |   |-- DICOM_SEField1_PA_20190628133307_9.json
    |   |-- DICOM_SEField1_PA_20190628133307_9.nii
    |   |-- DICOM_SEField1_PA_20190628133307_9a.json
    |   |-- DICOM_SEField1_PA_20190628133307_9a.nii
    |   |-- DICOM_SEField2_AP_20190628133307_22.json
    |   |-- DICOM_SEField2_AP_20190628133307_22.nii
    |   |-- DICOM_SEField2_AP_20190628133307_22a.json
    |   |-- DICOM_SEField2_AP_20190628133307_22a.nii
    |   |-- DICOM_SEField2_PA_20190628133307_25.json
    |   |-- DICOM_SEField2_PA_20190628133307_25.nii
    |   |-- DICOM_SEField2_PA_20190628133307_25a.json
    |   |-- DICOM_SEField2_PA_20190628133307_25a.nii
    |   |-- DICOM_T1_MPR_20190628133307_12.json
    |   |-- DICOM_T1_MPR_20190628133307_12.nii
    |   |-- DICOM_T1_MPR_20190628133307_12a.json
    |   |-- DICOM_T1_MPR_20190628133307_12a.nii
    |   |-- DICOM_T2_SPC_20190628133307_13.json
    |   |-- DICOM_T2_SPC_20190628133307_13.nii
    |   |-- DICOM_T2_SPC_20190628133307_13a.json
    |   `-- DICOM_T2_SPC_20190628133307_13a.nii
    |-- Seriesinfo.csv 
    `-- Studyinfo.csv 


``` 
 usage:
 
 ex). $ python3 bcil_dcm_kspace_info.py <dicom full path
 
```

Outputs are :

### Dependencies
[dcm2niix][], [pydicom][], [dibabel][]

### Aknowledgements
We thank Yuta Urushibata for his help in analyzing DICOM files

### License
BCILDCMCONVERT is licensed under the terms of the MIT license.

[dcm2niix]: https://github.com/rordenlab/dcm2niix "dcm2niix"
[pydicom]: https://github.com/pydicom/pydicom "pydicom"
[dibabel]: https://github.com/nyurik/dibabel "dibabel"

### References
Brain/MINDS Beyond Human Brain MRI Study: A Protocol of Multi-Site Harmonization for Brain Disorders Throughout the Lifespan bioRxiv
doi: https://doi.org/10.1101/2020.05.05.076273
