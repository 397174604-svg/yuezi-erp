// 登录页演示账号搜索过滤（纯函数，可测；Login.vue import 它，避免 computed 内联逻辑无测漂移）。
// 规则：关键词命中「角色名」→ 整组保留；否则按「姓名/手机号」过滤该组；空组丢弃；空关键词→原样返回。大小写不敏感。
export interface Acct { name?: string; phone?: string; [k: string]: unknown }
export interface Group { role: string; list: Acct[] }

export function filterAccountGroups(groups: Group[], kw: string): Group[] {
  const k = (kw || '').trim().toLowerCase();
  if (!k) return groups;
  return groups
    .map((g) => ({
      role: g.role,
      list: g.role.toLowerCase().includes(k)
        ? g.list
        : g.list.filter((d) => String(d.name || '').toLowerCase().includes(k) || String(d.phone || '').includes(k)),
    }))
    .filter((g) => g.list.length);
}
