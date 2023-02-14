# redis_key_mig
redis 单一key迁移，支持hset zset string 类型的key

@[TOC]
## 优化redis key 迁移程序(云原生版本)

### 问题

问题: 

Key迁移本地跑超过30mins

共:1264笔, 迁移总共花费6.323 s

共:3374笔, 迁移总共花费5.459 s

[外链图片转存失败,源站可能有防盗链机制,建议将图片保存下来直接上传(img-Ppxu8gBu-1675851078556)(E:\book\redis\redis迁移优化\wps1.jpg)] 

可优化点: 

1、放在服务器上执行

  需要搭建python3环境 + 相关依赖  -> docker解决

- Ø 寻找基础镜像        

- Ø 开发dokcer File

- Ø 构建镜像

- Ø 测试效能

2、自动切分index数量，多支job来迁移

例如3500个index，每500行切分一个文件对应一个python job处理。

每个文件多少行根据传入的参数决定.

如何用docker 跑多个python job？

3、脚本获取redis key

```bash
#!/bin/bash
# author: ninesun
# date: 2023年2月8日08:55:21
# desc: generate fl redis key

indexprefix=${1-'/202302/08'}
echo '' > /tmp/indexfile
echo '' > /tmp/startline.txt
echo '' > /tmp/lineurl.txt
echo "start generate ..."
# acf
cd /dfs/acf/INDEX/${indexprefix}
for i in `ls | grep -E "^A|^C"`;do echo START_LINE:/INDEX${indexprefix}/$i >> /tmp/startline.txt ;done
for i in `ls | grep -E "^A|^C"`;do echo LINE_URL:/INDEX${indexprefix}/$i >> /tmp/lineurl.txt ;done

# oc
cd /dfs/oc/INDEX/${indexprefix}
for i in `ls | grep -E "^L"`;do echo LINE_URL:/INDEX${indexprefix}/$i >> /tmp/lineurl.txt ;done
for i in `ls | grep -E "^L"`;do echo START_LINE:/INDEX${indexprefix}/$i >> /tmp/startline.txt ;done


cat /tmp/lineurl.txt | cut -d / -f5| grep -Ev '^$' >> /tmp/indexfile # 比对时使用
qty=$(wc -l /tmp/indexfile)
echo "end generate ...,total index: ${qty}"
```

运行: 

```bash
#bash generateindexlist.sh
start generate ...
end generate ...,total index: 1060 /tmp/indexfile

```

example： 

```bash
/tmp/lineurl.txt
LINE_URL:/INDEX/202302/02/A1110MACR02.TXT
LINE_URL:/INDEX/202302/02/A1150DAOIH02.TXT
LINE_URL:/INDEX/202302/02/A1150SUFS01.TXT
LINE_URL:/INDEX/202302/02/A1210MACR04.TXT
LINE_URL:/INDEX/202302/02/A1215MACR16.TXT
LINE_URL:/INDEX/202302/02/A1230DNANO02.TXT
LINE_URL:/INDEX/202302/02/A1250AOIH02.TXT
LINE_URL:/INDEX/202302/02/A1250AOIH04.TXT
LINE_URL:/INDEX/202302/02/A1250AOIH05.TXT

/tmp/startline.txt
START_LINE:/INDEX/202302/08/A1110MACR02.TXT
START_LINE:/INDEX/202302/08/A1150DAOIH02.TXT
START_LINE:/INDEX/202302/08/A1150SUFS01.TXT
START_LINE:/INDEX/202302/08/A1210MACR04.TXT
START_LINE:/INDEX/202302/08/A1215MACR16.TXT
START_LINE:/INDEX/202302/08/A1230DNANO02.TXT
START_LINE:/INDEX/202302/08/A1250AOIH02.TXT
START_LINE:/INDEX/202302/08/A1250AOIH04.TXT
START_LINE:/INDEX/202302/08/A1250AOIH05.TXT
```



### 迁移程序的Dockerfile

前置准备：

1、将要迁移的key先写入文件

2、先切分文件，按照100/500行切分

```bash
# -d：使用数字作为后缀。
#-l：值为每一输出档的行数大小。
#-a：指定后缀长度(默认为2)。
split -l 100 fl-key.txt -d -a 3 fl100
# 按照500行切分，文件前缀为fl500，后缀是三个数字
split -l 500 fl-key.txt -d -a 3 fl500
```

注意:

- 项目文件和Dockerfile在同一目录层级
- 注意要将切分的文件一并build到image里面

```bash
FROM python:3.7
COPY ./redis_key_mig /app
WORKDIR /app
RUN /bin/bash -c 'pwd;ls -l /app' # 用于调试
#RUN  /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install redis==3.5.3
cmd ["python", "/app/redisMigrate.py"]
```

#### 优化

问题: 当有新的index需要迁移的时候如果需要重新build镜像

