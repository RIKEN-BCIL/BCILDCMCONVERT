# BCILDCMCONVERT

Converts DICOM to NIFTI, organizes the data into a study directory, and reads MRI scanning params useful for preprocessing brain imaging.

### Installation and Usage
1. System requirements: linux, python3, nibabel 3.1.0, nampy 1.16.4 pydicom 2.0.0, dcm2niix
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

```
<Study dir>/<Subject dir>  
 `--RawData  
    |-- DICOMlist   
    |-- NIFTI  
    |-- Seriesinfo.csv  
    `-- Studyinfo.csv  
```

Detailes of example outputs and contents of Seriesinfo.csv and Studyinfo.csv are desribed at [wiki][]

[wiki]: https://github.com/RIKEN-BCIL/BCILDCMCONVERT/wiki "wiki"


### Dependencies
[dcm2niix][], [pydicom][], [nibabel][]

### Aknowledgements
We thank Yuta Urushibata for his help in analyzing DICOM files and verifying by phantom experiments.

### License
BCILDCMCONVERT is licensed under the terms of the MIT license.

[dcm2niix]: https://github.com/rordenlab/dcm2niix "dcm2niix"
[pydicom]: https://github.com/pydicom/pydicom "pydicom"
[nibabel]: https://github.com/nipy/nibabel "nibabel"

### References
Shinsuke Koike, Saori C Tanaka, Tomohisa Okada, Toshihiko Aso, Michiko Asano, Norihide Maikusa, Kentaro Morita, Naohiro Okada, Masaki Fukunaga, Akiko Uematsu, Hiroki Togo, Atsushi Miyazaki, Katsutoshi Murata, Yuta Urushibata, Joonas Autio, Takayuki Ose, Junichiro Yoshimoto, Toshiyuki Araki, Matthew F Glasser, David C Van Essen, Megumi Maruyama, Norihiro Sadato, Mitsuo Kawato, Kiyoto Kasai, Yasumasa Okamoto, Takashi Hanakawa, Takuya Hayashi. (2020) Brain/MINDS Beyond Human Brain MRI GroupBrain/MINDS Beyond Human Brain MRI Study: A Protocol of Multi-Site Harmonization for Brain Disorders Throughout the Lifespan _**bioRxiv**_  
https://doi.org/10.1101/2020.05.05.076273

