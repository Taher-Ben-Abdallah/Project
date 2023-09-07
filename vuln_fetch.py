import nvdlib

r = nvdlib.searchCVE(cveId='CVE-2017-0144')
print(r[0].score)
