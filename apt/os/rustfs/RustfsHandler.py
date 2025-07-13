import os
import io
import pandas as pd
import numpy as np
import tables
import h5py
import os   #用于读取文件目录
from dotenv import load_dotenv #用于读取.env文件
import boto3    #aws通用s3接口
from botocore.client import Config  #aws通用s3接口
from botocore.exceptions import ClientError
from apt.vendor.akshare.data import data as ak_data
from datetime import datetime
from apt.os.hdf5.hdf5Handler import hdf5ClientWrapper

class RustfsClientWrapper:
    """
    Rustfs客户端封装类（兼容S3协议）\n
    Attributes:
        RUSTFS_CACHE_PATH (str): 本地缓存路径
        client: boto3 S3客户端对象

    Methods:
        create_bucket(bucket_name): 创建桶
        list_buckets(): 列出所有桶

        file_exists(bucket_name, object_name): 检查文件是否存在
        read_file(bucket_name, object_name, encoding='utf-8'): 读取文件内容
        upload_file(bucket_name, object_name, file_path): 上传文件
        download_file(bucket_name, object_name, file_path): 下载文件
        remove_file(bucket_name, object_name): 删除文件
        list_files(bucket_name, prefix=None): 罗列文件

    目前支持的功能有：
    1. 创建桶 create_bucket
    2. 删除桶 delete_bucket
    3. 列出所有桶 list_buckets
    4. 列出桶中的所有文件 list_files
    5. 上传文件 upload_file
    6. 下载文件 download_file
    7. 删除文件 remove_file
    8. 检查文件是否存在 file_exists
    9. 读取文件内容（二进制流） read_file
    10. 待增加
    备注：如果要对Rustfs文件系统中的hdf5进行操作，请使用专用接口os.RustfsHDF5.py
    """
    def __init__(self, endpoint = None, access_key = None, secret_key = None, secure=False, cache_path = None):
        """
        Parameters:
            endpoint: Rustfs服务端点
            access_key: Rustfs访问密钥
            secret_key: Rustfs访问密钥
            secure: 是否启用安全连接HTTPS
            cache_path: Rustfs本地缓存路径

        Returns:
            N/A
        
        Attributes: 
            对类属性进行说明。

        Yields: 
            用于生成器函数，描述 yield 的值。

        Examples: 
            给出使用示例。

        Notes: 
            对外参数：client: boto3 S3客户端对象（主接口）
            RUSTFS_CACHE_PATH: Rustfs本地缓存路径

        See Also: 
            引用相关资源或文档。

        References: 
            （目前这些参数接口保留，但实际都是从本地的env环境变量配置文件中读取数据）
           
        """
        #读取.env文件
        load_dotenv()           
        # 定义默认缓存路径
        self.RUSTFS_CACHE_PATH = os.getenv('RUSTFS_CACHE_PATH', "c:\\minio_cache")
        #检查缓存路径是否存在
        if not os.path.exists(self.RUSTFS_CACHE_PATH):
            os.makedirs(self.RUSTFS_CACHE_PATH, exist_ok=True)                
        # 检查参数是否有效    
        if access_key is None or secret_key is None or endpoint is None:
            # 配置默认的参数
            endpoint = os.getenv('RUSTFS_ENDPOINT')
            access_key = os.getenv('RUSTFS_ACCESS_KEY')
            secret_key = os.getenv('RUSTFS_SECRET_KEY')
            
        # 构建endpoint URL
        if endpoint and not endpoint.startswith('http'):
            endpoint_url = f"http://{endpoint}"
        else:
            endpoint_url = endpoint
            
        # 创建 boto3 S3 客户端
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        if access_key is None or secret_key is None or endpoint is None:
            raise ValueError("Rustfs客户端初始化失败，目前不允许自定义设置，仅从env文件中读取配置")

    def file_exists(self , bucket_name , object_name , case_sensitive = True) -> bool:
        """
        检查文件是否存在

        Parameters:
            bucket_name: 桶名
            object_name: 文件名（带路径的，如akshare/data/1min/600000.SH.h5）
            case_sensitive: 是否区分大小写, 默认区分大小写
        
        Returns:
            bool: True if the file exists, False otherwise.        
        """
        try:
            if case_sensitive:
                self.client.head_object(Bucket=bucket_name, Key=object_name)
                return True
            else:
                # 对于不区分大小写的搜索，需要列出所有对象进行比较
                response = self.client.list_objects_v2(Bucket=bucket_name, Prefix=object_name)
                for obj in response.get('Contents', []):
                    if obj['Key'].lower() == object_name.lower():
                        return True
                return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
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
            response = self.client.get_object(Bucket=bucket_name, Key=object_name)
            # 读取内容
            content = response['Body'].read()
            # 如果是HDF5文件，直接返回二进制内容（针对HDF5做特别优化）
            # 备注：由于HDF5文件采用pd.HDFStore存储，直接读取二进制有困难，因此采用下载至临时文件夹的方法
            # 临时文件夹默认位于os.getenv("RUSTFS_CACHE_PATH", "c:\minio_cache")
            if object_name.lower().endswith('.h5'):
                raise NotImplementedError("HDF5文件读取需要特殊处理")       
            # 如果是文本文件,进行解码
            if encoding:
                return content.decode(encoding)
            # 如果是二进制文件,直接返回
            return content
        except ClientError as err:
            print(f"Error reading file: {err}")
            raise    

    def create_bucket(self, bucket_name) -> bool:
        """
        创建桶
        params: bucket_name: 桶名称
        return: bool - 如果成功创建则返回True，如果桶已经存在则返回False
        """      
        try:
            self.client.create_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyOwnedByYou':
                return False
            else:
                raise e
    
    def delete_bucket(self, bucket_name) -> bool:
        """
        删除桶
        params: bucket_name: 桶名称
        return: bool - 如果成功删除则返回True，如果桶不存在则返回False
        """
        try:
            self.client.delete_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return False
            else:
                raise e

    def list_buckets(self) -> pd.DataFrame:
        """
        列出所有桶及其对象信息
        return: pandas.DataFrame 包含桶名称、创建日期、对象数及总大小
        """
        response = self.client.list_buckets()
        buckets = response.get('Buckets', [])
        data = []
        for bucket in buckets:
            bucket_name = bucket['Name']
            try:
                # 获取桶中的对象信息
                objects_response = self.client.list_objects_v2(Bucket=bucket_name)
                objects = objects_response.get('Contents', [])
                count = len(objects)
                total_size = sum(obj['Size'] for obj in objects)
                
                def sizeof_fmt(num, suffix="B"):
                    for unit in ["", "K", "M", "G", "T"]:
                        if abs(num) < 1024.0:
                            return f"{num:3.1f} {unit}{suffix}"
                        num /= 1024.0
                    return f"{num:.1f} P{suffix}"
                
                bucket_info = {
                    '桶名称': bucket_name,
                    '创建日期': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M'),
                    '总文件数': count,
                    '总大小': sizeof_fmt(total_size)
                }
                data.append(bucket_info)
            except ClientError as e:
                # 如果无法访问桶，记录错误信息
                bucket_info = {
                    '桶名称': bucket_name,
                    '创建日期': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M'),
                    '总文件数': 'Error',
                    '总大小': 'Error'
                }
                data.append(bucket_info)
        return pd.DataFrame(data)
    
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
            self.client.upload_file(file_path, bucket_name, object_name)
            return True
        except Exception:
            return False

    def download_file(self, bucket_name, object_name, file_path)->bool:
        """
        下载文件\n
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
        try:
            self.client.download_file(bucket_name, object_name, file_path)
            return True
        except Exception:
            return False

    def remove_file(self, bucket_name, object_name):
        """
        删除文件
        params:
            bucket_name: 桶名称
            object_name: 对象名称（文件路径）
        """
        self.client.delete_object(Bucket=bucket_name, Key=object_name)

    def list_files(self, bucket_name, prefix=None) -> pd.DataFrame:
        """
        列出指定 bucket 中的所有文件，可根据前缀进行过滤，并返回包含详细信息的 DataFrame。

        参数:
            bucket_name (str): 要列出文件的 bucket 名称。
            prefix (str, 可选): 用于过滤对象的前缀。如果提供的话，只返回对象名称以此前缀开始的文件。

        返回:
            pandas.DataFrame: 包含文件详细信息，列包括文件名称、修改日期、文件大小（智能化格式）等。
        """
        try:
            if prefix:
                response = self.client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            else:
                response = self.client.list_objects_v2(Bucket=bucket_name)
            
            objects = response.get('Contents', [])
            data = []
            for obj in objects:
                def sizeof_fmt(num, suffix="B"):
                    for unit in ["", "K", "M", "G", "T"]:
                        if abs(num) < 1024.0:
                            return f"{num:3.1f}{unit}{suffix}"
                        num /= 1024.0
                    return f"{num:.1f}P{suffix}"
                
                file_info = {
                    "文件名称": obj['Key'],
                    "修改日期": obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                    "文件大小": sizeof_fmt(obj['Size'])
                }
                data.append(file_info)
            return pd.DataFrame(data)
        except ClientError as e:
            print(f"Error listing files: {e}")
            return pd.DataFrame()  # 返回空DataFrame
    

    def create_local_file(file_path, content="Hello MinIO!"):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_object(self, bucket_name, object_name):
        """
        获取对象，返回 boto3 S3 客户端的对象数据
        如果hdf5文件，需要使用get_object读取二进制流，以避免HDF5文件的读取问题
        pandas.read_hdf() 无法直接读取二进制数据，需要将二进制数据包装为文件流
        """        
        response = self.client.get_object(Bucket=bucket_name, Key=object_name)
        return response['Body']



# 示例调用
# print(rustfs_client.list_files("hdf5", "akshare/data/1min"))
# 示例调用
if __name__ == "__main__":
    # 创建客户端
    rustfs_client = RustfsClientWrapper()
    # 演示：列出所有桶
    print(rustfs_client.list_buckets())
    # 演示：检查文件是否存在
    print(rustfs_client.file_exists("hdf5", "akshare/data/1min/600000.sh.h5"))  # False
    # 演示：下载文件
    file_name = "600000.SH.h5"
    #download_path = os.path.join(cache_dir, "akshare", "data", "1min", file_name)
    download_path = os.path.join(rustfs_client.RUSTFS_CACHE_PATH, file_name)
    is_success = rustfs_client.download_file("hdf5", f"/akshare/data/1min/{file_name}", download_path)
    print(f"Downloaded file: {is_success}")
    # 演示：上传文件
    file_name = "600000_test.SH.h5"
    local_file = os.path.join(rustfs_client.RUSTFS_CACHE_PATH,file_name)
    is_success = rustfs_client.upload_file("hdf5", f"akshare/data/1min_test/{file_name}", local_file)
    print(f"Uploaded file: {is_success}")
    # 演示：读取文件内容（二进制）（copilot代码）
    #content = rustfs_client.read_file("hdf5", "akshare/data/1min_test/000001.SZ.h5")
    # 演示：读取文件内容（二进制）（deepseek代码）
    #   从 Rustfs 读取二进制数据
    binary_data = rustfs_client.get_object("hdf5", f"akshare/data/1min_test/{file_name}").read()
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




    #####1.1 从mysql中取出时间段内的所有数据（
    #df = ts.pro_bar(api = a.api , ts_code = a.code , freq = '1min' , adj = None , start_date = dt.strftime('%Y-%m-%d %H:%M:%S') , end_date = tmp_end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
    #df = a.get_k_data() #从数据库中读取数据
    print(df)
    df_h5 = hdf5ClientWrapper(a).data_query()
    print(df_h5)
