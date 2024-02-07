import argparse
import copy
import os.path
import subprocess
import random
import numpy as np
import fio
from sched_util import *

import matplotlib.pyplot as plt

NSEC_PER_SEC = 1000000000


# CONSTANTS for kyber
def us_in_ns(us):
    return str(int(us) * 1000)


def ms_in_ns(ms):
    return str(int(ms) * 1000000)


# Machine-dependent settings
devices = '/dev/nvme5n1'
device_name = 'nvme5n1'
mount_dir = '/mnt/nvme_test/'
fio_file = os.path.join(mount_dir, 'fio_file')
scheduler = 'kyber'
rep_start = 0
rep_end = 4

enable_sched_cmd = 'modprobe kyber_iosched'
disable_sched_cmd = 'modprobe -r kyber_iosched'

# read_target_latencies_ticks = [
#     '50us', '100us', '250us', '500us', '1ms', '2ms', '5ms', '10ms', '100ms'
# ]
# read_target_latencies_values = [
#     us_in_ns(x) for x in [50, 100, 250, 500, 1000, 2000, 5000, 10000, 100000]
# ]
# write_target_latencies_ticks = [
#     '20us', '50us', '100us', '250us', '500us', '1ms', '2ms', '5ms', '10ms',
#     '100ms'
# ]
# write_target_latencies_values = [
#     us_in_ns(x)
#     for x in [20, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 100000]
# ]

read_target_latencies_ticks = ['50us', '100ms']
read_target_latencies_values = [us_in_ns(x) for x in [50, 100000]]
write_target_latencies_ticks = ['20us', '100ms']
write_target_latencies_values = [us_in_ns(x) for x in [20, 100000]]

parameter_value_ticks = []
parameter_values = []

for cur_r_lat_ticks, cur_r_lat_val in zip(read_target_latencies_ticks,
                                          read_target_latencies_values):
    for cur_w_lat_ticks, cur_w_lat_val in zip(write_target_latencies_ticks,
                                              write_target_latencies_values):
        parameter_value_ticks.append((cur_r_lat_ticks, cur_w_lat_ticks))
        parameter_values.append((cur_r_lat_val, cur_w_lat_val))

# nsec, read default = 2,000,000; write default = 10,000,000
parameter_name = ('read_lat_nsec', 'write_lat_nsec')
parameter_name_abbr = ('r', 'w')

workload_name = ['r256-w256']
workload_fio_options = [
    '--name=1 --rw=randread --cpus_allowed=1 --iodepth=256 --name=2 --rw=randwrite --cpus_allowed=2 --iodepth=256'
]

# settings
results_root = 'results_kyber_vary_target_lat'
fig_dir = results_root
# fio_results_dir = os.path.join(cur_results_root, 'fio_output')
# bpf_log_dir = os.path.join(cur_results_root, 'bpf_log')
# iops_log_dir = os.path.join(cur_results_root, 'iops_log')

# fig_name_prefix = 'bfq_expire_sync_single_p'

FIO_RAMP_TIME = 360
FIO_RUN_TIME = 360
FIO_CMD = '/mnt/sdc/zebin/local/fio-3.35/fio'

# Parse command line settings
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-r',
                    '--run',
                    action='store_true',
                    help='Run the experiment')
parser.add_argument('-p',
                    '--print_only',
                    action='store_true',
                    help='Only print the command')
args = parser.parse_args()
config = vars(args)
print(config)

## construct fio options
ENGINE_OPTIONS = '--ioengine=io_uring --registerfiles=1 --fixedbufs=1'
FIO_OPTIONS = '--size=100% --norandommap=1 --group_reporting=1 --direct=1 --output-format=json --bs=4k'.format(
    FIO_RAMP_TIME, FIO_RUN_TIME)
FIO_TIME_OPTIONS = '--time_based=1 --ramp_time={}s --runtime={}s'.format(
    FIO_RAMP_TIME, FIO_RUN_TIME)
FIO_FILE = '--filename=' + fio_file
FIO_COMMAND_GENERAL = ' '.join(
    [FIO_TIME_OPTIONS, ENGINE_OPTIONS, FIO_OPTIONS, FIO_FILE])

BPF_CMD = 'bpftrace -e \'BEGIN {printf("start: %llu\\n", nsecs)} tracepoint:kyber:kyber_adjust {printf("domain: %s, depth: %d, timestamp: %llu\\n", args->domain, args->depth, nsecs)}\''


