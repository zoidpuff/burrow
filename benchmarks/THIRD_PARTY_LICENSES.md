# Third-party licenses of the converted site tables in benchmarks/

## LIGYSIS (benchmarks/ligysis/sites.tsv.gz; LIGYSIS_NI derived from it)

Adapted from the LIGYSIS human binding-site data of "LBS-Comparison results" (Zenodo 14645504,
https://doi.org/10.5281/zenodo.14645504), J. Sanchez Utges and G. J. Barton, licensed under the
Creative Commons Attribution 4.0 International license (CC-BY-4.0,
https://creativecommons.org/licenses/by/4.0/). Changes are listed in benchmarks/README.md.
Reference: Utges JS, Barton GJ. Comparative evaluation of methods for the prediction of
protein-ligand binding sites. J Cheminform 16, 126 (2024).

## CryptoBench (benchmarks/cryptobench/sites.tsv.gz)

Derived from CryptoBench (https://osf.io/pz4a9/, https://github.com/skrhakv/CryptoBench).
Reference: Skrhak V et al., Bioinformatics 41, btae745 (2025). License of the upstream repository:

```
MIT License

Copyright (c) 2024 Vít Škrhák

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## PocketWatch (benchmarks/pocketwatch/sites.tsv.gz)

Derived from PocketWatch (https://huggingface.co/datasets/genesisml/PocketWatch, revision
db7bd0611a14cb98e3b1d24b343565418b7193ef; zPocket paper, arXiv 2610.17696), released by its
authors under the MIT license (dataset card: "This dataset is released under the MIT licence").
No copyright line is given on the dataset card; the standard MIT terms apply:

```
MIT License

Copyright (c) the PocketWatch authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Our own tables

The AF-set and dimer tables, test union, clusters and entry lists are released with this
repository. They are built from the wwPDB (CC0), AlphaFold DB (CC-BY-4.0, Jumper et al. 2021;
Varadi et al. 2024), LIGYSIS (CC-BY-4.0, above) and BioLiP2 (freely available; Zhang et al.,
NAR 52:D404, 2024); please cite these resources.
