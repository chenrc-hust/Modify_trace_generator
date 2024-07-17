import numpy as np
import sys
import collections
import multiprocessing as mp
import os

sys.path.append('/home/whb/.local/lib/python3.8/site-packages')  # 根据实际路径调整
import matplotlib.pyplot as plt

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def find_close_mapping(x, a):
    target = 0
    close = 50
    small = 0
    big = len(a) - 1
    for i in range(len(a)):
        if (a[i]) < x:
            small = i
        if a[i] >= x:
            big = i
            break
    diff_s = x - a[small]
    diff_b = a[big] - x

    if small == 0 and big == 0:
        target = small
    elif small == big and small > 0:
        target = big
    else:
        if diff_s < 0 or diff_b < 0:
            print("Error (diff_s: %d, diff_b: %d)" % (diff_s, diff_b))
        elif diff_s < close and diff_b < close:
            target = small if diff_s <= diff_b else big
        elif diff_s < close:
            target = small
        elif diff_b < close:
            target = big
    return target

def process_mapping(lines):
    d = collections.defaultdict(list)
    item_cnt = 0
    map_cnt = 0
    vpn_cnt = 0
    exist_cnt = 0

    for line in lines:
        line = line.replace(']', '}').replace('[', '{').replace('}', ' ').replace('\n', ' ')
        splitline = line.split("{")[1:]

        for item in splitline:
            elem = ' '.join(item.split()).split()
            if elem[0] not in {'R', 'W'}:
                map_cnt += 1
                kn_vpn = int(elem[2], 16)
                kn_pfn = int(elem[3], 16)
                d[kn_vpn].append((item_cnt, kn_pfn))
                vpn_cnt += 1 if len(d[kn_vpn]) == 1 else 0
                exist_cnt += 1 if len(d[kn_vpn]) > 1 else 0
            item_cnt += 1
    return d

def worker(input_file_name, start, end):
    with open(input_file_name, 'r') as raw_trace_file:
        for _ in range(7):
            next(raw_trace_file)

        # Skip to start position
        for _ in range(start):
            raw_trace_file.readline()

        lines = []
        for _ in range(end - start):
            line = raw_trace_file.readline()
            if not line:
                break
            lines.append(line)

    return process_mapping(lines)

def process_lines(lines, d, linenum):
    none_cnt = 0
    ok_cnt = 0
    output_lines = []
    item_cnt = 0

    for line in lines:
        line = line.replace(']', '}').replace('[', '{').replace('}', ' ').replace('\n', ' ')
        splitline = line.split("{")[1:]

        for item in splitline:
            elem = ' '.join(item.split()).split()
            if elem[0] in {'R', 'W'}:
                cg_vaddr = int(elem[1], 16)
                cg_vpn = cg_vaddr // 4096
                cg_ofs = cg_vaddr & 0xfff

                if cg_vpn not in d:
                    none_cnt += 1
                else:
                    val = d[cg_vpn]
                    kn_pfn = val[find_close_mapping(item_cnt, [v[0] for v in val])][1] if len(val) > 1 else val[0][1]
                    paddr = kn_pfn * 4096 + cg_ofs
                    output_lines.append(f"{elem[0]} {hex(paddr)} {elem[2]}\n")
                    ok_cnt += 1
            item_cnt += 1

    return output_lines, ok_cnt, none_cnt

def worker_processing(input_file_name, start, end, final_mapping, linenum):
    with open(input_file_name, 'r') as raw_trace_file:
        for _ in range(7):
            next(raw_trace_file)

        # Skip to start position
        for _ in range(start):
            raw_trace_file.readline()

        lines = []
        for _ in range(end - start):
            line = raw_trace_file.readline()
            if not line:
                break
            lines.append(line)

    return process_lines(lines, final_mapping, linenum)

def main(input_file_name):
    linenum = file_len(input_file_name)
    print("linenum of %s: %d" % (input_file_name, linenum))

    if input_file_name[-4:] != ".mix":
        print("input file [%s] is not .mix!" % (input_file_name))
        exit()

    cpu_count = mp.cpu_count()
    print(f"Using {cpu_count} CPU cores for processing.")

    pool = mp.Pool(cpu_count)
    chunk_size = linenum // cpu_count
    mapping_results = []

    for i in range(cpu_count):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != cpu_count - 1 else linenum
        mapping_results.append(pool.apply_async(worker, args=(input_file_name, start, end)))

    pool.close()
    pool.join()

    # 合并所有子进程的结果
    final_mapping = collections.defaultdict(list)
    for result in mapping_results:
        partial_mapping = result.get()
        for kn_vpn, values in partial_mapping.items():
            final_mapping[kn_vpn].extend(values)

    print("Finished creating v2p map.")

    file_base_name = input_file_name.split('/')[-1][:-4]
    output_file_name = f"/mnt/sdb/pout/{file_base_name}.pout"
    print("output_file_name :", output_file_name)

    pool = mp.Pool(cpu_count)
    results = []

    for i in range(cpu_count):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != cpu_count - 1 else linenum
        results.append(pool.apply_async(worker_processing, args=(input_file_name, start, end, final_mapping, linenum)))

    pool.close()
    pool.join()

    with open(output_file_name, 'w') as mem_trace:
        total_ok_cnt = 0
        total_none_cnt = 0

        for result in results:
            output_lines, ok_cnt, none_cnt = result.get()
            mem_trace.writelines(output_lines)
            total_ok_cnt += ok_cnt
            total_none_cnt += none_cnt

        print("ok: %d, none: %d, (%.1f%%)" % (total_ok_cnt, total_none_cnt, (total_ok_cnt / (total_ok_cnt + total_none_cnt)) * 100.0))

if __name__ == "__main__":
    main(sys.argv[1])