def exec_cmd(cmd):
    print(cmd)
    if config['print_only']:
        return

    res = subprocess.run(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True,
                         check=True)
    print(res.stdout)
    print(res.stderr)


def exec_cmd_background(cmd):
    print(cmd)
    if config['print_only']:
        return

    p = subprocess.Popen(
        cmd,
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
        shell=True)
    return p


if config['run']:
    for cur_rep in range(rep_start, rep_end + 1):
        cur_results_root = os.path.join(results_root, 'rep_{}'.format(cur_rep))
        os.mkdir(cur_results_root)
        fio_results_dir = os.path.join(cur_results_root, 'fio_output')
        bpf_log_dir = os.path.join(cur_results_root, 'bpf_log')
        iops_log_dir = os.path.join(cur_results_root, 'iops_log')
        lat_log_dir = os.path.join(cur_results_root, 'lat_log')
        os.mkdir(fio_results_dir)
        os.mkdir(bpf_log_dir)
        os.mkdir(iops_log_dir)
        os.mkdir(lat_log_dir)
        for cur_workload_name, cur_workload_option in zip(
                workload_name, workload_fio_options):
            # Choose the next one randomly
            cur_para_value_all = copy.deepcopy(parameter_values)
            cur_para_ticks_all = copy.deepcopy(parameter_value_ticks)
            while len(cur_para_value_all) > 0:
                cur_idx = random.randint(0, len(cur_para_value_all) - 1)
                cur_para_value = cur_para_value_all[cur_idx]
                cur_para_ticks = cur_para_ticks_all[cur_idx]
                del cur_para_value_all[cur_idx]
                del cur_para_ticks_all[cur_idx]

                output_file = '{}_sche_{}_{}_{}_{}_{}.txt'.format(
                    cur_workload_name, scheduler, parameter_name_abbr[0],
                    cur_para_ticks[0], parameter_name_abbr[1],
                    cur_para_ticks[1])
                output_file_bpf = 'bpf_' + output_file
                output_file_iops_log = '{}_sche_{}_{}_{}_{}_{}_iops'.format(
                    cur_workload_name, scheduler, parameter_name_abbr[0],
                    cur_para_ticks[0], parameter_name_abbr[1],
                    cur_para_ticks[1])
                output_file_lat_log = '{}_sche_{}_{}_{}_{}_{}_lat'.format(
                    cur_workload_name, scheduler, parameter_name_abbr[0],
                    cur_para_ticks[0], parameter_name_abbr[1],
                    cur_para_ticks[1])
                output_file = os.path.join(fio_results_dir, output_file)
                output_file_bpf = os.path.join(bpf_log_dir, output_file_bpf)
                output_file_iops_log = os.path.join(iops_log_dir,
                                                    output_file_iops_log)
                output_file_lat_log = os.path.join(lat_log_dir,
                                                   output_file_lat_log)
                # reformat the device
                exec_cmd('umount ' + devices)
                exec_cmd('nvme format -s 1 ' + devices)
                exec_cmd('mkfs.ext4 ' + devices)
                exec_cmd('mount {} {}'.format(devices, mount_dir))
                fill_file_cmd = f'head -c 50G </dev/urandom >{fio_file}'
                exec_cmd(fill_file_cmd)

                # reload the kyber module to reset the kyber state
                set_scheduler(
                    device_name,
                    'none')  # set to none to reset all the scheduler states
                exec_cmd('sleep 10s')
                exec_cmd(disable_sched_cmd)
                exec_cmd(enable_sched_cmd)
                set_scheduler(device_name, scheduler)
                if not assert_scheduler(device_name, scheduler):
                    print('Assert scheduler failed, get {}, expect'.format(
                        get_scheduler(device_name), scheduler))
                    exit(1)
                set_parameter(device_name, parameter_name[0],
                              cur_para_value[0])
                set_parameter(device_name, parameter_name[1],
                              cur_para_value[1])
                print('Set parameter {} to {}'.format(parameter_name[0],
                                                      cur_para_value[0]))
                print('Set parameter {} to {}'.format(parameter_name[1],
                                                      cur_para_value[1]))

                # Also record iops log
                log_option = '--write_iops_log={} --write_lat_log={} --log_avg_msec=1000'.format(
                    output_file_iops_log, output_file_lat_log)

                cur_fio_command = ' '.join([
                    FIO_CMD, FIO_COMMAND_GENERAL, log_option,
                    cur_workload_option, '-o', output_file
                ])
                # bpftrace
                cur_bpf_cmd = 'exec ' + BPF_CMD + ' > ' + output_file_bpf
                bpf_p = exec_cmd_background(cur_bpf_cmd)
                exec_cmd('sleep 10s')  # wait for bpf to start
                # execute command
                exec_cmd(cur_fio_command)
                bpf_p.kill()
                exec_cmd('sleep 5s')

                if not assert_parameter(device_name, parameter_name[0],
                                        cur_para_value[0]):
                    print('Assert parameter failed, get {}, expect {}'.format(
                        get_parameter(device_name, parameter_name[0]),
                        cur_para_value[0]))
                    exit(1)
                if not assert_parameter(device_name, parameter_name[1],
                                        cur_para_value[1]):
                    print('Assert parameter failed, get {}, expect {}'.format(
                        get_parameter(device_name, parameter_name[1]),
                        cur_para_value[1]))
                    exit(1)

