import os  
  
def file_name(file_dir):   
    
    for root, dirs, files in os.walk(file_dir):  
        #print(root) #当前目录路径  
        #print(dirs) #当前路径下所有子目录  
        #print(files) #当前路径下所有非目录子文件
        for file in files:
            if "(2)." in file:
                pth = os.path.join(root, file)
                print(pth)
                os.remove(pth) 
                #删除
    #print(root)
        
file_name(file_dir = "\\\\192.168.1.200\\Study\\13 得到全集\\03 每天听本书（更新中）\\")
