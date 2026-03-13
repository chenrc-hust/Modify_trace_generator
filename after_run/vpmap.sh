#!/bin/bash

OUT_DIR="/home/chen/hdd-1t"  # 指定输出目录
logfile="ramsmp_INTmem"                 # 指定日志文件名

# 确保输出目录存在
mkdir -p "$OUT_DIR"

# 打开文件描述符，使用 exec 命令将其与输出文件关联
exec 3>>"$OUT_DIR/$logfile.vpmap"

# 读取 vpmap 文件的内容，逐行写入
while IFS= read -r line
do
  echo "$line" >&3
done < /proc/vpmap/vpmap

# 关闭文件描述符
exec 3>&-

echo "File has been written to $OUT_DIR/$logfile.vpmap"
