import re

################ 老模块测试代码  ################ 
cap = "胡少波Tb,王沛德C2"
#初始化责任机长标识
cap_flag_loop=0
#######第二步：拆分和导入[机长]字段
if cap is not None and len(cap) > 0:
    #字段内有内容，拆分
    cap_list=cap.split("," )
    for n in cap_list:
        num=len(n)
        name=n[0:num-2]
        tech=n[num-2:num]
        if cap_flag_loop==0:
            cap_flag=1
        else:
            cap_flag=0
        cap_flag_loop=cap_flag_loop+1
        print("姓名：%s，|技术授权：%s,|责任机长标识=%d" % (name,tech,cap_flag))
        #将sql查询语句加载到多语句列表中

else:
    #字段内无内容，跳过
    pass


################# 新模块测试代码  ################ 
cap = "龚恒一C2.2,王沛德C2.3,李明Ta"
#初始化责任机长标识
cap_flag_loop=0
#######第二步：拆分和导入[机长]字段
if cap is not None and len(cap) > 0:
    #字段内有内容，拆分
    cap_list=cap.split("," )
    for n in cap_list:
        # 新版识别码格式：Ta Tb Tc C4 C4.3 C4.2 C3 C2.2 C2.3 C2.1 C1
        # 使用正则表达式匹配识别码部分（字母+数字，可能包含小数点）
        pattern = r'^(.*?)([A-Z][a-z]?|[A-Z]\d+(?:\.\d+)?)$'
        match = re.match(pattern, n.strip())
        
        if match:
            name = match.group(1)  # 姓名部分
            tech = match.group(2)  # 识别码部分
        else:
            # 如果匹配失败，使用旧逻辑作为备份
            num = len(n)
            name = n[0:num-2]
            tech = n[num-2:num]
        
        if cap_flag_loop==0:
            cap_flag=1
        else:
            cap_flag=0
        cap_flag_loop=cap_flag_loop+1
        print("姓名：%s，|技术授权：%s,|责任机长标识=%d" % (name,tech,cap_flag))
else:
    #字段内无内容，跳过
    pass