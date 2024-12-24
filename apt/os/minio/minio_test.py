import os
from minio import Minio
from minio.error import S3Error

class MinioClientWrapper:
    def __init__(self, endpoint = None, access_key = None, secret_key = None, secure=False):
        if access_key is None or secret_key is None or endpoint is None:
            # 配置默认的参数
            endpoint="192.168.1.201:19000"
            access_key="A9LUdGKJSbSTyV9FrfsF"
            secret_key="dyyJTGH2bhqXp2ziyIzbJ8os3GOuEbPDauvdMq60"
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

    def create_bucket(self, bucket_name):
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def upload_file(self, bucket_name, object_name, file_path):
        self.client.fput_object(bucket_name, object_name, file_path)

    def download_file(self, bucket_name, object_name, file_path):
        self.client.fget_object(bucket_name, object_name, file_path)

    def remove_file(self, bucket_name, object_name):
        self.client.remove_object(bucket_name, object_name)

    def list_files(self, bucket_name, prefix=None):
        files = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
        return [obj.object_name for obj in files]
def create_local_file(file_path, content="Hello MinIO!"):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)




# 示例调用
# print(minio_client.list_files("hdf5", "akshare/data/1min"))
# 示例调用
if __name__ == "__main__":
    # 创建客户端
    minio_client = MinioClientWrapper()
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