## Read and parse results, throughput
global_rk = []
jobs_rk = [
    'read:lat_ns:mean',
    'read:iops',
    'read:lat_ns:stddev',
    'read:iops_stddev',
    'usr_cpu',
    'sys_cpu',
    'read:bw',
    'read:clat_ns:percentile:99.000000',
    'write:lat_ns:mean',
    'write:iops',
    'write:lat_ns:stddev',
    'write:iops_stddev',
    'write:clat_ns:percentile:99.000000',
]

avg_lat_results = {}
read_p99_lat_results = {}
write_p99_lat_results = {}
iops_read_results = {}
iops_stddev = {}
iops_write_results = {}
iops_write_stddev = {}
cpu_results = {}
bw_results = {}

for cur_workload_name in workload_name:
    avg_lat_results[cur_workload_name] = []
    read_p99_lat_results[cur_workload_name] = []
    write_p99_lat_results[cur_workload_name] = []
    iops_read_results[cur_workload_name] = []
    iops_stddev[cur_workload_name] = []
    iops_write_results[cur_workload_name] = []
    iops_write_stddev[cur_workload_name] = []
    cpu_results[cur_workload_name] = []
    bw_results[cur_workload_name] = []
    for cur_para_ticks in parameter_value_ticks:
        cur_conf_read_iops = []
        cur_conf_write_iops = []
        cur_conf_read_p99_lat = []
        cur_conf_write_p99_lat = []
        for cur_rep in range(rep_start, rep_end + 1):
            cur_results_root = os.path.join(results_root,
                                            'rep_{}'.format(cur_rep))
            fio_results_dir = os.path.join(cur_results_root, 'fio_output')
            bpf_log_dir = os.path.join(cur_results_root, 'bpf_log')
            iops_log_dir = os.path.join(cur_results_root, 'iops_log')

            output_file = '{}_sche_{}_{}_{}_{}_{}.txt'.format(
                cur_workload_name, scheduler, parameter_name_abbr[0],
                cur_para_ticks[0], parameter_name_abbr[1], cur_para_ticks[1])
            output_file = os.path.join(fio_results_dir, output_file)

            _, j_res = fio.parse_experiment(output_file, global_rk, jobs_rk)
            j_res = j_res[0]
            cur_conf_read_iops.append(j_res['read:iops'] / 1000)
            cur_conf_write_iops.append(j_res['write:iops'] / 1000)
            cur_conf_read_p99_lat.append(
                j_res['read:clat_ns:percentile:99.000000'] / 1000)
            cur_conf_write_p99_lat.append(
                j_res['write:clat_ns:percentile:99.000000'] / 1000)
        iops_read_results[cur_workload_name].append(cur_conf_read_iops)
        iops_write_results[cur_workload_name].append(cur_conf_write_iops)
        read_p99_lat_results[cur_workload_name].append(cur_conf_read_p99_lat)
        write_p99_lat_results[cur_workload_name].append(cur_conf_write_p99_lat)
        # avg_lat_results[cur_workload_name].append(
        #     j_res['read:lat_ns:mean'] / 1000)
        # # p99_lat_results[cur_workload_name].append(
        # #     j_res['read:clat_ns:percentile:99.000000'] / 1000)
        # iops_results[cur_workload_name].append(j_res['read:iops'] / 1000)
        # iops_write_results[cur_workload_name].append(j_res['write:iops'] /
        #                                              1000)
        # iops_write_stddev[cur_workload_name].append(
        #     j_res['write:iops_stddev'] / 1000)
        # iops_stddev[cur_workload_name].append(j_res['read:iops_stddev'] /
        #                                       1000)
        # cpu_results[cur_workload_name].append(
        #     (j_res['usr_cpu'] + j_res['sys_cpu']) / 100)
        # bw_results[cur_workload_name].append(j_res['read:bw'] / 1024 /
        #                                      1024)

