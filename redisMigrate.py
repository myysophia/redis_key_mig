#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：redis_key_mig 
@File ：redisMigrate.py
@Author ：ninesun
@Date ：22022年8月25日16:21:56
@Desc: 
'''
import sys

import redis
import time

from log.log import get_logger


# 迁移hash
def moveHash(cursor):
    cursor, data = r.hscan(key, cursor)
    for eachKey in data:
        rNew.hset(key, eachKey, data[eachKey])
    get_logger("---key:处理了---")
    print(key, "---处理了---", len(data), '个')
    if cursor != 0:
        print(cursor, "批处理")
        moveHash(cursor)
    else:
        print(cursor, "处理完成了")


# 迁移list
def moveList():
    length = r.llen(key)
    if length == 0:
        print(key, "---list迁移结束---剩余长度", length)
    else:
        # 每次迁移一千个
        start = length - 1000;
        if start < 0:
            start = 0
        data = r.lrange(key, start, -1)
        pl = r.pipeline();
        for eachI in data:
            setAdd = r.sadd("ordernokey_move", eachI);
            if setAdd == 1:
                pl.rpush("aaaaaaa", eachI)
            else:
                print("迁移的key的值重复了", eachI)
        pl.execute()
        if start == 0:
            # 清空
            r.ltrim(key, 1, 0)
        r.ltrim(key, 0, start - 1)
        moveList()

# 迁移soted set
def moveZset(keyStr):
    key = keyStr.lstrip()
    data = r.zrange(key, 0, -1, withscores='true')
    pl = r.pipeline();
    zcardRet = r.zcard(key)
    count = 1
    main_start = time.time()
    for eachI in data:
        score = str(eachI[1])
        value = eachI[0]
        # ch=true 仅仅是update 了score 才会，原封不动的zadd直接返回0
        if zcardRet > 0:
            zaddRet = rNew.zadd(key, {value: score}, ch='true');
            # rNew.delete(key)
            # if scoreRet != scoreRetNew:
            #     get_logger().error("数据不一致，key: %s,scoreRet: %s, scoreRetNew: %s",key,scoreRet,scoreRetNew)
            if zaddRet == 1:
                pl.zadd(key, {value: score})
                #get_logger().info("迁移的key的值%s,value: %s, score: %s", key, value, score)
            else:
                count = count + 1;
                # get_logger().info("迁移的key的值重复了,第: %s个key: %s,score: %s",count,key,scoreRet)
                # print("迁移的key的值重复了,key: ", key)
                # get_logger().info("---剩余长度: %s", length);
    main_end = time.time()
    duration = round((main_end - main_start), 3)
    get_logger().info("key: %s, 共:%s笔, 迁移总共花费%s s",key,zcardRet, duration)




# 打开文件
def  keyList():
    f = open("/pythontab/code.txt")  # 返回一个文件对象
    line = f.readline()  # 调用文件的 readline()方法
    while line:
        # print line,                 # 在 Python 2中，后面跟 ',' 将忽略换行符
        print(line, end='')  # 在 Python 3中使用
        line = f.readline()
    f.close()
    # for line in open("fl-key.txt"):
    #     print(line)

############################

if __name__ == '__main__':

    sourceHost = sys.argv[1]
    sourcePort = sys.argv[2]
    targetHost = sys.argv[3]
    targetPort = sys.argv[4]
    index = sys.argv[5]
    # key = sys.argv[1]

    # opeID 迁移
    # key = 'ope_array'
    # key = 'ope_cf'
    # key = 'ope_oc'

    #
    # key = 'prod_array'
    # key = 'prod_cf'
    # key = 'prod_oc'

    # key = 'basicOwn'

    # key = 'basicProd'
    #
    # print('输入的key是：' + key)
    # # ip = '47.254.149.109'
    # # password = 'Kikuu2018'

    ip1 = '10.50.10.45'

    ip2 = '10.50.10.170'

    # 连接redis  源库
    r = redis.Redis(host=sourceHost,  port=sourcePort, db=0,
                    decode_responses=True)

    # 连接redis  待接收的库
    rNew = redis.Redis(host=targetHost,  port=targetPort, db=0,
                       decode_responses=True)

    # with open('fl-key.txt', 'r') as f:
    #     lines = f.readlines()
    #     line_num = len(lines)
    #     print(lines)
    #     print(line_num)
    # moveZset('LINE_URL:/INDEX/202208/25/A1353IMRV02.TXT')

    # sour = sys.argv[1]
    # strT = sys.argv[2]

    get_logger().info("开始迁移---------关键信息: indexName:%s, sourceHost:%s, sourcePort:%s, targetHost:%s, targetPort:%s",index, sourceHost, sourcePort, targetHost, targetPort)
    # with open('fl-key.txt', 'r') as f:
    with open(index, 'r') as f:
        while True:
            line = f.readline()  # 逐行读取
            if not line:
                break
            #print(line),  # 这里加了 ',' 是为了避免 print 自动换行
            key=line.strip('\n')
            keyType = r.type(key)
            if keyType == 'string':
                s_start = time.time()
                #rNew.set(key, r.get(key))
                newValue = rNew.get(key)
                oldValue = r.get(key)
                s_end = time.time()
                s_duration = round((s_end - s_start), 3)
                get_logger().info("string-key= %s, oldValue: %s, newValue: %s 迁移到新库迁移总共花费%s s", key,oldValue,newValue, s_duration)
            if keyType == 'zset':
                moveZset(key)
                #get_logger().info("zset-key= %s迁移到新库", key)
    get_logger().info("迁移结束----------")
    # for line in open("fl-key.txt"):
    #     print(line.strip('\n'))
    #    # key = line.strip('\n')
    #     rNew.set(key, r.get(key))
    #     print("key=" + key + "迁移到新库:" + rNew)
        #keyType = r.type(key)
        #print(keyType, end='')
        #key = keyType.strip('\n')
        #print(keyType)
    #keyList()
    # if keyType == 'string':
    #     rNew.set(key, r.get(key))
    #     print("key=" + key + "迁移到新库:" + rNew)
    #
    # if keyType == 'hash':
    #     cursor = r.hlen(key)
    #     print(" key值长度是 + ", cursor)
    #     moveHash(0)
    #
    # if keyType == 'list':
    #     moveList()
