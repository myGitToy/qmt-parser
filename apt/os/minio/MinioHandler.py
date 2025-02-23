import os
import io
import pandas as pd
import numpy as np
import tables
import h5py
import os   #用于读取文件目录
from dotenv import load_dotenv #用于读取.env文件
from minio import Minio
from minio.error import S3Error
from apt.vendor.akshare.data import data as ak_data
from datetime import datetime
from apt.os.hdf5 import hdf5 as hdf5

class MinioClientWrapper:
    """
    Minio客户端封装类
    目前支持的功能有：
    1. 创建桶 create_bucket
    2. 列出所有桶 list_buckets
    3. 上传文件 upload_file
    4. 下载文件 download_file
    5. 删除文件 remove_file
    6. 列出桶中的所有文件 list_files
    7. 检查文件是否存在 file_exists
    8. 读取文件内容（二进制流） read_file
    9. 待增加
    """
    def __init__(self, endpoint = None, access_key = None, secret_key = None, secure=False, cache_path = None):
        """
        params（目前这些参数接口保留，但实际都是从本地的env环境变量配置文件中读取数据）:
            endpoint: MinIO服务端点
            access_key: MinIO访问密钥
            secret_key: MinIO访问密钥
            secure: 是否启用安全连接HTTPS
            cache_path: MinIO本地缓存路径
        对外参数：
            client: MinIO客户端对象（主接口）
            MINIO_CACHE_PATH: MinIO本地缓存路径

        """
        #读取.env文件
        load_dotenv()           
        # 定义默认缓存路径
        self.MINIO_CACHE_PATH = os.getenv('CACHE_PATH', "c:\\minio_cache")
        #检查缓存路径是否存在
        if not os.path.exists(self.MINIO_CACHE_PATH):
            os.makedirs(self.MINIO_CACHE_PATH, exist_ok=True)                
        # 检查参数是否有效    
        if access_key is None or secret_key is None or endpoint is None:
            # 配置默认的参数
            endpoint = os.getenv('ENDPOINT')
            access_key = os.getenv('ACCESS_KEY')
            secret_key = os.getenv('SECRET_KEY')
            
        self.client = Minio(
            endpoint = endpoint,
            access_key = access_key,
            secret_key = secret_key,
            secure = secure
        )
        if access_key is None or secret_key is None or endpoint is None:
            raise ValueError("MinIO客户端初始化失败，目前不允许自定义设置，仅从env文件中读取配置")

    def file_exists(self , bucket_name , object_name , case_sensitive = True) -> bool:
        """
        检查文件是否存在
        :param bucket_name: 桶名
        :param object_name: 文件名（带路径的，如akshare/data/1min/600000.SH.h5）
        :param case_sensitive: 是否区分大小写, 默认区分大小写
        """
        try:
            if case_sensitive:
                self.client.stat_object(bucket_name, object_name)
                return True
            else:
                objects = self.client.list_objects(bucket_name, prefix=object_name, recursive=True)
                for obj in objects:
                    if obj.object_name.lower() == object_name.lower():
                        return True
                return False
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                raise e
            
    def read_file(self, bucket_name, object_name, encoding='utf-8'):
        """
        读取文件内容(二进制流式传输)
        :param bucket_name: 桶名称
        :param object_name: 对象名称(文件路径)
        :param encoding: 文件编码,默认utf-8
        :return: 文件内容
        """
        try:
            # 获取文件数据
            data = self.client.get_object(bucket_name, object_name)
            # 读取内容
            content = data.read()
            # 如果是HDF5文件，直接返回二进制内容（针对HDF5做特别优化）
            # 备注：由于HDF5文件采用pd.HDFStore存储，直接读取二进制有困难，因此采用下载至临时文件夹的方法
            # 临时文件夹默认位于os.getenv("MINIO_CACHE_PATH", "c:\minio_cache")
            if object_name.lower().endswith('.h5'):
                raise NotImplementedError("HDF5文件读取需要特殊处理")       
            # 如果是文本文件,进行解码
            if encoding:
                return content.decode(encoding)
            # 如果是二进制文件,直接返回
            return content
        except S3Error as err:
            print(f"Error reading file: {err}")
            raise    

    def create_bucket(self, bucket_name):
        """
        创建桶
        params:bucket_name: 桶名称
        """      
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def list_buckets(self) -> pd.DataFrame:
        """
        列出所有桶
        params:
        return: pandas.DataFrame
        """
        buckets = self.client.list_buckets()
        return pd.DataFrame([bucket.__dict__ for bucket in buckets])
    
    def upload_file(self, bucket_name, object_name, file_path)->bool:
        """
        上传文件
        params:
            bucket_name: 桶名称 例hdf5
            object_name: 带路径的对象名称（不包括桶名称） 例akshare/data/1min/600000.SH.h5
                备注：桶名称和路径如果填写错误，则会自动创建
            file_path: 文件路径 例c:\\data\\1min\\600000.SH.h5
        """
        # 检查file_path是否有效
        if not os.path.exists(file_path):
            # 文件路径不存在，跳过上传，返回False
            return False
        try:
            self.client.fput_object(bucket_name, object_name, file_path)
            return True
        except Exception:
            return False

    def download_file(self, bucket_name, object_name, file_path)->bool:
        """
        下载文件
        params:
            bucket_name: 桶名称 例akshare
            object_name: 带路径的对象名称（不包括桶名称） 例akshare/data/1min/600000.SH.h5
            file_path: 文件路径 例c:\\data\\1min\\600000.SH.h5
        return: bool 是否下载成功        
        """
        # 检查file_path是否有效
        if not os.path.exists(os.path.dirname(file_path)):
            # 路径不存在，创建对应的路径
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            return True
        except Exception:
            return False

    def remove_file(self, bucket_name, object_name):
        self.client.remove_object(bucket_name, object_name)

    def list_files(self, bucket_name, prefix=None):
        files = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
        return [obj.object_name for obj in files]
    def create_local_file(file_path, content="Hello MinIO!"):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_object(self, bucket_name, object_name):
        """
        获取对象，返回 Minio 客户端的对象数据
        如果hdf5文件，需要使用get_object读取二进制流，以避免HDF5文件的读取问题
        pandas.read_hdf() 无法直接读取二进制数据，需要将二进制数据包装为文件流
        """        
        return self.client.get_object(bucket_name, object_name)



