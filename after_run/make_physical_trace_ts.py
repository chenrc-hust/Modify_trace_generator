# 如果 .vout 追踪文件包含时间戳，请使用此脚本。
import matplotlib.pyplot as plt
import numpy as np
import sys

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
    """
    target = 0
    close = 50
    small = 0
    big = len(a) - 1
    for i in range(len(a)):
        if (a[i]) <x:
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

def output_vp_map(vp_map, output_file):
    """
    将虚拟到物理地址的映射表输出到文件。
    :param vp_map: 虚拟到物理地址的映射表
    :param output_file: 输出文件名
    """
    with open(output_file, 'w') as f:
        for vpn in vp_map:
            for entry in vp_map[vpn]:
                f.write(f"{hex(vpn)} -> {hex(entry[1])} at time {entry[0]:.6f}\n")
# 获取输入文件名
input_file_name = sys.argv[1]
# 计算输入文件的行数
linenum = file_len(input_file_name)
print("linenum of %s: %d" % (input_file_name, linenum))

# 检查输入文件的扩展名是否为 .mix
if input_file_name[-4:] != ".mix":
    print("input file [%s] is not .mix!" % (input_file_name))
    exit()

# 打开 .mix 文件
raw_trace_file = open(input_file_name, 'r')
# # 跳过文件的前七行
# for i in range(7):
#     line = raw_trace_file.readline()

i = 0
d = {}  # 初始化字典 d
d.clear()
item_idx = {}  # 初始化字典 item_idx
item_idx.clear()
item_cnt = 0  # 初始化计数器
map_cnt = 0
vpn_cnt = 0
exist_cnt = 0

# 创建虚拟到物理地址的映射表（字典）
while True:
    line = raw_trace_file.readline()
    if not line: break  # 如果没有更多行，退出循环
    if (i % (linenum // 1000)) == 0:  # 每处理 1000 行，打印进度
        print('\r', "%.0f%% [%d/%d]" % (i / linenum * 100, i, linenum), end="")

    # 统计 '[' 和 '{' 的数量
    num_cg = line.count('[')
    num_kn = line.count('{')
    num_total = num_cg + num_kn

    # 替换字符并删除换行符
    line = line.replace(']', '}').replace('[', '{').replace('}', ' ').replace('\n', ' ')

    # 根据 '{' 分割行内容并删除第一个元素
    splitline = line.split("{")
    del splitline[0]

    for item in splitline:
        # 根据空格分割每个项并去除多余的空格
        elem = item.split(" ")
        elem = ' '.join(elem).split()
        if elem[0] == 'R' or elem[0] == 'W':  # 如果元素是 'R' 或 'W'（读或写操作）
            cg_vaddr = int(elem[1], 16)  # 将虚拟地址从十六进制字符串转换为整数
        else:
            map_cnt += 1
            kn_vpn = int(elem[2], 16)  # 获取虚拟页号
            kn_pfn = int(elem[3], 16)  # 获取物理页号
            if kn_vpn in d:  # 如果 VPN 在字典 d 中
                d[kn_vpn].append([item_cnt, kn_pfn])  # 添加新的映射项
                exist_cnt += 1
            else:  # 如果 VPN 不在字典 d 中
                d[kn_vpn] = [[item_cnt, kn_pfn]]  # 创建新的映射项
                vpn_cnt += 1
        item_cnt += 1  # 增加处理过的项计数器

    i += 1

# 输出虚拟到物理地址的映射表到文件
vp_map_output_file = input_file_name[:-4] + "_vp_map.txt"
output_vp_map(d, vp_map_output_file)
# 第二次扫描，将 Valgrind 的虚拟内存追踪转换为物理内存追踪
output_file_name = input_file_name[:-4] + ".pout"  # 生成输出文件名
mem_trace = open(output_file_name, 'w')  # 打开输出文件
raw_trace_file.seek(0)  # 重置文件读取位置

# # 跳过文件的前七行
# for i in range(7):
#     line = raw_trace_file.readline()

i = 0
item_cnt = 0  # 初始化计数器
none_cnt = 0
ok_cnt = 0
find_flag = 0
variable_map_cnt = 0

while True:
    line = raw_trace_file.readline()
    if not line: break  # 如果没有更多行，退出循环
    if (i % (linenum // 1000)) == 0:  # 每处理 1000 行，打印进度
        print('\r', "%.0f%% [%d/%d]" % (i / linenum * 100, i, linenum), end="")

    # 替换字符并删除换行符
    line = line.replace(']', '}').replace('[', '{').replace('}', ' ').replace('\n', ' ')

    # 根据 '{' 分割行内容并删除第一个元素
    splitline = line.split("{")
    del splitline[0]

    for item in splitline:
        # 根据空格分割每个项并去除多余的空格
        elem = item.split(" ")
        elem = ' '.join(elem).split()
        
        if elem[0] == 'R' or elem[0] == 'W':  # 如果元素是 'R' 或 'W'（读或写操作）
            cg_vaddr = int(elem[1], 16)  # 将虚拟地址从十六进制字符串转换为整数
            cg_vpn = cg_vaddr // 4096  # 计算虚拟页号（VPN）
            cg_ofs = cg_vaddr & 0xfff  # 计算页内偏移量（offset）
            if( item_cnt>749000 and item_cnt<750000):
                print(elem[2]," ",item_cnt)
            if (d.get(cg_vpn) == None):  # 如果 VPN 不在字典 d 中
                none_cnt += 1  # 增加未找到映射的计数器
            else:  # 如果 VPN 在字典 d 中
                val = d[cg_vpn]  # 获取 VPN 对应的映射列表
                if len(val) > 1:  # 如果映射列表长度大于 1
                    idx_list = []  # 创建一个空的索引列表
                    for j in range(len(val)):  # 遍历映射列表
                        idx_list.append(val[j][0])  # 将时间戳添加到索引列表中
                    target_j = find_close_mapping(item_cnt, idx_list)  # 查找与当前时间戳最接近的索引
                    kn_pfn = val[target_j][1]  # 获取对应的物理页号（PFN）
                    variable_map_cnt += 1  # 增加可变映射计数器
                    if( item_cnt>749000 and item_cnt<750000):print(target_j)
                else:  # 如果映射列表长度等于 1
                    kn_pfn = val[0][1]  # 获取唯一的物理页号（PFN）
                    if( item_cnt>749000 and item_cnt<750000):print("one")
                if (kn_pfn == None):  # 如果 PFN 为 None
                    none_cnt += 1  # 增加未找到映射的计数器
                    print(hex(cg_vpn), "what?")  # 打印当前的虚拟页号
                    exit()  # 退出程序
                else:  # 如果 PFN 不为 None
                    paddr = kn_pfn * 4096 + cg_ofs  # 计算物理地址
                    mem_trace.write(elem[0] + " " + str(hex(paddr)) + " " + elem[2] + "\n")  # 写入输出文件
                    ok_cnt += 1  # 增加成功找到映射的计数器

        item_cnt += 1  # 增加处理过的项计数器

    i += 1

print("ok: %d, none: %d, (%.1f%%)" % (ok_cnt, none_cnt, (ok_cnt / (ok_cnt + none_cnt)) * 100.0))
# mem_trace.seek(0)
# mem_trace.write(str(ok_cnt) + " " + str(none_cnt) + " " + str((ok_cnt / (ok_cnt + none_cnt)) * 100.0))

raw_trace_file.close()  # 关闭输入文件
mem_trace.close()  # 关闭输出文件
