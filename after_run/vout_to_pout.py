import sys
import os
import bisect
import argparse

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def find_close_mapping(x, a):
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
    vpmap = {}
    with open(vpmap_file_name, "r") as vpmap_file:
        for line in vpmap_file:
            msline = line.replace("}", "").replace("\n", "").split(" ")
            map_ts = round(float(msline[-1]), 6)
            kn_vpn = int(msline[2], 16)
            kn_pfn = int(msline[3], 16)
            if kn_vpn not in vpmap:
                vpmap[kn_vpn] = []
            vpmap[kn_vpn].append((map_ts, kn_pfn))
    for vpn in vpmap:
        vpmap[vpn].sort()
    return vpmap

def main():
    parser = argparse.ArgumentParser(description="Convert .vout + .vpmap to .pout (physical address trace)")
    parser.add_argument("input", help="Input .vout file path")
    parser.add_argument("--with-timestamp", "-t", action="store_true",
                        help="Include timestamp in output (default: no timestamp)")
    parser.add_argument("--vpmap", help="Specify .vpmap file (default: same basename as input)")
    parser.add_argument("--output", "-o", help="Specify output file (default: input with .pout extension)")
    args = parser.parse_args()

    input_file_name = args.input

    if args.vpmap:
        vpmap_file_name = args.vpmap
    else:
        vpmap_file_name = input_file_name.rsplit(".", 1)[0] + ".vpmap"

    if args.output:
        output_file_name = args.output
    elif args.with_timestamp:
        output_file_name = input_file_name.rsplit(".", 1)[0] + "_trace.pout"
    else:
        output_file_name = input_file_name.rsplit(".", 1)[0] + ".pout"

    linenum = file_len(input_file_name)
    print("linenum of %s: %d" % (input_file_name, linenum))

    try:
        raw_trace_file = open(input_file_name, "r")
    except FileNotFoundError:
        sys.stderr.write("No file: %s\n" % input_file_name)
        exit(1)

    try:
        vpmap = load_vpmap(vpmap_file_name)
        print("vpmap loaded: %s" % vpmap_file_name)
    except FileNotFoundError:
        sys.stderr.write("No file: %s\n" % vpmap_file_name)
        exit(1)

    progress_step = max(linenum // 1000, 1)

    with open(output_file_name, "w") as mem_trace:
        i = 0
        none_cnt = 0
        ok_cnt = 0

        while True:
            line = raw_trace_file.readline()
            if not line:
                break

            if line[0] != "[" and line[0] != "R" and line[0] != "W":
                i += 1
                continue

            if (i % progress_step) == 0:
                print("\r%.0f%% [%d/%d]" % (i / linenum * 100, i, linenum), end="")

            line = line.replace("]", "}").replace("[", "{").replace("}", " ").replace("\n", " ")
            splitline = line.split("{")
            del splitline[0]

            for item in splitline:
                elem = " ".join(item.split()).split()

                if elem[0] == "R" or elem[0] == "W":
                    cg_vaddr = int(elem[1], 16)
                    cg_vpn = cg_vaddr // 4096
                    cg_ofs = cg_vaddr & 0xfff
                    ts = round(float(elem[2]), 6)

                    if cg_vpn not in vpmap:
                        none_cnt += 1
                    else:
                        vpmap_entries = vpmap[cg_vpn]
                        idx_list = [entry[0] for entry in vpmap_entries]
                        target_idx = find_close_mapping(ts, idx_list)

                        if target_idx is not None:
                            kn_pfn = vpmap_entries[target_idx][1]
                            paddr = kn_pfn * 4096 + cg_ofs
                            if args.with_timestamp:
                                mem_trace.write(f"{elem[0]} {hex(paddr)} {elem[2]}\n")
                            else:
                                mem_trace.write(f"{elem[0]} {hex(paddr)}\n")
                            ok_cnt += 1
                        else:
                            none_cnt += 1

            i += 1

        print(f"\nok: {ok_cnt}, none: {none_cnt}, ({(ok_cnt / (ok_cnt + none_cnt)) * 100:.1f}%)")
        print(f"Output: {output_file_name}")

    raw_trace_file.close()

if __name__ == "__main__":
    main()