qd_results = {}
qd_results_sec = {}
avg_qd_results = {}
std_qd_results = {}
# average queue depth
for cur_workload_name in workload_name:
    qd_results[cur_workload_name] = []
    qd_results_sec[cur_workload_name] = []
    avg_qd_results[cur_workload_name] = []
    std_qd_results[cur_workload_name] = []
    for cur_para_ticks in parameter_value_ticks:
        cur_conf_qd_results = []
        cur_conf_qd_results_sec = []
        cur_conf_read_depth = []
        cur_conf_write_depth = []
        for cur_rep in range(rep_start, rep_end + 1):
            cur_results_root = os.path.join(results_root,
                                            'rep_{}'.format(cur_rep))
            bpf_log_dir = os.path.join(cur_results_root, 'bpf_log')
            output_file = '{}_sche_{}_{}_{}_{}_{}.txt'.format(
                cur_workload_name, scheduler, parameter_name_abbr[0],
                cur_para_ticks[0], parameter_name_abbr[1], cur_para_ticks[1])
            output_file_bpf = 'bpf_' + output_file
            output_file_bpf = os.path.join(bpf_log_dir, output_file_bpf)

            # parse bpf, first line is index, second line is start time
            f = open(output_file_bpf, 'r')
            f.readline()  # Discard the first line
            start_time = int(f.readline().split(':')[1].strip())
            cur_read_qd = [(0, 256)]
            cur_write_qd = [(0, 128)]
            cur_read_qd_sec = [(0, 256)]
            cur_write_qd_sec = [(0, 128)]
            for line in f.readlines():
                line = line.strip().split(',')
                cur_domain = line[0].split(':')[1].strip()
                cur_depth = int(line[1].split(':')[1].strip())
                cur_timestamp = int(line[2].split(':')[1].strip())
                if cur_domain == 'READ':
                    cur_read_qd.append((cur_timestamp - start_time, cur_depth))
                    cur_read_qd_sec.append((int(
                        (cur_timestamp - start_time) / NSEC_PER_SEC),
                                            cur_depth))
                elif cur_domain == 'WRITE':
                    cur_write_qd.append(
                        (cur_timestamp - start_time, cur_depth))
                    cur_write_qd_sec.append((int(
                        (cur_timestamp - start_time) / NSEC_PER_SEC),
                                             cur_depth))
            cur_conf_qd_results.append((cur_read_qd, cur_write_qd))
            cur_conf_qd_results_sec.append((cur_read_qd_sec, cur_write_qd_sec))

            # compute average queue depth results
            cur_avg_qd = []
            for cur_domain_qd in [cur_read_qd, cur_write_qd]:
                accu_qd = 0
                prev_ts = 0
                prev_qd = cur_domain_qd[0][1]
                for cur_ts, cur_qd in cur_domain_qd[1:]:
                    if cur_ts / NSEC_PER_SEC < FIO_RAMP_TIME:
                        # before we steady state, continue
                        prev_ts = cur_ts
                        prev_qd = cur_qd
                        continue
                    ts_gap = cur_ts - max(prev_ts,
                                          FIO_RAMP_TIME * NSEC_PER_SEC)
                    ts_gap = ts_gap / NSEC_PER_SEC
                    accu_qd += ts_gap * prev_qd
                    prev_ts = cur_ts
                    prev_qd = cur_qd
                # before finish
                ts_gap = (FIO_RAMP_TIME + FIO_RUN_TIME) * NSEC_PER_SEC - max(
                    prev_ts, FIO_RAMP_TIME * NSEC_PER_SEC)
                ts_gap = ts_gap / NSEC_PER_SEC
                accu_qd += ts_gap * prev_qd
                cur_avg_qd.append(accu_qd / FIO_RUN_TIME)
            cur_conf_read_depth.append(cur_avg_qd[0])
            cur_conf_write_depth.append(cur_avg_qd[1])

            f.close()
        avg_qd_results[cur_workload_name].append(
            (np.average(cur_conf_read_depth),
             np.average(cur_conf_write_depth)))
        std_qd_results[cur_workload_name].append(
            (np.std(cur_conf_read_depth), np.std(cur_conf_write_depth)))
        qd_results[cur_workload_name].append(cur_conf_qd_results)
        qd_results_sec[cur_workload_name].append(cur_conf_qd_results_sec)

