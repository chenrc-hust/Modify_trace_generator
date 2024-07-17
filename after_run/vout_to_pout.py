import numpy as np
import sys
import bisect

sys.path.append('/home/whb/.local/lib/python3.8/site-packages')  # 根据实际路径调整
import matplotlib.pyplot as plt

def file_len(fname):
    """
    计算文件的行数。
    """
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def find_close_mapping(x, a):
    """
    查找与目标值 x 最接近的值在列表 a 中的索引。
    如果没有小于等于 x 的值，则返回第一个大于 x 的值。
    """
    pos = bisect.bisect_left(a, x)
    if pos == 0:
        return pos
    if pos == len(a):
        return pos - 1
    before = a[pos - 1]
    after = a[pos]
    if abs(after - x) < abs(x - before):
        return pos
    return pos - 1

def load_vpmap(vpmap_file_name):
    """
    加载 vpmap 文件，并将其内容存储在字典中。
    """
    vpmap = {}
    with open(vpmap_file_name, 'r') as vpmap_file:
        for line in vpmap_file:
            msline = line.replace('}', '').replace('\n', '').split(" ")
            map_ts = round(float(msline[-1]), 6)  # 获取时间戳并保留6位小数
            kn_vpn = int(msline[2], 16)  # 获取虚拟页号
            kn_pfn = int(msline[3], 16)  # 获取物理页号
            if kn_vpn not in vpmap:
                vpmap[kn_vpn] = []
            vpmap[kn_vpn].append((map_ts, kn_pfn))  # 将时间戳和物理页号存入字典中
    for vpn in vpmap:
        vpmap[vpn].sort()  # 确保每个 VPN 的映射列表按时间戳排序
    return vpmap

def main():
    input_file_name = sys.argv[1]  # 从命令行参数获取输入文件名
    vpmap_file_name = input_file_name[:-5] + ".vpmap"  # 生成对应的 .vpmap 文件名
    output_file_name = input_file_name[:-5] + ".pout"  # 生成输出文件名

    linenum = file_len(input_file_name)  # 获取 .vout 文件的行数
    print("linenum of %s: %d" % (input_file_name, linenum))

    try:
        raw_trace_file = open(input_file_name, 'r')  # 尝试打开 .vout 文件
    except:
        sys.stderr.write("No file: %s\n" % input_file_name)
        exit(1)

    try:
        vpmap = load_vpmap(vpmap_file_name)  # 加载 .vpmap 文件内容
    except:
        sys.stderr.write("No file: %s\n" % vpmap_file_name)
        exit(1)

    with open(output_file_name, 'w') as mem_trace:  # 打开输出文件
        i = 0
        item_cnt = 0
        none_cnt = 0
        ok_cnt = 0

        while True:
            line = raw_trace_file.readline()  # 从 .vout 文件读取一行
            if not line:
                break  # 如果读取到文件末尾，则退出循环

            if line[0] != "[" and line[0] != "R" and line[0] != "W":  # 跳过不以 '[' 或 'R' 或 'W' 开头的行
                i += 1
                continue

            if (i % (linenum // 1000)) == 0:
                print('\r', "%.0f%% [%d/%d]" % (i / linenum * 100, i, linenum), end="")

            line = line.replace(']', '}').replace('[', '{').replace('}', ' ').replace('\n', ' ')

            splitline = line.split("{")
            del splitline[0]

            for item in splitline:
                elem = item.split(" ")
                elem = ' '.join(elem).split()

                if elem[0] == 'R' or elem[0] == 'W':
                    cg_vaddr = int(elem[1], 16)
                    cg_vpn = cg_vaddr // 4096
                    cg_ofs = cg_vaddr & 0xfff
                    ts = round(float(elem[2]), 6)  # 获取时间戳并保留6位小数

                    if cg_vpn not in vpmap:
                        none_cnt += 1
                    else:
                        vpmap_entries = vpmap[cg_vpn]
                        idx_list = [entry[0] for entry in vpmap_entries]
                        target_idx = find_close_mapping(ts, idx_list)
                        
                        # 检查找到的映射是否在允许的时间跨度内
                        if target_idx is not None:
                            kn_pfn = vpmap_entries[target_idx][1]
                            paddr = kn_pfn * 4096 + cg_ofs
                            # mem_trace.write(f"{elem[0]} {hex(paddr)} {elem[2]}\n")
                            mem_trace.write(f"{elem[0]} {hex(paddr)}\n")
                            ok_cnt += 1
                        else:
                            none_cnt += 1

                item_cnt += 1

            i += 1

        print(f"ok: {ok_cnt}, none: {none_cnt}, ({(ok_cnt / (ok_cnt + none_cnt)) * 100:.1f}%)")

    raw_trace_file.close()

if __name__ == "__main__":
    main()
