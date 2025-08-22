import requests
import json
import os
import datetime
import pandas as pd

class KlbqDataFetcher:
    """卡拉彼丘数据获取器
    用于从游戏API获取英雄数据并保存到本地文件
    """
    def __init__(self):
        """初始化数据获取器，设置基础URL和请求头"""
        self.session = requests.Session()
        self.api_url = "https://klbq-prod-www.idreamsky.com/api/common/ide"
        # 设置请求头，模拟移动设备浏览器
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://klbq.idreamsky.com",
            "Referer": "https://klbq.idreamsky.com/",
            "Content-Type": "application/json"
        }
        
    def get_ide_params(self):
        """获取IDE API所需的默认参数
        Returns:
            dict: 包含iChartId和sIdeToken的参数字典
        """
        print("使用默认参数")
        return {
            "iChartId": "338985",
            "sIdeToken": "b7FM3m"
        }
    
    def make_ide_request(self, params=None, map_code="-255", rank_codes=["2"]):
        """发送IDE API请求
        Args:
            params (dict, optional): API请求参数
            map_code (str, optional): 地图代码
            rank_codes (list, optional): 段位代码列表
        Returns:
            dict or None: API响应结果，如果请求失败则返回None
        """
        # 使用默认参数或传入的参数
        params = params or self.get_ide_params()
                
        # 准备请求数据
        data = {
            "iChartId": params["iChartId"],
            "iSubChartId": params["iChartId"],
            "sIdeToken": params["sIdeToken"],
            "mode": "5",
            "map": map_code,
            "rank": rank_codes,
            "season1": "11",
            "season2": "0"
        }
        
        try:
            print(f"发送API请求 (map: {map_code}, rank: {rank_codes})...")
            response = self.session.post(
                self.api_url, 
                headers=self.headers, 
                json=data, 
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API请求失败: {e}")
            return None
    
    def fetch_data(self, map_code="-255", rank_codes=["2"]):
        """获取数据的完整流程
        Args:
            map_code (str): 地图代码
            rank_codes (list): 段位代码列表
        Returns:
            dict or None: 获取的数据，如果失败则返回None
        """
        print(f"开始获取卡拉彼丘数据 (map: {map_code}, rank: {rank_codes})...")
        
        # 获取参数并发送请求
        params = self.get_ide_params()
        #print(f"使用的参数: {params}")
        result = self.make_ide_request(params, map_code, rank_codes)
        
        if result:
            print("数据获取成功!")
            return result
        else:
            print("数据获取失败")
            return None

# 读取配置文件
def load_config(config_path="配置.json"):
    """从配置文件中加载地图和段位信息
    Args:
        config_path (str): 配置文件路径
    Returns:
        tuple: (maps, ranks) 包含地图和段位信息的列表
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            maps = []
            ranks = []
            
            if "data" in config and "value" in config["data"] and "setting" in config["data"]["value"]:
                setting = config["data"]["value"]["setting"]
                
                # 提取map配置
                if "map" in setting:
                    for item in setting["map"]:
                        try:
                            content = json.loads(item["content"])
                            maps.append({
                                "code": content["code"],
                                "name": content["name"]
                            })
                        except Exception as e:
                            print(f"解析map配置项失败: {e}")
                
                # 提取rank配置
                if "rank" in setting:
                    for item in setting["rank"]:
                        try:
                            content = json.loads(item["content"])
                            ranks.append({
                                "code": content["code"],
                                "name": content["name"]
                            })
                        except Exception as e:
                            print(f"解析rank配置项失败: {e}")
            
            return maps, ranks
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return [], []

# 使用示例
if __name__ == "__main__":
    # 加载配置
    maps, ranks = load_config()
    print(f"加载到 {len(maps)} 个map配置和 {len(ranks)} 个rank配置")
    
    if not maps or not ranks:
        print("配置加载失败，无法继续执行")
    else:
        fetcher = KlbqDataFetcher()
        
        # 创建一个空的DataFrame用于存储所有数据
        all_data = pd.DataFrame(columns=[
            '角色名字', '阵营', '胜率', '选取率', 'kd', '平均伤害', '表现分', '地图', '段位', '赛季', '时间'
        ])
        
        # 遍历所有map和rank组合
        for map_item in maps:
            for rank_item in ranks:
                # 获取当前时间
                current_time = datetime.datetime.now()
                time_str = current_time.strftime("%Y/%m/%d %H:%M:%S")
                
                # 获取数据
                data = fetcher.fetch_data(map_code=map_item['code'], rank_codes=[rank_item['code']])
                
                if data and "jData" in data and "data1" in data["jData"]:
                    data1 = data["jData"]["data1"]
                    map_name = map_item['name']
                    rank_name = rank_item['name']
                    
                    # 处理进攻方数据 (side1)
                    if data1.get('side1'):
                        for hero in data1['side1']:
                            # 提取英雄数据
                            hero_name = hero.get('heroName', '未知')
                            win_rate = hero.get('winRate', 0)
                            select_rate = hero.get('selectRate', 0)
                            kd = hero.get('kd', 0)
                            damage_ave = hero.get('damageAve', 0)
                            score = hero.get('score', 0)
                            
                            # 添加到DataFrame
                            new_row = pd.DataFrame({
                                '角色名字': [hero_name],
                                '阵营': ['进攻方'],
                                '胜率': [win_rate],
                                '选取率': [select_rate],
                                'kd': [kd],
                                '平均伤害': [damage_ave],
                                '表现分': [score],
                                '地图': [map_name],
                                '段位': [rank_name],
                                '赛季': ['11'],  # season1的值
                                '时间': [time_str]
                            })
                            all_data = pd.concat([all_data, new_row], ignore_index=True)
                    
                    # 处理防守方数据 (side2)
                    if data1.get('side2'):
                        for hero in data1['side2']:
                            # 提取英雄数据
                            hero_name = hero.get('heroName', '未知')
                            win_rate = hero.get('winRate', 0)
                            select_rate = hero.get('selectRate', 0)
                            kd = hero.get('kd', 0)
                            damage_ave = hero.get('damageAve', 0)
                            score = hero.get('score', 0)
                            
                            # 添加到DataFrame
                            new_row = pd.DataFrame({
                                '角色名字': [hero_name],
                                '阵营': ['防守方'],
                                '胜率': [win_rate],
                                '选取率': [select_rate],
                                'kd': [kd],
                                '平均伤害': [damage_ave],
                                '表现分': [score],
                                '地图': [map_name],
                                '段位': [rank_name],
                                '赛季': ['11'],  # season1的值
                                '时间': [time_str]
                            })
                            all_data = pd.concat([all_data, new_row], ignore_index=True)
                    
                    print(f"已处理 {map_name} - {rank_name} 的数据")
                else:
                    print(f"获取数据失败或数据格式不正确 (map: {map_item['name']}, rank: {rank_item['name']})")
        
        # 保存到Excel文件
        excel_file = f"klbq_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        all_data.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"所有数据已保存到 {excel_file}")