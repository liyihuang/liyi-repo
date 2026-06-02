from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import akshare as ak
import pandas as pd


@dataclass(frozen=True)
class Stock:
    industry: str
    name: str
    code: str
    tier: str
    note: str = ""


@dataclass(frozen=True)
class Cycle:
    industry: str
    name: str
    reference_stock: str
    bottom_start: str
    bottom_end: str
    top_start: str
    top_end: str
    note: str = ""


STOCKS = [
    Stock("钢铁", "宝钢股份", "600019", "龙头", "板材龙头，盈利质量和分红属性较强"),
    Stock("钢铁", "华菱钢铁", "000932", "二线/区域龙头", "盈利弹性较强，区域和产品结构影响大"),
    Stock("钢铁", "方大特钢", "600507", "二线", "长材/特钢样本，分红属性较强"),
    Stock("钢铁", "新钢股份", "600782", "二线", "普钢弹性样本"),
    Stock("钢铁", "重庆钢铁", "601005", "困境弹性", "重整后困境反转属性强"),
    Stock("钢铁", "安阳钢铁", "600569", "困境弹性", "高弹性但经营质量和区域扰动较大"),
    Stock("有色", "紫金矿业", "601899", "龙头", "金铜龙头，全球矿山 alpha 明显"),
    Stock("有色", "江西铜业", "600362", "龙头", "铜冶炼和铜资源，周期敞口较纯"),
    Stock("有色", "中国铝业", "601600", "龙头", "铝行业龙头，政策和央企属性明显"),
    Stock("有色", "云铝股份", "000807", "二线", "电解铝弹性样本，水电铝属性"),
    Stock("有色", "神火股份", "000933", "二线", "煤铝双周期，弹性较强"),
    Stock("有色", "洛阳钼业", "603993", "二线/多金属", "铜钴钼多金属，海外资产 alpha 明显"),
    Stock("煤炭", "中国神华", "601088", "龙头", "煤炭高分红龙头，防御属性强"),
    Stock("煤炭", "陕西煤业", "601225", "龙头", "煤炭高质量龙头"),
    Stock("煤炭", "兖矿能源", "600188", "弹性龙头", "澳洲资产和煤化工影响较大"),
    Stock("煤炭", "山煤国际", "600546", "二线", "煤炭弹性样本"),
    Stock("煤炭", "平煤股份", "601666", "二线", "焦煤弹性样本"),
    Stock("煤炭", "潞安环能", "601699", "二线", "煤炭弹性样本"),
    Stock("化工", "万华化学", "600309", "龙头", "MDI 龙头，成长 alpha 和周期 beta 并存"),
    Stock("化工", "华鲁恒升", "600426", "龙头", "煤化工龙头，成本和管理 alpha 强"),
    Stock("化工", "鲁西化工", "000830", "二线", "综合化工弹性样本"),
    Stock("化工", "卫星化学", "002648", "二线/成长", "轻烃化工，成长和周期混合"),
    Stock("化工", "桐昆股份", "601233", "二线", "涤纶长丝周期样本"),
    Stock("化工", "恒力石化", "600346", "龙头/炼化", "大炼化龙头，成长扩产 alpha 强"),
    Stock("航运", "中远海控", "601919", "龙头", "集运超级周期核心标的"),
    Stock("航运", "招商轮船", "601872", "龙头/油运", "油运和散运敞口，子行业差异大"),
    Stock("航运", "中远海能", "600026", "二线/油运", "油运周期，与集运节奏不同"),
    Stock("航运", "中远海特", "600428", "二线", "特种船运输，弹性和主题属性较强"),
    Stock("航运", "宁波海运", "600798", "小盘弹性", "区域航运小盘弹性样本"),
    Stock("面板", "京东方A", "000725", "龙头", "面板绝对龙头，规模和估值锚明显"),
    Stock("面板", "TCL科技", "000100", "龙头", "面板龙头，半导体显示和新能源材料混合"),
    Stock("面板", "深天马A", "000050", "二线", "中小尺寸面板，弹性较弱"),
    Stock("面板", "彩虹股份", "600707", "二线弹性", "面板玻璃/显示，2020-2021 弹性极强"),
    Stock("面板", "维信诺", "002387", "二线", "OLED 样本，盈利质量扰动较大"),
    Stock("水泥建材", "海螺水泥", "600585", "龙头", "水泥龙头，质量和分红属性强"),
    Stock("水泥建材", "华新水泥", "600801", "龙头", "区域水泥龙头"),
    Stock("水泥建材", "冀东水泥", "000401", "二线", "北方水泥弹性样本"),
    Stock("水泥建材", "上峰水泥", "000672", "二线", "区域水泥弹性样本"),
    Stock("水泥建材", "塔牌集团", "002233", "二线", "华南区域水泥样本"),
    Stock("水泥建材", "万年青", "000789", "二线", "区域水泥弹性样本"),
    Stock("造纸", "太阳纸业", "002078", "龙头", "纸业龙头，成长和成本 alpha 较强"),
    Stock("造纸", "晨鸣纸业", "000488", "二线", "高负债纸业弹性样本"),
    Stock("造纸", "博汇纸业", "600966", "二线", "白卡纸弹性样本"),
    Stock("造纸", "山鹰国际", "600567", "二线", "包装纸周期样本，信用压力较高"),
    Stock("造纸", "岳阳林纸", "600963", "二线/主题", "纸业和碳汇主题混合"),
    Stock("航空", "中国国航", "601111", "龙头", "航空龙头，油价汇率和国际线影响大"),
    Stock("航空", "南方航空", "600029", "龙头", "航空龙头，机队规模大"),
    Stock("航空", "春秋航空", "601021", "优质龙头", "低成本航空，经营 alpha 强"),
    Stock("航空", "吉祥航空", "603885", "二线", "民营航空弹性样本"),
    Stock("航空", "华夏航空", "002928", "二线", "支线航空，个股经营 alpha 强"),
    Stock("锂", "赣锋锂业", "002460", "龙头", "锂盐龙头，港股/全球资产影响"),
    Stock("锂", "天齐锂业", "002466", "龙头", "锂盐龙头，债务修复曾是重要 alpha"),
    Stock("锂", "盛新锂能", "002240", "二线", "锂盐二线弹性样本"),
    Stock("锂", "融捷股份", "002192", "二线", "小市值锂矿弹性样本"),
    Stock("锂", "永兴材料", "002756", "二线", "锂电+特钢，非锂业务稀释"),
    Stock("锂", "江特电机", "002176", "困境弹性", "困境反转/高弹性，个股 alpha 很强"),
]

