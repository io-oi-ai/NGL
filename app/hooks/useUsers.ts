import { useState, useEffect } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  // 添加其他需要的用户属性
}

export function useUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchUsers() {
      try {
        // 这里应该是从API或数据库获取用户数据的逻辑
        // 现在我们只是模拟一些数据
        const response = await new Promise<User[]>((resolve) => {
          setTimeout(() => {
            resolve([
              { id: 1, username: '用户1', email: 'user1@example.com' },
              { id: 2, username: '用户2', email: 'user2@example.com' },
              // 添加更多模拟用户数据
            ]);
          }, 1000);
        });
        setUsers(response);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('An error occurred'));
        setLoading(false);
      }
    }

    fetchUsers();
  }, []);

  return { users, loading, error };
}