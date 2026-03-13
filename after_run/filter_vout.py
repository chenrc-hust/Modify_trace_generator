import re
import sys

def process_log_line(line):
    """
    处理单行日志，返回符合格式的结果。
    """
    pattern = re.compile(r'^\[([R|W])\s([0-9a-f]+)\s([\d\.]+)\]$')
    line = line.strip()

    match = pattern.match(line)
    if match:
        rw_flag = match.group(1)  # 读写标志 ('R' 或 'W')
        hex_address = match.group(2)  # 十六进制地址
        formatted_address = f'0x{hex_address}'  # 格式化为带 0x 的地址
        return f"{rw_flag} {formatted_address}"
    return None

def process_log_file(input_file, output_file):
    """
    处理日志文件，逐行读取并过滤符合格式的行，单线程处理。
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            result = process_log_line(line)
            if result:
                outfile.write(result + '\n')

    print(f"Processing complete. Results saved to {output_file}.")

def main():
    # 检查是否提供了输入文件作为命令行参数
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <input_file.vout>")
        sys.exit(1)

    # 从命令行参数获取输入文件名
    input_file = sys.argv[1]

    # 确保输入文件后缀是 .vout
    if not input_file.endswith('.vout'):
        print("Error: Input file must have a .vout extension.")
        sys.exit(1)

    # 输出文件名，生成一个相同文件名但带 "_filtered" 后缀的文件
    output_file = input_file.replace('.vout', '_filtered.vout')

    # 处理日志文件
    process_log_file(input_file, output_file)

if __name__ == "__main__":
    main()