CYCLES = [
    Cycle(
        industry="钢铁",
        name="钢铁 2020-2021",
        reference_stock="宝钢股份",
        bottom_start="2020-03-01",
        bottom_end="2020-06-30",
        top_start="2021-05-01",
        top_end="2021-09-30",
        note="疫情后需求修复、钢价上行和限产预期共振；宝钢股份作为质量龙头基准",
    ),
    Cycle(
        industry="有色",
        name="有色 2020-2021",
        reference_stock="紫金矿业",
        bottom_start="2020-03-01",
        bottom_end="2020-06-30",
        top_start="2021-02-01",
        top_end="2021-09-30",
        note="全球复苏、铜铝价格上行和资源股重估；紫金矿业作为资源龙头基准",
    ),
    Cycle(
        industry="煤炭",
        name="煤炭 2020-2022",
        reference_stock="中国神华",
        bottom_start="2020-03-01",
        bottom_end="2021-02-28",
        top_start="2022-06-01",
        top_end="2022-09-30",
        note="煤价上行和煤炭股重估波段；中国神华作为防御型龙头基准",
    ),
    Cycle(
        industry="化工",
        name="化工 2020-2021",
        reference_stock="万华化学",
        bottom_start="2020-03-01",
        bottom_end="2020-06-30",
        top_start="2021-01-01",
        top_end="2021-09-30",
        note="疫情后补库存、油化煤化价格上行；万华化学作为高质量龙头基准",
    ),
    Cycle(
        industry="航运",
        name="航运 2020-2021",
        reference_stock="中远海控",
        bottom_start="2020-03-01",
        bottom_end="2020-09-30",
        top_start="2021-06-01",
        top_end="2021-12-31",
        note="集运超级周期；航运内部集运、油运、特运差异很大",
    ),
    Cycle(
        industry="面板",
        name="面板 2020-2021",
        reference_stock="京东方A",
        bottom_start="2020-03-01",
        bottom_end="2020-06-30",
        top_start="2021-01-01",
        top_end="2021-07-31",
        note="面板价格上行周期；京东方A作为面板龙头基准",
    ),
    Cycle(
        industry="水泥建材",
        name="水泥建材 2020-2021",
        reference_stock="海螺水泥",
        bottom_start="2020-03-01",
        bottom_end="2020-06-30",
        top_start="2020-07-01",
        top_end="2021-12-31",
        note="地产和基建链周期波动；水泥更多受区域和地产预期影响",
    ),
    Cycle(
        industry="造纸",
        name="造纸 2020-2021",
        reference_stock="太阳纸业",
        bottom_start="2020-03-01",
        bottom_end="2020-06-30",
        top_start="2020-12-01",
        top_end="2021-06-30",
        note="纸价上行和补库存周期；太阳纸业作为质量龙头基准",
    ),
    Cycle(
        industry="航空",
        name="航空 2020-2021",
        reference_stock="中国国航",
        bottom_start="2020-03-01",
        bottom_end="2020-10-31",
        top_start="2021-02-01",
        top_end="2021-12-31",
        note="疫情后修复预期波段；航空受油价、汇率、疫情政策影响，和商品周期不同",
    ),
    Cycle(
        industry="锂",
        name="锂 2020-2021",
        reference_stock="赣锋锂业",
        bottom_start="2020-03-01",
        bottom_end="2020-12-31",
        top_start="2021-08-01",
        top_end="2021-12-31",
        note="新能源需求爆发下的锂价上行第一波；赣锋锂业作为龙头基准",
    ),
    Cycle(
        industry="锂",
        name="锂 2022反弹",
        reference_stock="赣锋锂业",
        bottom_start="2022-03-01",
        bottom_end="2022-05-15",
        top_start="2022-06-01",
        top_end="2022-09-30",
        note="锂股 2022 年中反弹波段，观察第二轮顶部是否更分化",
    ),
]

