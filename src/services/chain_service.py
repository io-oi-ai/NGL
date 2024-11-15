from typing import Dict, List, Optional
from enum import Enum

class Chain(Enum):
    ETH = ('ethereum', 'Ethereum')
    BSC = ('bsc', 'BNB Chain')
    POLYGON = ('polygon', 'Polygon')
    ARBITRUM = ('arbitrum', 'Arbitrum')
    BASE = ('base', 'Base')
    SOL = ('solana', 'Solana')
    
    def __init__(self, chain_id: str, display_name: str):
        self._chain_id = chain_id
        self._display_name = display_name
    
    @property
    def chain_id(self) -> str:
        return self._chain_id
        
    @property
    def display_name(self) -> str:
        return self._display_name

class ChainService:
    def __init__(self):
        self.chains = {chain.chain_id: chain for chain in Chain}
        
    def get_chain_name(self, chain_id: str) -> str:
        """获取链的显示名称"""
        return self.chains[chain_id].display_name if chain_id in self.chains else chain_id
        
    def is_valid_chain(self, chain_id: str) -> bool:
        """验证链ID是否有效"""
        return chain_id in self.chains
        
    def get_all_chains(self) -> List[Dict[str, str]]:
        """获取所有支持的链信息"""
        return [{'id': chain.chain_id, 'name': chain.display_name} for chain in Chain]
        
    def is_solana_address(self, address: str) -> bool:
        """验证是否为 Solana 地址"""
        return len(address) == 44 or len(address) == 32  # Solana 地址通常是 32/44 字节的 base58 编码