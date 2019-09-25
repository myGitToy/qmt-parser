# -*- coding: utf-8 -*-
"""
文档说明【历史分笔数据】：
    所有股票的历史分笔数据处理
    主要完成事件匹配和事件数据输出，为QAR分析提供csv格式的raw_data
    引用规范：请使用下列语句
        import ags_event as event
基本框架：
    match   QAR事件和人名匹配，主要用于被ags.mysql_import_data调用
    export_ags_event_summary    导出月度（指定日期间）QAR事件率汇总表（每人一行，行数等同于飞行员人数）
    export_ags_event_summary_dep    将export_ags_event_summary的结果拆分成分部后导出到~/export 
                                    原计划这个功能将通过邮件发送拆分后的事件给各分部，现在搁置，由于担心分部滥用数据
    export_ags_event_person     导出月度（指定日期间）QAR所有事件含人名的表格（每月约7万条）
版本信息：
    version 0.1
    乔晖 2019/9/24
修改日志：

TODO LIST：
    
"""
import tushare as ts
import pandas as pd
class tick(object):
    def __init__(self,code,date):
        df = ts.get_tick_data(code,date,src='tt')
        print(df)
    pass


