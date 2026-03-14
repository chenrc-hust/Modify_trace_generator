#!/bin/bash
#
# spec_trace_generator_11-6.sh - 使用 trace_generator 抓取 SPEC CPU 内存 trace
#
# 功能: 遍历 SPEC CPU benchmark，使用 valgrind callgrind 抓取内存访问 trace
#       支持 SPEC CPU 2017 和 2006
#
# 用法: 直接运行 (无参数，输出到 hdd-1t)
#
# 注意: 需要 sudo 权限 (valgrind trace 抓取需要 root)
#       每个 benchmark 运行 3600 秒后自动终止

set -euo pipefail

# ===== 路径配置 =====
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
tooldir="$(cd "$SCRIPT_DIR/.." && pwd)"

# SPEC CPU 配置
# --- SPEC CPU 2017 ---
spec_version="2017"
spec_base_dir="/home/chen/speccpu2017/benchspec/CPU"
spec_run_suffix="run/run_base_refrate_mytest-m64.0000"
# --- SPEC CPU 2006 ---
# spec_version="2006"
# spec_base_dir="/home/chen/spec2006"
# spec_run_suffix=""

# 输出目录
output_dir="/home/chen/hdd-1t"

# ===== SPEC 测试命令定义 =====
declare -A spec_commands
declare -A spec_dirs

if [ "$spec_version" = "2017" ]; then
  # SPEC CPU 2017 (已编译的 benchmark)
  # --input 指定可执行文件，后面跟参数
  spec_dirs[mcf]="505.mcf_r"
  spec_commands[mcf]="--input ./mcf_r_base.mytest-m64 inp.in"

  spec_dirs[lbm]="519.lbm_r"
  spec_commands[lbm]="--input ./lbm_r_base.mytest-m64 3000 reference.dat 0 0 100_100_130_ldc.of"

  spec_dirs[perlbench]="500.perlbench_r"
  spec_commands[perlbench]="--input ./perlbench_r_base.mytest-m64 -I./lib splitmail.pl 6400 12 26 16 100 0"

  spec_dirs[namd]="508.namd_r"
  spec_commands[namd]="--input ./namd_r_base.mytest-m64 --input apoa1.input --output apoa1.ref.output --iterations 65"

  spec_dirs[cactuBSSN]="507.cactuBSSN_r"
  spec_commands[cactuBSSN]="--input ./cactusBSSN_r_base.mytest-m64 spec_ref.par"

  spec_dirs[parest]="510.parest_r"
  spec_commands[parest]="--input ./parest_r_base.mytest-m64 ref.prm"

  spec_dirs[povray]="511.povray_r"
  spec_commands[povray]="--input ./povray_r_base.mytest-m64 SPEC-benchmark-ref.ini"

  # 未编译:
  # spec_dirs[omnetpp]="520.omnetpp_r"
  # spec_commands[omnetpp]="--input ./omnetpp_r_base.mytest-m64 -c General -r 0"
  # spec_dirs[deepsjeng]="531.deepsjeng_r"
  # spec_commands[deepsjeng]="--input ./deepsjeng_r_base.mytest-m64 ref.txt"
  # spec_dirs[xalancbmk]="523.xalancbmk_r"
  # spec_commands[xalancbmk]="--input ./xalancbmk_r_base.mytest-m64 -v t5.xml xalanc.xsl"

