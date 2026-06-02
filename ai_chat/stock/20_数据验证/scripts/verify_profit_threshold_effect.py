from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import akshare as ak
import pandas as pd
from verify_cross_industry_cycles import CYCLES as CROSS_CYCLES
from verify_cross_industry_cycles import STOCKS as CROSS_STOCKS


@dataclass(frozen=True)
class Stock:
    industry: str
    name: str
    code: str
    tier: str


@dataclass(frozen=True)
class Cycle:
    industry: str
    name: str
    reference_stock: str
    bottom_start: str
    bottom_end: str
    top_start: str
    top_end: str


PIG_STOCKS = [
    Stock("猪股", "牧原股份", "002714", "龙头"),
    Stock("猪股", "温氏股份", "300498", "1.5线"),
    Stock("猪股", "巨星农牧", "603477", "二线"),
    Stock("猪股", "华统股份", "002840", "二线"),
    Stock("猪股", "神农集团", "605296", "二线"),
    Stock("猪股", "唐人神", "002567", "二线"),
]

PIG_CYCLES = [
    Cycle("猪股", "猪股 2021-2022", "牧原股份", "2021-08-01", "2022-05-01", "2022-05-01", "2022-11-30"),
    Cycle("猪股", "猪股 2023-2024", "牧原股份", "2023-08-01", "2024-03-15", "2024-03-15", "2024-11-30"),
]

STOCKS = [
    Stock(stock.industry, stock.name, stock.code, stock.tier)
    for stock in CROSS_STOCKS
] + PIG_STOCKS

CYCLES = [
    Cycle(cycle.industry, cycle.name, cycle.reference_stock, cycle.bottom_start, cycle.bottom_end, cycle.top_start, cycle.top_end)
    for cycle in CROSS_CYCLES
] + PIG_CYCLES

VERIFY_DIR = Path(__file__).resolve().parents[1]
CACHE_PRICE_DIR = VERIFY_DIR / "data" / "stock_prices"
CACHE_FINANCIAL_DIR = VERIFY_DIR / "data" / "financials"
REPORT_DIR = VERIFY_DIR / "reports"
LOW_MARGIN_THRESHOLD = 0.02


def market_symbol(code: str) -> str:
    return f"{'SH' if code.startswith('6') else 'SZ'}{code}"


def price_cache_path(code: str, start_date: str, end_date: str) -> Path:
    return CACHE_PRICE_DIR / f"{code}_{start_date}_{end_date}_qfq.csv"


def fetch_price(stock: Stock, start_date: str, end_date: str) -> pd.DataFrame:
    path = price_cache_path(stock.code, start_date, end_date)
    if path.exists():
        df = pd.read_csv(path, parse_dates=["日期"])
        df.set_index("日期", inplace=True)
        return df

    CACHE_PRICE_DIR.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            print(f"Fetching price {stock.name} ({stock.code}) via sina attempt {attempt}...")
            df = ak.stock_zh_a_daily(
                symbol=market_symbol(stock.code).lower(),
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            if df.empty:
                raise RuntimeError("empty dataframe")
            df = df.rename(columns={"date": "日期", "close": "收盘"})
            df["日期"] = pd.to_datetime(df["日期"])
            df["收盘"] = pd.to_numeric(df["收盘"])
            df.set_index("日期", inplace=True)
            df.sort_index(inplace=True)
            df.to_csv(path)
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"  Error: {exc}")
            time.sleep(2)

    raise RuntimeError(f"failed to fetch price for {stock.name}: {last_error}")


def fetch_quarterly_profit(stock: Stock) -> pd.DataFrame:
    CACHE_FINANCIAL_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_FINANCIAL_DIR / f"{stock.code}_quarterly_profit.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["REPORT_DATE"])

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            print(f"Fetching quarterly profit {stock.name} ({stock.code}) attempt {attempt}...")
            df = ak.stock_profit_sheet_by_quarterly_em(symbol=market_symbol(stock.code))
            if df.empty:
                raise RuntimeError("empty dataframe")
            df.to_csv(path, index=False)
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"  Error: {exc}")
            time.sleep(2)

    raise RuntimeError(f"failed to fetch financials for {stock.name}: {last_error}")


def analyze_price(df: pd.DataFrame, cycle: Cycle) -> dict[str, object]:
    bottom = df.loc[cycle.bottom_start : cycle.bottom_end]
    top = df.loc[cycle.top_start : cycle.top_end]
    if bottom.empty or top.empty:
        raise RuntimeError(f"empty price window for {cycle.name}")

    bottom_date = bottom["收盘"].idxmin()
    top_date = top["收盘"].idxmax()
    bottom_close = float(bottom.loc[bottom_date, "收盘"])
    top_close = float(top.loc[top_date, "收盘"])
    return {
        "低点日期": bottom_date,
        "高点日期": top_date,
        "涨幅": (top_close / bottom_close - 1) * 100,
    }


