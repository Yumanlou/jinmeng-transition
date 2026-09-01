# -*- coding: utf-8 -*-
"""
Created on Sun May  4 14:12:05 2025

@author: David Zong
"""

import os
import lzma


def unzip_text_file(compressed_file_path, output_folder):
    # open the compressed file
    with lzma.open(compressed_file_path, 'rb') as f:
        decompressed_data = f.read()
    decompressed_text = decompressed_data.decode('utf-8')

    # split file and text 
    info_part, text_part = decompressed_text.split('\n\n', 1)
    file_info = [line.split(',') for line in info_part.split('\n')]

    # create output folder 
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # restore all files 
    for file_name, start_str, end_str in file_info:
        start = int(start_str)
        end = int(end_str)
        file_text = text_part[start:end]
        output_file_path = os.path.join(output_folder, file_name)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(file_text)






if __name__ == "__main__":
    compressed_file = r'H:\compessed gov report.xz'  
    output_folder = r'H:\restored_folder'  
    unzip_text_file(compressed_file, output_folder)
    