else
  # SPEC CPU 2006
  spec_dirs[astar]="astar"
  spec_commands[astar]="--input ./astar_base.x86_64_sse rivers.cfg"
  spec_dirs[bzip2]="bzip2"
  spec_commands[bzip2]="--input ./bzip2_base.x86_64_sse input/input.source 280"
  spec_dirs[cactusADM]="cactusADM"
  spec_commands[cactusADM]="--input ./cactusADM_base.x86_64_sse benchADM.par"
  spec_dirs[calculix]="calculix"
  spec_commands[calculix]="--input ./calculix_base.x86_64_sse hyperviscoplastic"
  spec_dirs[dealII]="dealII"
  spec_commands[dealII]="--input ./dealII_base.x86_64_sse 23"
  spec_dirs[gamess]="gamess"
  spec_commands[gamess]="--shuru input/triazolium.config --input ./gamess_base.x86_64_sse"
  spec_dirs[gcc]="gcc"
  spec_commands[gcc]="--input ./gcc_base.x86_64_sse input/scilab.i -o scilab.s"
  spec_dirs[GemsFDTD]="GemsFDTD"
  spec_commands[GemsFDTD]="--input ./GemsFDTD_base.x86_64_sse"
  spec_dirs[gobmk]="gobmk"
  spec_commands[gobmk]="--shuru input/score2.tst --input ./gobmk_base.x86_64_sse --quiet --mode gtp"
  spec_dirs[gromacs]="gromacs"
  spec_commands[gromacs]="--input ./gromacs_base.x86_64_sse -silent -deffnm input/gromacs -nice 0"
  spec_dirs[h264ref]="h264ref"
  spec_commands[h264ref]="--input ./h264ref_base.x86_64_sse -d input/sss_encoder_main.cfg"
  spec_dirs[hmmer]="hmmer"
  spec_commands[hmmer]="--input ./hmmer_base.x86_64_sse input/nph3.hmm input/swiss41"
  spec_dirs[lbm]="lbm"
  spec_commands[lbm]="--input ./lbm_base.x86_64_sse 3000 reference.dat 0 0 100_100_130_ldc.of"
  spec_dirs[leslie3d]="leslie3d"
  spec_commands[leslie3d]="--shuru leslie3d.in --input ./leslie3d_base.x86_64_sse"
  spec_dirs[libquantum]="libquantum"
  spec_commands[libquantum]="--input ./libquantum_base.x86_64_sse 1397 8"
  spec_dirs[mcf]="mcf"
  spec_commands[mcf]="--input ./mcf_base.x86_64_sse inp.in"
  spec_dirs[milc]="milc"
  spec_commands[milc]="--shuru input/su3imp.in --input ./milc_base.x86_64_sse"
  spec_dirs[namd]="namd"
  spec_commands[namd]="--input ./namd_base.x86_64_sse --input input/namd.input --iterations 38 --output namd.out"
  spec_dirs[omnetpp]="omnetpp"
  spec_commands[omnetpp]="--input ./omnetpp_base.x86_64_sse omnetpp.ini"
  spec_dirs[perlbench]="perlbench"
  spec_commands[perlbench]="--input ./perlbench_base.x86_64_sse -Ilib checkspam.pl 2500 5 25 11 150 1 1 1 1"
  spec_dirs[povray]="povray"
  spec_commands[povray]="--input ./povray_base.x86_64_sse SPEC-benchmark-ref.ini"
  spec_dirs[sjeng]="sjeng"
  spec_commands[sjeng]="--input ./sjeng_base.x86_64_sse input/ref.txt"
  spec_dirs[soplex]="soplex"
  spec_commands[soplex]="--input ./soplex_base.x86_64_sse -s1 -e -m45000 pds-50.mps"
  spec_dirs[sphinx_livepretend]="sphinx_livepretend"
  spec_commands[sphinx_livepretend]="--input ./sphinx_livepretend_base.x86_64_sse ctlfile . input/args.an4"
  spec_dirs[tonto]="tonto"
  spec_commands[tonto]="--input ./tonto_base.x86_64_sse"
  spec_dirs[wrf]="wrf"
  spec_commands[wrf]="--input ./wrf_base.x86_64_sse"
  spec_dirs[xalancbmk]="xalancbmk"
  spec_commands[xalancbmk]="--input ./xalancbmk_base.x86_64_sse -v t5.xml xalanc.xsl"
  spec_dirs[zeusmp]="zeusmp"
  spec_commands[zeusmp]="--input ./zeusmp_base.x86_64_sse"
fi

# 获取运行目录
get_test_dir() {
  local test_name=$1
  local bench_dir=${spec_dirs[$test_name]}
  if [ "$spec_version" = "2017" ]; then
    echo "$spec_base_dir/$bench_dir/$spec_run_suffix"
  else
    echo "$spec_base_dir/$bench_dir"
  fi
}

process_spec_test() {
  local test_name=$1

  local spec_command=${spec_commands[$test_name]}
  if [ -z "$spec_command" ]; then
    echo "No command found for SPEC test: $test_name" | tee -a error_log.txt
    return
  fi

  local test_dir
  test_dir=$(get_test_dir "$test_name")
  if [ ! -d "$test_dir" ]; then
    echo "Test directory not found: $test_dir" | tee -a error_log.txt
    return
  fi
  cd "$test_dir"

  local outname="${spec_version}-${test_name}-out"

  sudo "$tooldir/run_script/modify.sh" --type physical --pref \
    --outdir "$output_dir" --outname "$outname" \
    $spec_command &

  # 限制每个 benchmark 运行时间 (秒)
  sleep 3600

  sudo pkill -9 -f valgrind

  wait

  echo "Finished: $test_name"
}

# ===== 主循环 =====
for test_name in "${!spec_commands[@]}"; do
  process_spec_test "$test_name"
done

echo "All tasks completed."

wait