# for k in qd_results_sec.keys():
#     for cur_tick, cur_val in zip(parameter_value_ticks, qd_results_sec[k]):
#         print(cur_tick)
#         print('R', cur_val[0])
#         print('W', cur_val[1])

# just print the results
# for cur_workload_name in workload_name:
#     print(cur_workload_name)
#     for index, cur_para_ticks in zip(range(len(parameter_value_ticks)),
#                                      parameter_value_ticks):
#         template_string = "    {} & {} & {} & {}~({}) & {}~({}) & {}~({}) & {}~({}) \\\\"
#         # if cur_workload_name == workload_name[0]:
#         #     template_string = "    " + "\\multirow{{2}}{{" + "*" + "}}{{" + str(
#         #         index) + "}}" + " & {} & {} & {} & {} & {} \\\\"
#         print(
#             template_string.format(
#                 index, cur_para_ticks[0], cur_para_ticks[1],
#                 str(
#                     round(
#                         np.average(
#                             iops_read_results[cur_workload_name][index]), 1)),
#                 str(
#                     round(np.std(iops_read_results[cur_workload_name][index]),
#                           1)),
#                 str(
#                     round(
#                         np.average(
#                             iops_write_results[cur_workload_name][index]), 1)),
#                 str(
#                     round(np.std(iops_write_results[cur_workload_name][index]),
#                           1)),
#                 round(avg_qd_results[cur_workload_name][index][0], 1),
#                 round(std_qd_results[cur_workload_name][index][0], 1),
#                 round(avg_qd_results[cur_workload_name][index][1], 1),
#                 round(std_qd_results[cur_workload_name][index][1], 1)))
#     print('    \hline')

# without std
if True:
    print('###########Result without std###########')
    print('READ IOPS')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(np.average(iops_read_results[cur_workload_name][index]),
                      1)) + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

    print('WRITE IOPS')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(np.average(iops_write_results[cur_workload_name][index]),
                      1)) + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

    print('READ latency in ms')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(
                    np.average(read_p99_lat_results[cur_workload_name][index])
                    / 1000, 1)) + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

    print('Write latency in ms')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(
                    np.average(write_p99_lat_results[cur_workload_name][index])
                    / 1000, 1)) + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

# with std
if True:
    print('###########Result with std###########')
    print('READ IOPS')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(np.average(iops_read_results[cur_workload_name][index]),
                      1)) + ' (' +
                  str(
                      round(
                          np.std(iops_read_results[cur_workload_name][index]),
                          1)) + ')' + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

    print('WRITE IOPS')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(np.average(iops_write_results[cur_workload_name][index]),
                      1)) + ' (' +
                  str(
                      round(
                          np.std(iops_write_results[cur_workload_name][index]),
                          1)) + ')' + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

    print('READ latency in ms')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(str(
                round(
                    np.average(read_p99_lat_results[cur_workload_name][index])
                    / 1000, 1)) + ' (' +
                  str(
                      round(
                          np.std(
                              read_p99_lat_results[cur_workload_name][index]) /
                          1000, 1)) + ')' + ' & ',
                  end='')
            index += 1
        print('\\\\')

    print('')

    print('Write latency in ms')
    print('& ' + ' & '.join(write_target_latencies_ticks))
    # print each line
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        print(cur_read_tick + ' & ', end='')
        for cur_write_tick in write_target_latencies_ticks:
            print(
                str(
                    round(
                        np.average(
                            write_p99_lat_results[cur_workload_name][index]) /
                        1000, 1)) + ' (' +
                str(
                    round(
                        np.std(write_p99_lat_results[cur_workload_name][index])
                        / 1000, 1)) + ')' + ' & ',
                end='')
            index += 1
        print('\\\\')

    print('')

heatmap_axis_tick_font_size = 36
heatmap_data_tag_size = 28
cbar_tick_font_size = 26
############################################
# Heatmap
############################################

