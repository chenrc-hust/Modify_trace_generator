import logging
import sys
import os
import numpy as np
import collections
import multiprocessing as mp

sys.path.append('/home/whb/.local/lib/python3.8/site-packages')
import matplotlib.pyplot as plt

# 配置日志记录
logging.basicConfig(filename='/mnt/sdb/out/mix_parallel.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def read_lines_in_chunks(filename, start_line, end_line):
    lines = []
    with open(filename, 'r') as f:
        for current_line_num, line in enumerate(f):
            if start_line <= current_line_num < end_line:
                lines.append(line)
            if current_line_num >= end_line:
                break
    return lines

def process_chunk(chunk, vpmap_file_name):
    mixed_lines = []
    with open(vpmap_file_name, 'r') as vpmap_file:
        vpmap_lines = vpmap_file.readlines()
    
    vpmap_end = 0
    vpmap_index = 0
    for line in chunk:
        if line[0] != "[":
            continue
        
        sline = line.replace(']', '}').replace('\n', '').split(" ")
        ts = float(sline[-1])

        while vpmap_end == 0:
            if vpmap_index >= len(vpmap_lines):
                vpmap_end = 1
                break

            mline = vpmap_lines[vpmap_index]
            msline = mline.replace('}', '').replace('\n', '').split(" ")
            map_ts = float(msline[-1])
            if map_ts < ts:
                mixed_lines.append(mline)
                vpmap_index += 1
            else:
                break
        mixed_lines.append(line)
    
    return mixed_lines

def worker(input_file_name, start, end, vpmap_file_name, linenum, progress_queue):
    logging.debug(f"Worker started: start={start}, end={end}")
    chunk = read_lines_in_chunks(input_file_name, start, end)
    result = process_chunk(chunk, vpmap_file_name)
    progress_queue.put(len(chunk))  # Put the number of processed lines to the queue
    logging.debug(f"Worker finished: start={start}, end={end}")
    return result

def main():
    input_file_name = sys.argv[1]
    if input_file_name[-5:] != ".vout":
        print("input file [%s] is not .vout!" % (input_file_name))
        exit()
    linenum = file_len(input_file_name)
    print("linenum of %s: %d" % (input_file_name, linenum))

    try:
        raw_trace_file = open(input_file_name, 'r')
    except FileNotFoundError:
        sys.stderr.write("No file: %s\n" % input_file_name)
        exit(1)
    
    for _ in range(7):
        line = raw_trace_file.readline()

    vpmap_file_name = input_file_name[:-5] + ".vpmap"
    print("vpmap fname:", vpmap_file_name)

    try:
        open(vpmap_file_name, 'r')
    except FileNotFoundError:
        sys.stderr.write("No file: %s\n" % vpmap_file_name)
        exit(1)

    output_file_name = os.path.join('/mnt/sdb/out', os.path.basename(input_file_name[:-5] + ".mix"))

    # 检查输出目录的权限
    output_dir = os.path.dirname(output_file_name)
    if not os.access(output_dir, os.W_OK):
        sys.stderr.write("No write permission for directory: %s\n" % output_dir)
        exit(1)

    try:
        mixed_file = open(output_file_name, 'w')
    except PermissionError as e:
        sys.stderr.write("PermissionError: %s\n" % str(e))
        exit(1)

    # 分块读取和处理
    chunk_size = 100000  # 每个块包含的行数
    num_chunks = (linenum // chunk_size) + 1

    cpu_count = mp.cpu_count()
    print(f"Using {cpu_count} CPU cores for processing.")
    logging.debug(f"Using {cpu_count} CPU cores for processing.")

    pool = mp.Pool(cpu_count)
    progress_queue = mp.Queue()
    futures = []

    for chunk_idx in range(num_chunks):
        start_line = chunk_idx * chunk_size
        end_line = min(start_line + chunk_size, linenum)
        futures.append(pool.apply_async(worker, args=(input_file_name, start_line, end_line, vpmap_file_name, linenum, progress_queue)))

    # Progress display
    total_processed = 0
    while total_processed < linenum:
        processed = progress_queue.get()
        total_processed += processed
        progress = (total_processed / linenum) * 100
        print(f'\rProcessing... {progress:.2f}% [{total_processed}/{linenum}]', end='')

    pool.close()
    pool.join()

    for future in futures:
        mixed_lines = future.get()
        mixed_file.writelines(mixed_lines)

    print("\nProcessing complete.")
    raw_trace_file.close()
    mixed_file.close()
    logging.debug("Processing complete.")

if __name__ == "__main__":
    main()
