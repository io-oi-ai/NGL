import logging
import requests
import aiohttp
from typing import Optional, Dict, Any, List
import asyncio

class DexScreenerAPI:
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex"
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.twitter_url = "https://api.twitter.com/2"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def get_comprehensive_token_info(self, token_address: str) -> Dict[str, Any]:
        """获取综合代币信息"""
        try:
            # 并行获取各个数据源的信息
            tasks = [
                self._get_dex_data(token_address),
                self._get_coingecko_data(token_address),
                self._get_social_data(token_address),
                self._get_market_sentiment(token_address)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 合并所有数据
            comprehensive_data = {
                'dex_data': results[0],
                'coingecko_data': results[1],
                'social_data': results[2],
                'sentiment': results[3]
            }
            
            return comprehensive_data
            
        except Exception as e:
            logging.error(f"获取综合代币信息失败: {e}")
            return {}

    async def _get_dex_data(self, token_address: str) -> Dict[str, Any]:
        """获取DEX数据"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/tokens/{token_address}"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_token_data(data)
        return {}

    async def _get_coingecko_data(self, token_address: str) -> Dict[str, Any]:
        """获取CoinGecko数据"""
        try:
            async with aiohttp.ClientSession() as session:
                # 获取代币信息
                url = f"{self.coingecko_url}/coins/ethereum/contract/{token_address}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                            'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                            'community_data': data.get('community_data', {}),
                            'developer_activity': data.get('developer_data', {})
                        }
            return {}
        except Exception as e:
            logging.error(f"获取CoinGecko数据失败: {e}")
            return {}

    async def _get_social_data(self, token_address: str) -> Dict[str, Any]:
        """获取社交媒体数据"""
        try:
            # 这里可以添加Twitter、Telegram等社交媒体的API调用
            social_data = {
                'twitter': {
                    'followers': 0,
                    'engagement_rate': 0,
                    'sentiment': 'neutral'
                },
                'telegram': {
                    'members': 0,
                    'active_users': 0,
                    'messages_per_day': 0
                }
            }
            return social_data
        except Exception as e:
            logging.error(f"获取社交数据失败: {e}")
            return {}

    async def _get_market_sentiment(self, token_address: str) -> Dict[str, Any]:
        """分析市场情绪"""
        try:
            # 可以添加更多数据源来分析市场情绪
            sentiment_data = {
                'overall': 'neutral',
                'social_sentiment': 'neutral',
                'trading_sentiment': 'neutral',
                'news_sentiment': 'neutral'
            }
            return sentiment_data
        except Exception as e:
            logging.error(f"获取市场情绪数据失败: {e}")
            return {}

    def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """获取代币信息"""
        try:
            # 判断是否为 Solana 地址
            is_solana = len(token_address) in [32, 44]
            
            url = f"{self.base_url}/tokens/{token_address}"
            logging.info(f"请求 DexScreener API: {url}")
            
            response = requests.get(
                url,
                timeout=10,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and len(data['pairs']) > 0:
                    # 如果是 Solana，过滤出 Solana 的交易对
                    if is_solana:
                        pairs = [p for p in data['pairs'] if p.get('chainId') == 'solana']
                        if pairs:
                            data['pairs'] = pairs
                        else:
                            return None
                    return self._process_token_data(data)
                    
            logging.warning(f"未找到该代币的交易对信息")
            return None
            
        except Exception as e:
            logging.error(f"DexScreener API 调用错误: {e}")
            return None

    def get_hot_tokens(self, chain: str = 'bsc', limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门代币"""
        try:
            # 使用搜索端点，按交易量排序
            url = f"{self.base_url}/search"
            params = {
                'chainIds': chain,  # 指定链
                'sortBy': 'volume',  # 按交易量排序
                'sortOrder': 'desc', # 降序排序
                'limit': limit
            }
            
            logging.info(f"获取热门代币: {url} params={params}")
            
            response = requests.get(
                url,
                params=params,
                timeout=10,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    # 处理每个交易对数据
                    hot_tokens = []
                    seen_tokens = set()  # 用于去重
                    
                    for pair in data['pairs']:
                        token_address = pair['baseToken']['address']
                        if token_address not in seen_tokens:
                            seen_tokens.add(token_address)
                            processed_data = self._process_token_data({'pairs': [pair]})
                            if processed_data:
                                # 添加额外的热度指标
                                processed_data['heat_score'] = self._calculate_heat_score(pair)
                                hot_tokens.append(processed_data)
                    
                    # 按热度分数排序
                    hot_tokens.sort(key=lambda x: x['heat_score'], reverse=True)
                    return hot_tokens[:limit]
                    
            # 如果上面的方法失败，尝试使用另一个端点
            url = f"{self.base_url}/pairs/{chain}"  # 使用 pairs 端点
            params = {
                'sort_by': 'volume',
                'sort_order': 'desc',
                'limit': limit * 2  # 获取更多数据以便过滤
            }
            
            logging.info(f"尝试备用方法获取热门代币: {url} params={params}")
            
            response = requests.get(
                url,
                params=params,
                timeout=10,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    hot_tokens = []
                    seen_tokens = set()
                    
                    for pair in data['pairs']:
                        token_address = pair['baseToken']['address']
                        if token_address not in seen_tokens:
                            seen_tokens.add(token_address)
                            processed_data = self._process_token_data({'pairs': [pair]})
                            if processed_data:
                                hot_tokens.append(processed_data)
                    
                    # 按24h成交量排序
                    hot_tokens.sort(key=lambda x: x['volume24h'], reverse=True)
                    return hot_tokens[:limit]
                    
            logging.warning(f"获取热门代币失败: {response.status_code}")
            return []
            
        except Exception as e:
            logging.error(f"获取热门代币时出错: {e}")
            return []

    def _calculate_heat_score(self, pair: Dict[str, Any]) -> float:
        """计算代币热度分数"""
        try:
            volume_24h = float(pair.get('volume', {}).get('h24', 0) or 0)
            liquidity_usd = float(pair.get('liquidity', {}).get('usd', 0) or 0)
            price_change_24h = float(pair.get('priceChange', {}).get('h24', 0) or 0)
            txns_24h = pair.get('txns', {}).get('h24', {})
            buys = int(txns_24h.get('buys', 0))
            sells = int(txns_24h.get('sells', 0))
            
            # 计算各个指标的权重
            volume_score = min(volume_24h / 100000, 100)  # 成交量得分
            liquidity_score = min(liquidity_usd / 100000, 100)  # 流动性得分
            price_score = min(abs(price_change_24h) / 10, 100)  # 价格变化得分
            tx_score = min((buys + sells) / 100, 100)  # 交易次数得分
            
            # 计算综合得分
            heat_score = (
                volume_score * 0.4 +    # 成交量权重 40%
                liquidity_score * 0.3 + # 流动性权重 30%
                price_score * 0.2 +     # 价格变化权重 20%
                tx_score * 0.1          # 交易次数权重 10%
            )
            
            return heat_score
            
        except Exception as e:
            logging.error(f"计算热度分数时出错: {e}")
            return 0
            
    def _process_token_data(self, data: Dict) -> Dict[str, Any]:
        """处理API返回的原始数据"""
        pairs = sorted(
            data['pairs'],
            key=lambda x: float(x.get('volume', {}).get('h24', 0) or 0),
            reverse=True
        )
        pair = pairs[0]
        
        # 添加对 Solana 特有字段的处理
        chain_id = pair.get('chainId', 'Unknown')
        dex_id = pair.get('dexId', 'Unknown')
        
        # Solana 上的主要 DEX
        if chain_id == 'solana':
            if dex_id == 'raydium':
                dex_name = 'Raydium'
            elif dex_id == 'orca':
                dex_name = 'Orca'
            else:
                dex_name = dex_id.capitalize()
        else:
            dex_name = dex_id
        
        return {
            'price': float(pair.get('priceUsd', 0)),
            'volume24h': float(pair.get('volume', {}).get('h24', 0)),
            'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
            'priceChange24h': float(pair.get('priceChange', {}).get('h24', 0)),
            'pairs': pairs,
            'baseToken': pair.get('baseToken', {}),
            'txns': pair.get('txns', {}).get('h24', {}),
            'dex': dex_name,
            'chain': chain_id
        } 