VERIFY_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = VERIFY_DIR / "data" / "stock_prices"
REPORT_DIR = VERIFY_DIR / "reports"


def market_symbol(code: str) -> str:
    return f"{'sh' if code.startswith('6') else 'sz'}{code}"


def fetch_from_eastmoney(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    return ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )


def fetch_from_tencent(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    return ak.stock_zh_a_hist_tx(
        symbol=market_symbol(code),
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )


def fetch_from_sina(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    return ak.stock_zh_a_daily(
        symbol=market_symbol(code),
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )


def normalize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "date": "日期",
        "日期": "日期",
        "close": "收盘",
        "收盘": "收盘",
    }
    df = df.rename(columns={column: rename_map[column] for column in df.columns if column in rename_map})
    if "日期" not in df.columns or "收盘" not in df.columns:
        raise RuntimeError(f"unexpected columns: {list(df.columns)}")

    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"])
    df["收盘"] = pd.to_numeric(df["收盘"])
    df.set_index("日期", inplace=True)
    df.sort_index(inplace=True)
    return df


def fetch_stock(stock: Stock, start_date: str, end_date: str) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{stock.code}_{start_date}_{end_date}_qfq.csv"
    if cache_path.exists():
        df = pd.read_csv(cache_path, parse_dates=["日期"])
        df.set_index("日期", inplace=True)
        return df

    providers = [
        ("sina", fetch_from_sina),
        ("eastmoney", fetch_from_eastmoney),
        ("tencent", fetch_from_tencent),
    ]
    errors = []
    for provider_name, provider in providers:
        for attempt in range(1, 4):
            try:
                print(f"Fetching {stock.name} ({stock.code}) via {provider_name} attempt {attempt}...")
                df = normalize_price_frame(provider(stock.code, start_date, end_date))
                if df.empty:
                    raise RuntimeError("empty dataframe")
                df.to_csv(cache_path)
                return df
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider_name} attempt {attempt}: {exc}")
                print(f"  Error: {exc}")
                time.sleep(2)

    raise RuntimeError(f"failed to fetch {stock.name} ({stock.code}): {' | '.join(errors)}")


def analyze_cycle(df: pd.DataFrame, cycle: Cycle) -> dict[str, object] | None:
    bottom_data = df.loc[cycle.bottom_start : cycle.bottom_end]
    top_data = df.loc[cycle.top_start : cycle.top_end]
    if bottom_data.empty or top_data.empty:
        return None

    bottom_date = bottom_data["收盘"].idxmin()
    bottom_close = float(bottom_data.loc[bottom_date, "收盘"])
    top_date = top_data["收盘"].idxmax()
    top_close = float(top_data.loc[top_date, "收盘"])
    return {
        "低点日期": bottom_date,
        "低点价": bottom_close,
        "高点日期": top_date,
        "高点价": top_close,
        "涨幅": (top_close / bottom_close - 1) * 100,
    }