解决:  将容器目录挂载出来，然后外部修改即可。

优化后的Docker file 以及启动命令

```bash
split -l 100 /opt/redis-mig/startline.txt -d -a 3 startline.txt.
split -l 100 /opt/redis-mig/lineurl.txt -d -a 3 lineurl.txt.
```
脚本内容

```bash
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
```



### docker build 构建

```bash
 /opt/redis-mig docker build -t 10.50.10.185/harbortest/redis-mig:1.0 .
```

### docker run 启动程序

```bash
docker run --name redis-img 10.50.10.185/harbortest/redis-mig:1.0 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 fl-key.txt
```

```bash
#!/bin/bash
# date 2022年9月16日17:15:44
# author ninesun

for i in `echo {000..035}`;do
        echo ${i}
        docker rm -f redis-img-${i}
        docker rm -f redis-img-${i}-1
        {
        docker run  --name redis-img-${i} 10.50.10.185/harbortest/redis-mig:1.0 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 start_line${i} &>/dev/n
ull
        docker run  --name redis-img-${i}-1 10.50.10.185/harbortest/redis-mig:1.0 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 line_url${i} &>/dev/n
ull
        }&
done
wait
```

### 优化

1、docker 镜像达到了900MB. 可选择使用slim的镜像以减小镜像的大小.

pyhton镜像修改后image大小变为157MB了。

```bash
submitty/python:3.7
```

2、性能压测