# read IOPS
if True:
    fig_save_path = 'f2fs-r256-w256-read-iops.pdf'
    heatmap_data = iops_read_results
    heatmap = []
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        cur_read_row = []
        for cur_write_tick in write_target_latencies_ticks:
            cur_read_row.append(
                round(np.average(heatmap_data[cur_workload_name][index]), 1))
            index += 1
        heatmap.append(cur_read_row)
    heatmap.reverse()

    cbar_label = 'placeholder'

    # reset_color()
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xticks(np.arange(len(write_target_latencies_ticks)),
                  labels=write_target_latencies_ticks,
                  fontsize=heatmap_axis_tick_font_size)
    read_label_reverse = copy.deepcopy(read_target_latencies_ticks)
    read_label_reverse.reverse()
    ax.set_yticks(np.arange(len(read_target_latencies_ticks)),
                  labels=read_label_reverse,
                  fontsize=heatmap_axis_tick_font_size)
    plt.xlabel('Write target latency', fontsize=heatmap_axis_tick_font_size)
    plt.ylabel('Read target latency', fontsize=heatmap_axis_tick_font_size)
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(),
             rotation=45,
             ha="right",
             rotation_mode="anchor")

    im = ax.imshow(heatmap,
                   cmap='hot',
                   interpolation='nearest',
                   vmin=0.0,
                   vmax=250)
    color_threshold = (0 + 250) / 2

    # Create colorbar
    cbar = ax.figure.colorbar(
        im,
        ax=ax,
        location='right',
    )
    cbar.ax.tick_params(labelsize=cbar_tick_font_size)

    # cbar.ax.set_ylabel(cbar_label, rotation=-90, va="bottom")
    for i in range(len(read_target_latencies_ticks)):
        for j in range(len(write_target_latencies_ticks)):
            if heatmap[i][j] < color_threshold:
                color = 'w'
            else:
                color = 'black'
            text = ax.text(j,
                           i,
                           round(heatmap[i][j], 1),
                           ha="center",
                           va="center",
                           color=color,
                           fontsize=heatmap_data_tag_size)

    plt.savefig(fig_save_path, bbox_inches='tight')

# write IOPS
if True:
    fig_save_path = 'f2fs-r256-w256-write-iops.pdf'
    heatmap_data = iops_write_results
    heatmap = []
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        cur_read_row = []
        for cur_write_tick in write_target_latencies_ticks:
            cur_read_row.append(
                round(np.average(heatmap_data[cur_workload_name][index]), 1))
            index += 1
        heatmap.append(cur_read_row)
    heatmap.reverse()

    cbar_label = 'placeholder'

    # reset_color()
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xticks(np.arange(len(write_target_latencies_ticks)),
                  labels=write_target_latencies_ticks,
                  fontsize=heatmap_axis_tick_font_size)
    read_label_reverse = copy.deepcopy(read_target_latencies_ticks)
    read_label_reverse.reverse()
    ax.set_yticks(np.arange(len(read_target_latencies_ticks)),
                  labels=read_label_reverse,
                  fontsize=heatmap_axis_tick_font_size)
    plt.xlabel('Write target latency', fontsize=heatmap_axis_tick_font_size)
    plt.ylabel('Read target latency', fontsize=heatmap_axis_tick_font_size)
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(),
             rotation=45,
             ha="right",
             rotation_mode="anchor")

    vmin = 0
    vmax = 250
    im = ax.imshow(heatmap,
                   cmap='hot',
                   interpolation='nearest',
                   vmin=vmin,
                   vmax=vmax)
    color_threshold = (vmin + vmax) / 2

    # Create colorbar
    cbar = ax.figure.colorbar(
        im,
        ax=ax,
        location='right',
    )
    cbar.ax.tick_params(labelsize=cbar_tick_font_size)

    # cbar.ax.set_ylabel(cbar_label, rotation=-90, va="bottom")
    for i in range(len(read_target_latencies_ticks)):
        for j in range(len(write_target_latencies_ticks)):
            if heatmap[i][j] < color_threshold:
                color = 'w'
            else:
                color = 'black'
            text = ax.text(j,
                           i,
                           round(heatmap[i][j], 1),
                           ha="center",
                           va="center",
                           color=color,
                           fontsize=heatmap_data_tag_size)

    plt.savefig(fig_save_path, bbox_inches='tight')

