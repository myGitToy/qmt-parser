"""
本模块测试使用qlib进行因子的测试，调用deepseekAPI接口
需要计算的数据包括”
    核心评估指标是 RankIC (秩相关系数) 和 ICIR (信息系数的信息比率)这些指标用于衡量因子的选股能力和稳定性
"""


# 载入env 中deepseekAPI的key
import os
from pathlib import Path
from dotenv import load_dotenv
import qlib
from qlib.data import D
from qlib.contrib.evaluate import risk_analysis
import pandas as pd


def load_api_key():
    """从环境变量或.env文件加载DeepSeek API Key"""
    # 尝试从.env文件加载   
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
    return DEEPSEEK_API_KEY


def initialize_qlib(provider_uri: str = "~/.qlib/qlib_data/cn_data"):
    """初始化qlib"""
    qlib.init(provider_uri=provider_uri, region="cn")


def calculate_factor_metrics(factor_data: pd.DataFrame, 
                             return_data: pd.DataFrame) -> dict:
    """
    计算因子的RankIC和ICIR
    
    Args:
        factor_data: 因子值数据，index为datetime，columns为股票代码
        return_data: 收益率数据，index为datetime，columns为股票代码
    
    Returns:
        dict: 包含RankIC, ICIR等指标的字典
    """
    # 计算RankIC
    rank_ic = factor_data.corrwith(return_data, method='spearman', axis=1)
    
    metrics = {
        'mean_rank_ic': rank_ic.mean(),
        'std_rank_ic': rank_ic.std(),
        'icir': rank_ic.mean() / rank_ic.std() if rank_ic.std() != 0 else 0,
        'ic_positive_rate': (rank_ic > 0).sum() / len(rank_ic)
    }
    
    return metrics


def main():
    """主函数示例"""
    try:
        # 加载API Key
        api_key = load_api_key()
        print("DeepSeek API Key loaded successfully")
        
        # 初始化qlib
        initialize_qlib()
        print("Qlib initialized successfully")
        
        # TODO: 加载因子数据和收益率数据
        # factor_data = ...
        # return_data = ...
        
        # TODO: 计算指标
        # metrics = calculate_factor_metrics(factor_data, return_data)
        # print(f"Factor Metrics: {metrics}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()