def quarter_end_for(date: pd.Timestamp) -> pd.Timestamp:
    month = ((date.month - 1) // 3 + 1) * 3
    return pd.Timestamp(year=date.year, month=month, day=1) + pd.offsets.MonthEnd(0)


def financial_at_top(financials: pd.DataFrame, top_date: pd.Timestamp) -> dict[str, object]:
    df = financials.copy()
    df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"])
    df["NOTICE_DATE"] = pd.to_datetime(df["NOTICE_DATE"], errors="coerce")
    df = df[(df["REPORT_DATE"] <= quarter_end_for(top_date)) & (df["NOTICE_DATE"].notna()) & (df["NOTICE_DATE"] <= top_date)]
    df = df.sort_values(["REPORT_DATE", "NOTICE_DATE"])
    if df.empty:
        return {
            "财报期": pd.NaT,
            "归母净利": pd.NA,
            "收入": pd.NA,
            "净利率": pd.NA,
            "盈利状态": "无数据",
        }

    row = df.iloc[-1]
    income = pd.to_numeric(row.get("TOTAL_OPERATE_INCOME"), errors="coerce")
    profit = pd.to_numeric(row.get("PARENT_NETPROFIT"), errors="coerce")
    margin = profit / income if pd.notna(profit) and pd.notna(income) and income != 0 else pd.NA

    if pd.isna(profit):
        status = "无数据"
    elif profit <= 0:
        status = "亏损"
    elif pd.notna(margin) and margin < LOW_MARGIN_THRESHOLD:
        status = "微利"
    else:
        status = "盈利"

    return {
        "财报期": row["REPORT_DATE"],
        "归母净利": profit,
        "收入": income,
        "净利率": margin,
        "盈利状态": status,
    }


def build_table(cycle: Cycle, price_start: str, price_end: str) -> pd.DataFrame:
    stocks = [stock for stock in STOCKS if stock.industry == cycle.industry]
    rows = []
    for stock in stocks:
        price = analyze_price(fetch_price(stock, price_start, price_end), cycle)
        financial = financial_at_top(fetch_quarterly_profit(stock), price["高点日期"])
        rows.append({"行业": stock.industry, "公司": stock.name, "层级": stock.tier, **price, **financial})

    table = pd.DataFrame(rows)
    ref = table[table["公司"] == cycle.reference_stock].iloc[0]
    ref_gain = float(ref["涨幅"])
    table["相对基准涨幅差"] = table["涨幅"].apply(lambda value: float(value) - ref_gain)
    table["是否跑赢基准"] = table["相对基准涨幅差"].apply(lambda value: "是" if float(value) > 0 else "否")
    table["低盈利且跑输"] = table.apply(
        lambda row: row["公司"] != cycle.reference_stock and row["盈利状态"] in {"亏损", "微利"} and row["是否跑赢基准"] == "否",
        axis=1,
    )
    return table


def format_table(table: pd.DataFrame) -> pd.DataFrame:
    formatted = table.copy()
    for column in ["低点日期", "高点日期", "财报期"]:
        formatted[column] = formatted[column].apply(lambda value: "" if pd.isna(value) else value.strftime("%Y-%m-%d"))
    for column in ["涨幅", "相对基准涨幅差"]:
        formatted[column] = formatted[column].apply(lambda value: "" if pd.isna(value) else f"{float(value):.1f}")
    formatted["归母净利"] = formatted["归母净利"].apply(
        lambda value: "" if pd.isna(value) else f"{float(value) / 100000000:.2f}亿"
    )
    formatted["收入"] = formatted["收入"].apply(lambda value: "" if pd.isna(value) else f"{float(value) / 100000000:.2f}亿")
    formatted["净利率"] = formatted["净利率"].apply(lambda value: "" if pd.isna(value) else f"{float(value) * 100:.1f}%")
    formatted["低盈利且跑输"] = formatted["低盈利且跑输"].apply(lambda value: "是" if value else "否")
    return formatted


def build_summary(cycle_tables: list[tuple[Cycle, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for cycle, table in cycle_tables:
        ref = table[table["公司"] == cycle.reference_stock].iloc[0]
        non_ref = table[table["公司"] != cycle.reference_stock]
        low = non_ref[non_ref["盈利状态"].isin({"亏损", "微利"})]
        low_underperform = low[low["是否跑赢基准"] == "否"]
        matched = ref["盈利状态"] == "盈利" and len(low) > 0
        rows.append(
            {
                "周期": cycle.name,
                "基准": cycle.reference_stock,
                "基准盈利状态": ref["盈利状态"],
                "低盈利非基准样本": len(low),
                "低盈利且跑输": f"{len(low_underperform)}/{len(low)}" if len(low) else "无样本",
                "符合命题场景": "是" if matched else "否",
            }
        )
    return pd.DataFrame(rows)


def write_report(cycle_tables: list[tuple[Cycle, pd.DataFrame]]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "profit_threshold_effect.md"

    lines = [
        "# 龙头盈利区间与二线收益验证",
        "",
        f"口径：股价为前复权收盘价；财务为股价高点所在季度或之前最近单季度利润表；微利阈值为净利率低于 {LOW_MARGIN_THRESHOLD:.0%}。",
        "",
        "验证问题：当周期价格只足以让龙头舒服盈利、非龙头亏损或微利时，非龙头是否更容易跑输。",
        "",
    ]
    summary = build_summary(cycle_tables)
    lines.extend(["## 摘要", "", summary.to_markdown(index=False), ""])

    for cycle, table in cycle_tables:
        non_ref = table[table["公司"] != cycle.reference_stock]
        weak = non_ref[non_ref["盈利状态"].isin({"亏损", "微利"})]
        weak_underperform = weak[weak["是否跑赢基准"] == "否"]
        lines.extend(
            [
                f"## {cycle.name}",
                "",
                f"- 基准：{cycle.reference_stock}",
                f"- 低盈利非基准样本：{len(weak)}",
                f"- 低盈利且跑输基准：{len(weak_underperform)}/{len(weak)}" if len(weak) else "- 低盈利且跑输基准：无样本",
                "",
                format_table(table).to_markdown(index=False),
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    price_start = "20200301"
    price_end = "20241130"
    cycle_tables = []
    for cycle in CYCLES:
        table = build_table(cycle, price_start, price_end)
        cycle_tables.append((cycle, table))
        print(f"\n=== {cycle.name} ===")
        print(format_table(table).to_string(index=False))

    report = write_report(cycle_tables)
    print(f"\nReport written: {report}")


if __name__ == "__main__":
    main()
