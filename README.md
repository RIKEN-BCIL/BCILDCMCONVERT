# BCILDCMCONVERT

Converts DICOM to NIFTI, organizes the data into a study directory, and reads MRI scanning params useful for preprocessing brain imaging data with [HCP pipeline][] and [FSL][].

[HCP pipeline]: https://github.com/Washington-University/HCPpipelines "HCP pipeline"
[FSL]: https://fsl.fmrib.ox.ac.uk/fsl "FSL"

### Installation and Usage
1. System requirements: linux, python3, nibabel 3.1.0, nampy 1.16.4 pydicom 2.0.0, dcm2niix
2. Download BCILDCMCONVERT.zip and unzip
3. Run bcil_dcm_convert.py in the terminal

``` 
 usage:
 
 ex). $ bcil_dcm_convert.py [option(s)] <Study dir> <Subject DICOM dir>
 
 Compulsory arguments:
     <Study dir>           : full path to Study dir (parent dir) in which a new subject directory will be saved
     <Subject DICOM dir>   : full path to Subject dir including DICOM files 
 
 Optional arguments:
     -s  <Subject dirname> : subject dirname to be created in Study dir (by default, the dirname is automatically created)
     -o                    : overwrite Studyinfo.csv, Seriesinfo.csv, DICOMlist and NIFTI in <Subject dir>
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
Shinsuke Koike, Saori C Tanaka, Tomohisa Okada, Toshihiko Aso, Ayumu Yamashita, Okito Yamashita, Michiko Asano, Norihide Maikusa, Kentaro Morita, Naohiro Okada, Masaki Fukunaga, Akiko Uematsu, Hiroki Togo, Atsushi Miyazaki, Katsutoshi Murata, Yuta Urushibata, Joonas Autio, Takayuki Ose, Junichiro Yoshimoto, Toshiyuki Araki, Matthew F Glasser, David C Van Essen, Megumi Maruyama, Norihiro Sadato, Mitsuo Kawato, Kiyoto Kasai, Yasumasa Okamoto, Takashi Hanakawa, Takuya Hayashi. (in press) Brain/MINDS beyond human brain MRI project: A protocol for multi-level harmonization across brain disorders throughout the lifespan _**NeuroImage:Clinical**_  [DOI:10.1016/j.nicl.2021.102600][]

[DOI:10.1016/j.nicl.2021.102600]: https://doi.org/10.1016/j.nicl.2021.102600 "DOI: 10.1016/j.nicl.2021.102600"

