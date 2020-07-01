# BCILDCMCONVERT

Converts DICOM to NIFTI, organizes the data into a study directory, and reads MRI scanning params useful for preprocessing brain imaging.

### Installation and Usage
1. Systtem requirements: linux, python3, nibabel 3.1.0, nampy 1.16.4 pydicom 2.0.0
2. Download BCILDCMCONVERT.zip and unzip
3. Run bcil_dcm_convert.py in the terminal

``` 
 usage:
 
 ex). $ python3 bcil_dcm_convert.py [option(s)] <Study dir> <Subject DICOM dir>
 
 Compulsory arguments:
 
 
 Optional arguments:
     -s       : 
```

Outputs are :


``` 
 usage:
 
 ex). $ python3 bcil_dcm_kspace_info.py <dicom full path
 
```

Outputs are :

### Dependencies
[dcm2niix][], [pydicom][],


### Aknowledgements
Yuta Urushibata



[dcm2niix]: https://github.com/rordenlab/dcm2niix "dcm2niix"
[pydicom]: https://github.com/pydicom/pydicom "pydicom"

### References