大约5分钟即可迁移完成
![在这里插入图片描述](https://img-blog.csdnimg.cn/2ab21baba9124def83de70c709a373f5.png)

3、大版本优化

11个线程并行大约1mins。此时间影响RTM、停机时间，因此该程序的性能是**关键**.
![在这里插入图片描述](https://img-blog.csdnimg.cn/651e6eb763fa4601860fbbb4c9b76f9e.png)



## 存在的问题

绑定挂载为何提示没权限呢？

绑定挂载容器没权限写log

这块对于目录挂载权限的问题还得再消化一下

![在这里插入图片描述](https://img-blog.csdnimg.cn/24013fd1eab746b19777df76ec41e4f9.png)


```bash
#] docker run  --name redis-img-startline.txt-2 --user $(id -u) -v /opt/redis-mig/redis_key_mig:/app 10.50.10.185/harbortest/redis-mig:1.1 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 startline.txt.000
Traceback (most recent call last):
  File "redisMigrate.py", line 15, in <module>
    from log.log import get_logger
  File "/app/log/log.py", line 11, in <module>
    os.makedirs(full_path)
  File "/usr/local/lib/python3.7/os.py", line 221, in makedirs
    mkdir(name, mode)
PermissionError: [Errno 13] Permission denied: '/app/logs/20230201'

```

如果不用绑定挂载，直接将切分好的文件放入咋还找不到文件呢？

```zsh
 ⚡ root@ninesun  /opt/redis-mig docker build -t 10.50.10.185/harbortest/redis-mig:1.2 .
Sending build context to Docker daemon  14.49MB
Step 1/6 : FROM submitty/python:3.7
 ---> f3c79749b014
Step 2/6 : COPY ./redis_key_mig /app
 ---> b25a9707d3d9
Removing intermediate container 3b3a0ee6475e
Step 3/6 : WORKDIR /app
 ---> 78c42963e4ff
Removing intermediate container 1e522eef948d
Step 4/6 : RUN /bin/bash -c 'pwd;ls -l /app'
 ---> Running in 5792edf3252f

/app
total 304
-rw-rw-r--. 1 root root  84008 Feb  1 02:48 fl-key.txt
-rw-r--r--. 1 root root 100385 Sep 14 09:40 fl-parse-key.txt
drwxr-xr-x. 3 root root     39 Sep 14 09:40 log
drwxr-xr-x. 5 root root     54 Sep 14 09:40 logs
-rw-r--r--. 1 root root   1525 Feb  1 06:56 mig-v1.sh
-rw-r--r--. 1 root root    501 Sep 20 05:44 mig.sh
-rw-r--r--. 1 root root   6162 Sep 14 09:40 redisMigrate.py
-rw-r--r--. 1 root root     14 Sep 14 09:40 requirements.txt
-rw-r--r--. 1 root root   4418 Feb  1 06:57 startline.txt.000
-rw-r--r--. 1 root root   4426 Feb  1 06:57 startline.txt.001
-rw-r--r--. 1 root root   4400 Feb  1 06:57 startline.txt.002
-rw-r--r--. 1 root root   4440 Feb  1 06:57 startline.txt.003
-rw-r--r--. 1 root root   4400 Feb  1 06:57 startline.txt.004
-rw-r--r--. 1 root root   4400 Feb  1 06:57 startline.txt.005
-rw-r--r--. 1 root root   4412 Feb  1 06:57 startline.txt.006
-rw-r--r--. 1 root root   4418 Feb  1 06:57 startline.txt.007
-rw-r--r--. 1 root root   4408 Feb  1 06:57 startline.txt.008
-rw-r--r--. 1 root root   4410 Feb  1 06:57 startline.txt.009
-rw-r--r--. 1 root root   4496 Feb  1 06:57 startline.txt.010
-rw-r--r--. 1 root root   4598 Feb  1 06:57 startline.txt.011
-rw-r--r--. 1 root root   2706 Feb  1 06:57 startline.txt.012
 ---> 56c5b29893e7
Removing intermediate container 5792edf3252f
Step 5/6 : RUN pip3 install redis==3.5.3
 ---> Running in fcc1e58c8e64

Collecting redis==3.5.3
  Downloading https://files.pythonhosted.org/packages/a7/7c/24fb0511df653cf1a5d938d8f5d19802a88cef255706fdda242ff97e91b7/redis-3.5.3-py2.py3-none-any.whl (72kB)
Installing collected packages: redis
Successfully installed redis-3.5.3
You are using pip version 18.1, however version 23.0 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
 ---> 3f0558ea48ff
Removing intermediate container fcc1e58c8e64
Step 6/6 : CMD python /app/redisMigrate.py
 ---> Running in 215145ec8789
 ---> 2a6b2d18c8d7
Removing intermediate container 215145ec8789
Successfully built 2a6b2d18c8d7
 ⚡ root@ninesun  /opt/redis-mig  startline.txt.000
 ✘ ⚡ root@ninesun  /opt/redis-mig 
 ✘ ⚡ root@ninesun  /opt/redis-mig 
 ✘ ⚡ root@ninesun  /opt/redis-mig 
 ✘ ⚡ root@ninesun  /opt/redis-mig 
 ✘ ⚡ root@ninesun  /opt/redis-mig 
 ✘ ⚡ root@ninesun  /opt/redis-mig docker rm -f "/redis-img-startline.txt-2"
/redis-img-startline.txt-2
 ⚡ root@ninesun  /opt/redis-mig 
 ⚡ root@ninesun  /opt/redis-mig 
 ⚡ root@ninesun  /opt/redis-mig 
 ⚡ root@ninesun  /opt/redis-mig docker run  --name redis-img-startline.txt-2  10.50.10.185/harbortest/redis-mig:1.1 python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 startline.txt.000
2023-02-01 08:05:19,789 INFO    : 开始迁移---------关键信息: indexName:startline.txt.000, sourceHost:10.50.10.45, sourcePort:19000, targetHost:10.50.10.170, targetPort:7100
Traceback (most recent call last):
  File "redisMigrate.py", line 154, in <module>
    with open(index, 'r') as f:
FileNotFoundError: [Errno 2] No such file or directory: 'startline.txt.000'

```

### 没有权限的原因

通过 docker 挂载目录的 logs，迁移程序日志发现存在日志文件无法写入或者 Permission denied 这样的异常错误，基本可以判定是文件所有权问题。

比如你宿主机挂载的文件目录是 root 的，而 docker 容器中 python应用程序的默认的用户，id 和 group 都是 1000（官方容器默认的值），这种情况在容器中就无法正常写入文件到宿主机。

```bash
docker rm -f redis-img-startline.txt-2
docker run  --name redis-img-startline.txt-2  \
-v /opt/redis-mig/redis_key_mig/:/app \
10.50.10.185/harbortest/redis-mig:1.1 \
python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 startline.txt.000
```



### 如何解决权限问题

1、创建一个具名卷

```bash
docker volume create dv_pgdata
docker volume list
```

2、查看具名卷的具体存储位置

```bash
docker inspect dv_pgdatadocker inspect dv_pgdata
[
    {
        "Driver": "local",
        "Labels": {},
        "Mountpoint": "/var/lib/docker/volumes/dv_pgdata/_data",
        "Name": "dv_pgdata",
        "Options": {},
        "Scope": "local"
    }
]
```

3、docker 启动命令

```bash
docker rm -f redis-img-startline.txt-2
docker run --name redis-img-startline.txt-2  \
-v dv_pgdata:/app 10.50.10.185/harbortest/redis-mig:1.1 \
python3 redisMigrate.py 10.50.10.45 19000 10.50.10.170 7100 startline.txt.000
```

4、将需要变更的文件写入

![在这里插入图片描述](https://img-blog.csdnimg.cn/07fc645b7ddc4a06bbb0a0957a37da55.png)


## 随想

2023年2月2日13:42:43 

其实这个Dockerfile 可以使用git来管理， 如果有新的index 需要同步，直接在git提交需要迁移的index文件触发CICD,(continuous integration continuous deliver) ，将build好的镜像推送到镜像仓库.

使用迁移程序的的时候直接迁移即可.

## 参考

挂载权限问题: https://www.jianshu.com/p/83d787d50b61

