# hotcloudperf24-kyber-public

This is the artifact of **A Systematic Configuration Space Exploration of the Linux Kyber I/O Scheduler** published in HotCloudPerf 24, link to the paper: [https://dl.acm.org/doi/10.1145/3629527.3651416](https://dl.acm.org/doi/10.1145/3629527.3651416).

Please visit [https://github.com/ZebinRen/icpe24_io_scheduler_study_artifact](https://github.com/ZebinRen/icpe24_io_scheduler_study_artifact) for instructions for setting up the environment.

## Reproduce the environments

NOTE: Running the following experiments will wipe out all the existing data on the tested storage device!

### Micro-benchmark: Latency-sensitive read + Latency-sensitive write

Remove the existing data:

```bash
cd micro-bench-r1-w1

# Remove existing data
rm -r *pdf results_kyber_vary_target_lat/* results.txt kyber_vary_target_lat_log.txt
```

Change the 'FIO_CMD', 'devices', and 'device_name' to the path to the fio binary and the devices to be tested.

Then run the experiments:

```bash
sudo python3 kyber_vary_target_lat.py -r
```

After the experiments are done, the fio outputs are in the 'results_kyber_vary_target_lat' directory.

For the other three micro-benchmarks, the steps are similar.

### Experiments with File System

The procedure for the experiments with the three file systems, ext4, f2fs and xfs are similar. Here we take ext4 as an example.

First, prepare the device:

```bash
# Format the device
# Replace ext4 with f2fs or xfs for the other two file systems
sudo mkfs.ext4 YOUR_DEVICE
sudo mount YOUR_DEVICE YOUR_MOUNT_POINT
```

Then remove the existing data:

```bash
cd ext4-microbench/r1-w256
rm -r results_kyber_vary_target_lat/* kyber_vary_target_lat_log.txt *pdf
```

Then change the 'devices', 'device_name', 'mount_dir', and 'FIO_CMD' according to the local settings.

Run the experiments:

```bash
sudo python3 kyber_vary_target_lat.py -r
```

The results and the figure will be in the same directory as the script.

