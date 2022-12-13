# BCILDCMCONVERT

BCILDCMCONVERT converts DICOM from various MRI scanners to NIFTI volumes, organizes the data into a study directory, and stores MRI scanning params useful for preprocessing brain imaging data with [HCP pipeline][] and [FSL][]. It achieves high traceability, practicality, and reproducibility needed for high-quality MRI data analysis.

[HCP pipeline]: https://github.com/Washington-University/HCPpipelines "HCP pipeline"
[FSL]: https://fsl.fmrib.ox.ac.uk/fsl "FSL"


### Supported MRI scanners
Siemens 3T MRI scanner (MAGNETOME Trio, MAGNETOME Verio, MAGNETOME Skyra, MAGNETOME Prisma)

### Installation and Usage
1. System requirements: linux, python3, nibabel 3.1.0, numpy 1.16.4 pydicom 2.0.0, dcm2niix
2. Download BCILDCMCONVERT.zip and unzip
3. Run bcil_dcm_convert.py in the terminal

``` 
usage:

  ex). $ python3 bcil_dcm_convert.py [option(s)] <saveDir> <dcmDir>

positional arguments:
  saveDir              path to study dir (parent dir) in which a new subject directory will be saved
  dcmDir               path to subject dir including DICOM files

optional arguments:
  -h, --help           show this help message and exit
  -p, --progress       show progress bar
  -n, --no_nii         do not convert to NIFTI
  -s subject name      give an alias to the subject directory
  -w overwrite option  <num> overwrite options (0:do not overwrite, 1:replace, 2:append, default is 0)
  -z, --gz             compress NIFTI volumes with .gz (default is not compressed, and saved as .nii)
  -u unzip_dir_path    path to unzip dir. unzipped files will be deleted after processing. default is current dir

```

Example outputs are \<subject dir\> of which structure is as follows:

```
<Study dir>/<Subject dir>  
 `--RawData  
    |-- DICOMlist.txt   
    |-- NIFTI  
    |-- Seriesinfo.csv  
    `-- Studyinfo.csv  
```

- DICOMlist: a text listing input DICOM directories, which may be useful to track the original DICOM data.  
- NIFTI: sub-directory including all the NIFTI volumes converted from DICOM in the input \<Subject DICOM dir\>.  
- Seriesinfo.csv: major scanning parameters of each sequnce series. It includes dwell time in read and phase and their directions (in subject's coordinates), which are needed to correct distortion of images.  
- Studyinfo.csv: information on study, patients, and MRI scanners. It also inludes a type of gradient coil, which is needed when applying non-linear gradient distortion.  
  
Detailes and examples of Seriesinfo.csv, Studyinfo.csv and NIFTI directory are desribed at [wiki][]

[wiki]: https://github.com/RIKEN-BCIL/BCILDCMCONVERT/wiki "wiki"


### Dependencies
[dcm2niix][], [pydicom][], [nibabel][]

### Aknowledgements
We thank Yuta Urushibata for his help in analyzing DICOM files and verifying DICOM info by phantom experiments.

### License
BCILDCMCONVERT is licensed under the terms of the MIT license.

[dcm2niix]: https://github.com/rordenlab/dcm2niix "dcm2niix"
[pydicom]: https://github.com/pydicom/pydicom "pydicom"
[nibabel]: https://github.com/nipy/nibabel "nibabel"

### References
Koike, S., Tanaka, S.C., Okada, T., Aso, T., Yamashita, A., Yamashita, O., Asano, M., Maikusa, N., Morita, K., Okada, N., Fukunaga, M., Uematsu, A., Togo, H., Miyazaki, A., Murata, K., Urushibata, Y., Autio, J., Ose, T., Yoshimoto, J., Araki, T., Glasser, M.F., Van Essen, D.C., Maruyama, M., Sadato, N., Kawato, M., Kasai, K., Okamoto, Y., Hanakawa, T., Hayashi, T., 2021. Brain/MINDS beyond human brain MRI project: A protocol for multi-level harmonization across brain disorders throughout the lifespan. _**NeuroImage: Clinical**_ 30, 102600. [DOI][]

[DOI]: https://doi.org/10.1016/j.nicl.2021.102600 "DOI"