def build_cycle_table(price_data: dict[str, pd.DataFrame], cycle: Cycle) -> pd.DataFrame:
    rows = []
    stocks = [stock for stock in STOCKS if stock.industry == cycle.industry]
    for stock in stocks:
        result = analyze_cycle(price_data[stock.name], cycle)
        rows.append(
            {
                "行业": stock.industry,
                "公司": stock.name,
                "层级": stock.tier,
                **(
                    result
                    if result is not None
                    else {
                        "低点日期": pd.NaT,
                        "低点价": pd.NA,
                        "高点日期": pd.NaT,
                        "高点价": pd.NA,
                        "涨幅": pd.NA,
                    }
                ),
                "备注": stock.note,
            }
        )

    table = pd.DataFrame(rows)
    reference = table[table["公司"] == cycle.reference_stock]
    if reference.empty or pd.isna(reference.iloc[0]["涨幅"]):
        raise RuntimeError(f"reference stock {cycle.reference_stock} is missing in {cycle.name}")

    reference_row = reference.iloc[0]
    reference_bottom = reference_row["低点日期"]
    reference_top = reference_row["高点日期"]
    reference_gain = float(reference_row["涨幅"])

    table["相对基准低点天数"] = table["低点日期"].apply(
        lambda value: pd.NA if pd.isna(value) else (value - reference_bottom).days
    )
    table["相对基准高点天数"] = table["高点日期"].apply(
        lambda value: pd.NA if pd.isna(value) else (value - reference_top).days
    )
    table["相对基准涨幅差"] = table["涨幅"].apply(
        lambda value: pd.NA if pd.isna(value) else float(value) - reference_gain
    )
    table["是否跑赢基准"] = table["相对基准涨幅差"].apply(
        lambda value: pd.NA if pd.isna(value) else ("是" if float(value) > 0 else "否")
    )
    return table


def format_table(table: pd.DataFrame) -> pd.DataFrame:
    formatted = table.copy()
    for column in ["低点日期", "高点日期"]:
        formatted[column] = formatted[column].apply(
            lambda value: "" if pd.isna(value) else value.strftime("%Y-%m-%d")
        )
    for column in ["低点价", "高点价", "涨幅", "相对基准涨幅差"]:
        formatted[column] = formatted[column].apply(
            lambda value: "" if pd.isna(value) else f"{float(value):.1f}"
        )
    for column in ["相对基准低点天数", "相对基准高点天数"]:
        formatted[column] = formatted[column].apply(
            lambda value: "" if pd.isna(value) else f"{int(value):+d}"
        )
    return formatted


def build_summary_table(cycle_tables: list[tuple[Cycle, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for cycle, table in cycle_tables:
        valid = table.dropna(subset=["低点日期", "高点日期", "涨幅"]).copy()
        if valid.empty:
            continue

        non_reference = valid[valid["公司"] != cycle.reference_stock]
        top_span = (valid["高点日期"].max() - valid["高点日期"].min()).days
        bottom_span = (valid["低点日期"].max() - valid["低点日期"].min()).days
        outperform_count = int((non_reference["是否跑赢基准"] == "是").sum())
        sample_count = len(non_reference)
        median_top_abs_days = non_reference["相对基准高点天数"].apply(lambda value: abs(int(value))).median()

        rows.append(
            {
                "周期": cycle.name,
                "基准": cycle.reference_stock,
                "样本数": len(valid),
                "低点跨度(天)": bottom_span,
                "高点跨度(天)": top_span,
                "非基准跑赢数": f"{outperform_count}/{sample_count}",
                "非基准高点偏离中位数(天)": int(median_top_abs_days) if not pd.isna(median_top_abs_days) else pd.NA,
            }
        )
    return pd.DataFrame(rows)


def write_markdown_report(cycle_tables: list[tuple[Cycle, pd.DataFrame]]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "cross_industry_cycle_node_comparison.md"

    lines = [
        "# 跨行业周期节点对比",
        "",
        "口径：前复权日收盘价；在预先配置的行业周期窗口内，事后寻找各股票低点和高点。",
        "这份输出用于观察“顶部是否行业共振、二线弹性是否普遍存在”，不直接代表可交易信号。",
        "",
    ]

    summary = build_summary_table(cycle_tables)
    if not summary.empty:
        lines.extend(
            [
                "## 摘要",
                "",
                summary.to_markdown(index=False),
                "",
            ]
        )

    for cycle, table in cycle_tables:
        lines.extend(
            [
                f"## {cycle.name}",
                "",
                f"- 基准：{cycle.reference_stock}",
                f"- 找底窗口：{cycle.bottom_start} 至 {cycle.bottom_end}",
                f"- 找顶窗口：{cycle.top_start} 至 {cycle.top_end}",
                f"- 备注：{cycle.note}",
                "",
                format_table(table).to_markdown(index=False),
                "",
            ]
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    start_date = min(cycle.bottom_start for cycle in CYCLES).replace("-", "")
    end_date = max(cycle.top_end for cycle in CYCLES).replace("-", "")
    stocks = sorted({stock.name: stock for stock in STOCKS}.values(), key=lambda stock: stock.code)
    price_data = {stock.name: fetch_stock(stock, start_date, end_date) for stock in stocks}

    cycle_tables = []
    for cycle in CYCLES:
        table = build_cycle_table(price_data, cycle)
        cycle_tables.append((cycle, table))
        print(f"\n=== {cycle.name} ===")
        print(format_table(table).to_string(index=False))

    report_path = write_markdown_report(cycle_tables)
    print(f"\nReport written: {report_path}")


if __name__ == "__main__":
    main()
