# -*- coding:utf-8 -*-
# @Time   : 2020-07-29
# @Author : Dingjs

#DB基本信息
import os
import time
import datetime
import glob
import shutil
"""
Python3.7 来执行mysql数据备份操作
自动保持7天的数据
备份的sql文件名精确到时分秒，这样即使一天备份多次，也不会进行覆盖
"""

#数据库基本信息设定
#stock_user:a@1#Yy1c@localhost:3306/stock'
DB_HOST = 'localhost'
DB_USER = 'stock_user'
DB_USER_PASSWORD = 'a@1#Yy1c'
DB_PORT = '3306'

#多库备份
#写法一：把需要备份的库名写到txt文件中，然后读取txt文件内的数据
#DB_NAME = '/backup/dbnames.txt'

#写法二：通过执行sql语句来匹配下载的库
# sqlStr1 = "show databases like 'iot%'"

#单库备份
DB_NAME = 'stock'

#备份路径
BACKUP_PATH = './conn_DB/sql_path/'
#设置编码格式
DB_CharSet = 'utf8'
#创建datatime，作为备份文件名称
DATETIME = time.strftime('%Y%m%d')
#这里主要是做.sql文件的日期区分
DT_time = time.strftime("%Y%m%d_%H%M%S")
TODAYBACKUPPATH = BACKUP_PATH + DATETIME

#保留7天的备份文件
print ('del folder seven days ago')
folders = glob.glob('/backup/dbbackup/*')
today = datetime.datetime.now()
for item in folders:
    try:
        foldername = os.path.split(item)[1]
        day = datetime.datetime.strptime(foldername, "%Y%m%d")
        diff = today - day
        if diff.days >= 7:
            shutil.rmtree(item)
    except:
        pass

print("creating backup folder")
#查看备份文件夹是否存在，不存在，则创建

if not os.path.exists(TODAYBACKUPPATH):
    os.makedirs(TODAYBACKUPPATH)

# Code for checking if you want to take single database backup or assinged multiple backups in DB_NAME.
#开始备份文件
print ("checking for databases names file.")
if os.path.exists(DB_NAME):
    file1 = open(DB_NAME)
    multi = 1
    print("Databases file found...")
    print ("Starting backup of all dbs listed in file " + DB_NAME)
else:
    print ("Databases file not found...")
    print ("Starting backup of database " + DB_NAME)
    multi = 0

# Starting actual database backup process.

if multi:
   in_file = open(DB_NAME,"r")
   flength = len(in_file.readlines())
   in_file.close()
   p = 1
   dbfile = open(DB_NAME,"r")

   while p <= flength:
       # 从数据库读取文件
       db = dbfile.readline()
       db = db[:-1]

       #在python中通过cmd执行mysqldump备份语句
       # dumpcmd = "mysqldump -u " + DB_USER + "-h"+DB_HOST + " -p" + DB_USER_PASSWORD + " " + db + " > " + TODAYBACKUPPATH + "/" + db + ".sql"
       # os.system(dumpcmd)
		#在python中通过cmd来执行mysqldump命令的另一种写法
       os.system( "mysqldump -h%s -u%s -p%s %s --default_character-set=%s > %s/%s_%s.sql" % (
           DB_HOST, DB_USER, DB_USER_PASSWORD, db, DB_CharSet, TODAYBACKUPPATH, DT_time, db))

       p = p + 1
   dbfile.close()
else:
   db = DB_NAME
   # dumpcmd = "mysqldump -u " + DB_USER + " -p" + DB_USER_PASSWORD + " " + db + " > " + TODAYBACKUPPATH + "/" + db + ".sql"
   # os.system(dumpcmd)
   os.system("mysqldump -h%s -u%s -p%s %s --default_character-set=%s > %s/%s_%s.sql" % (
       DB_HOST, DB_USER, DB_USER_PASSWORD, db, DB_CharSet, TODAYBACKUPPATH,DT_time, db))

#结束后，打印执行状态信息
print ("Backup script completed")
print("Your backups has been created in '" + TODAYBACKUPPATH + "' directory")