# 示例调用
# print(minio_client.list_files("hdf5", "akshare/data/1min"))
# 示例调用
if __name__ == "__main__":
    # 创建客户端
    minio_client = MinioClientWrapper()
    # 演示：列出所有桶
    print(minio_client.list_buckets())
    # 演示：检查文件是否存在
    print(minio_client.file_exists("hdf5", "akshare/data/1min/600000.sh.h5"))  # False
    # 演示：下载文件
    file_name = "600000.SH.h5"
    #download_path = os.path.join(cache_dir, "akshare", "data", "1min", file_name)
    download_path = os.path.join(minio_client.MINIO_CACHE_PATH, file_name)
    is_success = minio_client.download_file("hdf5", f"akshare/data/1min/{file_name}", download_path)
    print(f"Downloaded file: {is_success}")
    # 演示：上传文件
    file_name = "600000_test.SH.h5"
    local_file = os.path.join(minio_client.MINIO_CACHE_PATH,file_name)
    is_success = minio_client.upload_file("hdf5", f"akshare/data/1min_test/{file_name}", local_file)
    print(f"Uploaded file: {is_success}")
    # 演示：读取文件内容（二进制）（copilot代码）
    #content = minio_client.read_file("hdf5", "akshare/data/1min_test/000001.SZ.h5")
    # 演示：读取文件内容（二进制）（deepseek代码）
    #   从 Minio 读取二进制数据
    binary_data = minio_client.get_object("hdf5", f"akshare/data/1min_test/{file_name}").read()
    #   将二进制数据包装为文件流
    data_buffer = io.BytesIO(binary_data)
    #   读取 HDF5 文件，指定 key（数据集路径）
    df = pd.read_hdf(data_buffer, key="RawData")  # 替换为实际路径
    print(df)
    ############## 以下代码均为临时测试代码 ################
    # 读取HDF5文件内容，转换为DataFrame
    df_ak = pd.DataFrame() #ak主数据
    a = ak_data()
    a.start_date = datetime(2023,3,12,8)
    a.end_date = datetime(2024,3,20,16)
    a.fq = ak_data.复权.动态复权
    a.code = '601318.sh'
    a.ktype = '1m'

#   从 MinioClientWrapper 获取对象流并写入内存缓冲区
    buffer = io.BytesIO(content)
    with h5py.File(buffer, 'r') as file:
        def visit_item(name, node):
            if isinstance(node, h5py.Dataset):
                print("Dataset:", name)
            else:
                print("Group:", name)
        file.visititems(visit_item)
    #raw_data = file['RawData/table'][:]
    pd_df = pd.read_hdf(content, key='RawData')
    print(pd_df)
    #print(raw_data)
    #with pd.HDFStore(buffer, mode='r') as store:
        #df_buffer = store['RawData']
    #print(df_ak)

    # 使用tables直接从内存读取
    df = pd.read_hdf(io.BytesIO(content), key='RawData')
    print(content)
    arr = np.frombuffer(content, dtype=np.uint8)
    fileh = tables.open_file(arr.tobytes(), mode='r', driver="H5FD_CORE", 
                            driver_core_image=content,
                            driver_core_backing_store=0)
    # 打印文件结构以便调试
    print("HDF5文件结构:")
    fileh.list_nodes('/')

    # 正确读取表数据
    table = fileh.get_node('/', 'RawData')  # 获取根目录下的RawData节点
    df = pd.DataFrame(table[:])  # 使用切片操作读取所有数据
    
    print("\n数据预览:")
    print(df.head())    
    fileh.close()
    # 使用get_node读取数据
    tables2 = fileh.get_node('/RawData')
    df2 = pd.DataFrame(tables2.read())
    print(df2)
    print(tables2)
    # 转换为DataFrame
    df = pd.DataFrame(fileh.root['RawData'][:])
    fileh.close()
    print(df)

    # 使用BytesIO读取HDF5数据
    with io.BytesIO(content) as bio:
        df = pd.read_hdf(
            bio, 
            key='RawData',
            where=f"date >='{a.start_date}' and date <='{a.end_date}'"
        )
    #####1.1 从mysql中取出时间段内的所有数据（
    #df = ts.pro_bar(api = a.api , ts_code = a.code , freq = '1min' , adj = None , start_date = dt.strftime('%Y-%m-%d %H:%M:%S') , end_date = tmp_end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
    #df = a.get_k_data() #从数据库中读取数据
    print(df)
    df_h5 = hdf5(a).data_query()
    print(df_h5)




    # 显示某个桶里的全部文件
    print(minio_client.list_files("hdf5", "akshare/data/1min"))
    test_bucket = "testbucket"
    minio_client.create_bucket(test_bucket)

    local_file = "test.txt"
    create_local_file(local_file, "这是文件内容")
    minio_client.upload_file(test_bucket, "test.txt", local_file)
    minio_client.download_file(test_bucket, "test.txt", "downloaded_test.txt")
    print(minio_client.list_files(test_bucket))
    minio_client.remove_file(test_bucket, "test.txt")

    if os.path.exists(local_file):
        os.remove(local_file)