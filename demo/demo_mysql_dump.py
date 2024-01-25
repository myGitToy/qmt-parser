import subprocess

def import_database(db_name, dump_file_path):
    try:
        # 构建mysql命令
        cmd = f'mysql --binary-mode=TRUE --user=root --password=sal62688558 --default-character-set=utf8mb4 {db_name} < {dump_file_path}'
        #完整的字符串命令如下，使用mysql自带的命令行也可以，需要将bin添加到系统环境变量中
        #mysql --binary-mode=TRUE --user=root --password=sal62688558 stock < C:\mysqldump20230406\stock_tspro_1d.sql
        # 使用subprocess执行命令
        subprocess.run(cmd, shell=True, check=True)

        print("Database import successful.")
    except subprocess.CalledProcessError as e:
        print(f"Database import failed. Error: {e}")

def import_database_V2(db_name, dump_file_path):
    try:
        # 构建mysql命令
        cmd = ['mysql', '-u', 'stock_user', '-p', 'atp73V4', db_name]

        # 打开dump文件
        with open(dump_file_path, 'r') as file:
            # 使用subprocess执行命令
            subprocess.run(cmd, stdin=file, check=True)

        print("Database import successful.")
    except subprocess.CalledProcessError as e:
        print(f"Database import failed. Error: {e}")

# 使用函数导入数据库
import_database('stock', 'C:\\mysqldump20230406\\stock_tspro_1m.sql')
