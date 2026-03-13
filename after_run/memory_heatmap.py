import re
import sys
import os
from concurrent.futures import ProcessPoolExecutor

def process_log_line(line):
    """
    处理单行日志，返回符合格式的结果。
    """
    pattern = re.compile(r'^([R|W])\s(0x[0-9a-f]+)$')
    line = line.strip()

    match = pattern.match(line)
    if match:
        hex_address = match.group(2)  # 带 0x 的十六进制地址
        address = int(hex_address, 16)  # 转换为十六进制的整数地址
        return address
    else:
        return None

def process_chunk(lines, block_size=4096):
    """
    处理文件的一部分（行块），并统计每个内存地址的访问次数。
    """
    address_count = {}
    for line in lines:
        address = process_log_line(line)
        if address:
            # 按块划分，例如每4KB一个块
            block_address = address // block_size
            if block_address not in address_count:
                address_count[block_address] = 0
            address_count[block_address] += 1
    return address_count

def merge_dictionaries(dicts):
    """
    合并多个字典，将相同键的值累加。
    """
    merged = {}
    for d in dicts:
        for key, value in d.items():
            if key not in merged:
                merged[key] = 0
            merged[key] += value
    return merged

def process_log_file_multiprocess(input_file, chunk_size=100000, block_size=4096, max_workers=20):
    """
    处理日志文件，逐行读取并统计每个内存地址的访问次数，使用多进程处理。
    """
    total_lines = 0
    chunks = []
    results = []

    with open(input_file, 'r') as infile:
        chunk = []
        for line in infile:
            chunk.append(line)
            if len(chunk) >= chunk_size:
                chunks.append(chunk)
                chunk = []
            total_lines += 1

        # 提交最后的块
        if chunk:
            chunks.append(chunk)

    print(f"Total chunks to process: {len(chunks)}")  # 调试信息

    # 使用多进程处理文件块
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk, chunk, block_size) for chunk in chunks]

        # 收集结果
        for future in futures:
            results.append(future.result())

    # 合并所有进程的结果
    address_count = merge_dictionaries(results)

    return address_count

def output_access_distribution(address_count, output_file, scale=100000000):
    """
    根据地址访问计数输出每个页地址，并使用 '|' 表示访问次数百分比。
    """
    total_accesses = sum(address_count.values())
    
    if total_accesses == 0:
        print("No accesses found.")
        return

    with open(output_file, 'w') as outfile:
        for address in sorted(address_count.keys()):
            access_count = address_count[address]
            percentage = (access_count / total_accesses) * scale
            bars = '|' * int(percentage)  # 以百分比生成相应数量的 '|'
            outfile.write(f"0x{address:x} {bars} ({access_count} accesses)\n")

    print(f"Results saved to {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <input_file.pout>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not input_file.endswith('.pout'):
        print("Error: Input file must have a .pout extension.")
        sys.exit(1)

    output_file = input_file.replace('.pout', '_access_distribution.txt')

    # 处理日志文件并生成地址访问计数
    print("Processing log file...")
    address_count = process_log_file_multiprocess(input_file)

    if not address_count:
        print("No valid log lines processed.")
        sys.exit(1)

    # 输出每个页地址的访问计数，用 '|' 表示百分比
    print("Generating access distribution output...")
    output_access_distribution(address_count, output_file)

if __name__ == "__main__":
    main()
