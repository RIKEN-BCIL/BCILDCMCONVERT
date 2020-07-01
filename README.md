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
     -o                    : overwrite Studyinfo.csv, Seriesinfo.csv, DICOMlist and NIFTI in <subject dir>
```

Outputs are :


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
