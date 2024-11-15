import React, { useState } from 'react';
import { getTokenInfo } from '../services/tokenService';

interface TokenInfo {
  name: string;
  symbol: string;
  price: number;
}

export function TokenLookup() {
  const [address, setAddress] = useState('');
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const info = await getTokenInfo(address);
    setTokenInfo(info);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="输入CA地址"
        />
        <button type="submit">查询</button>
      </form>
      {tokenInfo && (
        <div>
          <h3>{tokenInfo.name}</h3>
          <p>符号: {tokenInfo.symbol}</p>
          <p>价格: {tokenInfo.price}</p>
          {/* ... 显示其他token信息 */}
        </div>
      )}
    </div>
  );
}