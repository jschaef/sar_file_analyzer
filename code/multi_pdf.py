#!/usr/bin/python3

import os
from PyPDF4 import PdfFileMerger

def create_multi_pdf(pdf_field: list, outfile: str):
    rm_field = pdf_field.copy()
    merger = PdfFileMerger()
    while len(pdf_field) > 0:
        input = open(pdf_field.pop(0), "rb")
        merger.append(input)
    output = open(outfile, 'wb')
    merger.write(output)
    output.close()
    for file in rm_field:
        os.remove(file)
    return outfile