# read latency
if True:
    fig_save_path = 'r1-w256-read-latency-ms.pdf'
    heatmap_data = read_p99_lat_results
    heatmap = []
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        cur_read_row = []
        for cur_write_tick in write_target_latencies_ticks:
            cur_read_row.append(
                round(
                    np.average(heatmap_data[cur_workload_name][index]) / 1000,
                    1))
            index += 1
        heatmap.append(cur_read_row)
    heatmap.reverse()

    cbar_label = 'placeholder'

    # reset_color()
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xticks(np.arange(len(write_target_latencies_ticks)),
                  labels=write_target_latencies_ticks,
                  fontsize=heatmap_axis_tick_font_size)
    read_label_reverse = copy.deepcopy(read_target_latencies_ticks)
    read_label_reverse.reverse()
    ax.set_yticks(np.arange(len(read_target_latencies_ticks)),
                  labels=read_label_reverse,
                  fontsize=heatmap_axis_tick_font_size)
    plt.xlabel('Write target latency', fontsize=heatmap_axis_tick_font_size)
    plt.ylabel('Read target latency', fontsize=heatmap_axis_tick_font_size)
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(),
             rotation=45,
             ha="right",
             rotation_mode="anchor")

    vmin = 0
    vmax = 3
    im = ax.imshow(heatmap,
                   cmap='hot',
                   interpolation='nearest',
                   vmin=vmin,
                   vmax=vmax)
    color_threshold = (vmin + vmax) / 2

    # Create colorbar
    # cbar = ax.figure.colorbar(
    #     im,
    #     ax=ax,
    #     location='left',
    # )

    # cbar.ax.set_ylabel(cbar_label, rotation=-90, va="bottom")
    for i in range(len(read_target_latencies_ticks)):
        for j in range(len(write_target_latencies_ticks)):
            if heatmap[i][j] < color_threshold:
                color = 'w'
            else:
                color = 'black'
            text = ax.text(j,
                           i,
                           round(heatmap[i][j], 1),
                           ha="center",
                           va="center",
                           color=color,
                           fontsize=heatmap_data_tag_size)

    plt.savefig(fig_save_path, bbox_inches='tight')

# write latency
if True:
    fig_save_path = 'r1-w256-write-latency-ms.pdf'
    heatmap_data = write_p99_lat_results
    heatmap = []
    index = 0
    for cur_read_tick in read_target_latencies_ticks:
        cur_read_row = []
        for cur_write_tick in write_target_latencies_ticks:
            cur_read_row.append(
                round(
                    np.average(heatmap_data[cur_workload_name][index]) / 1000,
                    1))
            index += 1
        heatmap.append(cur_read_row)
    heatmap.reverse()

    cbar_label = 'placeholder'

    # reset_color()
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xticks(np.arange(len(write_target_latencies_ticks)),
                  labels=write_target_latencies_ticks,
                  fontsize=heatmap_axis_tick_font_size)
    read_label_reverse = copy.deepcopy(read_target_latencies_ticks)
    read_label_reverse.reverse()
    ax.set_yticks(np.arange(len(read_target_latencies_ticks)),
                  labels=read_label_reverse,
                  fontsize=heatmap_axis_tick_font_size)
    plt.xlabel('Write target latency', fontsize=heatmap_axis_tick_font_size)
    plt.ylabel('Read target latency', fontsize=heatmap_axis_tick_font_size)
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(),
             rotation=45,
             ha="right",
             rotation_mode="anchor")

    im = ax.imshow(heatmap,
                   cmap='hot',
                   interpolation='nearest',
                   vmin=0.0,
                   vmax=20)
    color_threshold = (0 + 20) / 2

    # Create colorbar
    # cbar = ax.figure.colorbar(
    #     im,
    #     ax=ax,
    #     location='left',
    # )

    # cbar.ax.set_ylabel(cbar_label, rotation=-90, va="bottom")
    for i in range(len(read_target_latencies_ticks)):
        for j in range(len(write_target_latencies_ticks)):
            if heatmap[i][j] < color_threshold:
                color = 'w'
            else:
                color = 'black'
            text = ax.text(j,
                           i,
                           round(heatmap[i][j], 1),
                           ha="center",
                           va="center",
                           color=color,
                           fontsize=heatmap_data_tag_size)

    plt.savefig(fig_save_path, bbox_inches='tight')