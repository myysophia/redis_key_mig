#!/bin/bash
# date 2022年9月16日17:15:44
# author ninesun

for i in `echo {000..013}`;do
        echo ${i}
        docker rm -f redis-img-${i}
        docker rm -f redis-img-${i}-1
        {
        
        docker run  --name redis-img-${i} 10.50.10.185/harbortest/redis-mig:1.2 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 startline.txt.${i} &>/dev/null
        docker run  --name redis-img-${i}-1 10.50.10.185/harbortest/redis-mig:1.2 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 lineurl.txt.${i} &>/dev/null
        }&
done
wait
