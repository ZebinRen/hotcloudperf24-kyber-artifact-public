cd r1-w256
python3 kyber_vary_target_lat.py -r > kyber_vary_target_lat_log.txt 2>&1
cd ../r256-w256
python3 kyber_vary_target_lat.py -r > kyber_vary_target_lat_log.txt 2>&1