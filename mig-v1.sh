#!/bin/bash
# create date: 2022年9月16日17:15:44
# modify date: 2023年2月1日11:19:52 
# author: ninesun
# 参数: 参数1 代表切分index数量 参数2: startline.txt 绝对路径
# 注意:脚本必须和key list在一个目录中
if [ $# -eq 2 ];then
        qty=$1
        path=$2
        #src_host=$3
        #src_port=$4
        #dest_port=$5
        #dest_port=$6
else 
        echo "para error,eg: $0 100 /opt/text.txt"
        exit 8        
fi

echo ${path}


prefix=$(basename ${path})
filepath=$(dirname ${path})

rm -rf ${filepath}/${prefix}.*
echo ${prefix}
# 开始切分fl-key split -l 500 /opt/startline.txt -d -a 3 startline.txt.
echo "split -l ${qty} ${path} -d -a 3 ${prefix}."
split -l ${qty} ${path} -d -a 3 ${prefix}.
tasks=$(find ${filepath} -name "${prefix}.*" |wc -l)
echo ${tasks}
for i in `seq 1 ${tasks}`;do
        echo ${i}
        # 清除上次运行完成的container
        # docker stop -t 1 redis-img-${prefix}-${i}  && docker rm -f redis-img-${prefix}-${i}        
        docker rm -f redis-img-${prefix}-${i}
        (
        echo "docker run  --name redis-img-${prefix}-${i} -v ${filepath}:/app 10.50.10.185/harbortest/redis-mig:1.1 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 ${prefix}.${i} &>/dev/null"        
        docker run  --name redis-img-${prefix}-${i} -v ${filepath}:/app 10.50.10.185/harbortest/redis-mig:1.1 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 ${prefix}.${i} &>/dev/null
        )&
done
wait

