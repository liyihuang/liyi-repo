# 周期股研究

这个目录最初从猪周期和牧原股份研究开始，后来扩展到 A 股主要周期行业的通用规律验证。

## 目录结构

```text
00_通用周期框架/
  周期股龙头与二线规律备忘.md
  交易心理与市场微观结构.md

10_猪周期与牧原/
  牧原交易计划.md
  牧原投资分析.md
  周期钝化情景分析.md
  猪股分析框架.md
  猪肉股历史弹性对比验证.md
  二线猪企与牧原价格一致性及弹性对比.md

20_数据验证/
  scripts/
    verify_all_cycles.py
    verify_cross_industry_cycles.py
    verify_profit_threshold_effect.py
  reports/
    pig_cycle_node_comparison.md
    cross_industry_cycle_node_comparison.md
    profit_threshold_effect.md
  data/
    stock_prices/
    financials/

90_草稿脚本/
  临时拉数和 akshare 测试脚本
```

## 核心阅读顺序

1. `00_通用周期框架/周期股龙头与二线规律备忘.md`
2. `10_猪周期与牧原/牧原交易计划.md`
3. `10_猪周期与牧原/周期钝化情景分析.md`
4. `20_数据验证/reports/cross_industry_cycle_node_comparison.md`
5. `20_数据验证/reports/profit_threshold_effect.md`

## 当前核心结论

- 顶部同步是相对最稳定的周期规律，但前提是同一价格锚。
- 二线 beta 更大不是铁律，真正高弹性来自“能活下来的边际产能”。
- 二线见底晚于龙头不是铁律，底部更多是风险定价。
- 边际成本位置是二线弹性的第一因子，但必须和生存能力一起看。

## 验证脚本

在项目根目录运行：

```bash
python3 20_数据验证/scripts/verify_all_cycles.py
python3 20_数据验证/scripts/verify_cross_industry_cycles.py
python3 20_数据验证/scripts/verify_profit_threshold_effect.py
```

脚本会复用 `20_数据验证/data/` 下的缓存，并把结果写入 `20_数据验证/reports/`。
