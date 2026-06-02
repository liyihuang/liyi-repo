from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import akshare as ak
import pandas as pd


@dataclass(frozen=True)
class Stock:
    name: str
    code: str
    tier: str
    note: str = ""


@dataclass(frozen=True)
class Cycle:
    name: str
    bottom_start: str
    bottom_end: str
    top_start: str
    top_end: str
    note: str = ""


STOCKS = [
    Stock("牧原股份", "002714", "一线龙头", "低成本龙头，作为时间和涨幅基准"),
    Stock("温氏股份", "300498", "1.5线", "猪+黄羽鸡，猪周期弹性被非猪业务稀释"),
    Stock("巨星农牧", "603477", "二线", "小市值弹性；上一轮涨幅大，可能有预期透支"),
    Stock("华统股份", "002840", "二线", "二线弹性样本"),
    Stock("神农集团", "605296", "二线", "2021-09 IPO，Wave 1 不完整"),
    Stock("唐人神", "002567", "二线", "信用压力更高，底部可能滞后"),
]

CYCLES = [
    Cycle(
        name="Wave 1 2021-2022",
        bottom_start="2021-08-01",
        bottom_end="2022-05-01",
        top_start="2022-05-01",
        top_end="2022-11-30",
        note="2021-2022 猪价反弹波段",
    ),
    Cycle(
        name="Wave 2 2023-2024",
        bottom_start="2023-08-01",
        bottom_end="2024-03-15",
        top_start="2024-03-15",
        top_end="2024-11-30",
        note="2023-2024 猪价反弹波段；边界写入配置，避免隐藏口径",
    ),
]

REFERENCE_STOCK = "牧原股份"
VERIFY_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = VERIFY_DIR / "data" / "stock_prices"
REPORT_DIR = VERIFY_DIR / "reports"


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
            except Exception as exc:  # noqa: BLE001 - keep source failures visible.
                errors.append(f"{provider_name} attempt {attempt}: {exc}")
                print(f"  Error: {exc}")
                time.sleep(2)

    raise RuntimeError(f"failed to fetch {stock.name} ({stock.code}): {' | '.join(errors)}")


def market_symbol(code: str) -> str:
    prefix = "sh" if code.startswith("6") else "sz"
    return f"{prefix}{code}"


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
    stock_by_name = {stock.name: stock for stock in STOCKS}

    for stock in STOCKS:
        result = analyze_cycle(price_data[stock.name], cycle)
        if result is None:
            rows.append(
                {
                    "公司": stock.name,
                    "层级": stock.tier,
                    "低点日期": pd.NaT,
                    "低点价": pd.NA,
                    "高点日期": pd.NaT,
                    "高点价": pd.NA,
                    "涨幅": pd.NA,
                    "备注": stock.note,
                }
            )
            continue

        rows.append(
            {
                "公司": stock.name,
                "层级": stock.tier,
                **result,
                "备注": stock.note,
            }
        )

    table = pd.DataFrame(rows)
    reference = table[table["公司"] == REFERENCE_STOCK]
    if reference.empty or pd.isna(reference.iloc[0]["涨幅"]):
        raise RuntimeError(f"reference stock {REFERENCE_STOCK} is missing in {cycle.name}")

    reference_row = reference.iloc[0]
    reference_bottom = reference_row["低点日期"]
    reference_top = reference_row["高点日期"]
    reference_gain = float(reference_row["涨幅"])

    table["相对牧原低点天数"] = table["低点日期"].apply(
        lambda value: pd.NA if pd.isna(value) else (value - reference_bottom).days
    )
    table["相对牧原高点天数"] = table["高点日期"].apply(
        lambda value: pd.NA if pd.isna(value) else (value - reference_top).days
    )
    table["相对牧原涨幅差"] = table["涨幅"].apply(
        lambda value: pd.NA if pd.isna(value) else float(value) - reference_gain
    )
    table["是否跑赢牧原"] = table["相对牧原涨幅差"].apply(
        lambda value: pd.NA if pd.isna(value) else ("是" if float(value) > 0 else "否")
    )

    # Keep an explicit lookup alive for future metadata expansion and to make
    # missing stocks obvious during edits.
    missing = sorted(set(table["公司"]) - set(stock_by_name))
    if missing:
        raise RuntimeError(f"unknown stocks in result table: {missing}")

    return table


def format_table(table: pd.DataFrame) -> pd.DataFrame:
    formatted = table.copy()
    for column in ["低点日期", "高点日期"]:
        formatted[column] = formatted[column].apply(
            lambda value: "" if pd.isna(value) else value.strftime("%Y-%m-%d")
        )
    for column in ["低点价", "高点价", "涨幅", "相对牧原涨幅差"]:
        formatted[column] = formatted[column].apply(
            lambda value: "" if pd.isna(value) else f"{float(value):.1f}"
        )
    for column in ["相对牧原低点天数", "相对牧原高点天数"]:
        formatted[column] = formatted[column].apply(
            lambda value: "" if pd.isna(value) else f"{int(value):+d}"
        )
    return formatted


def write_markdown_report(cycle_tables: list[tuple[Cycle, pd.DataFrame]]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "pig_cycle_node_comparison.md"

    lines = [
        "# 猪股周期节点对比",
        "",
        "口径：前复权日收盘价；在预先配置的行业周期窗口内，事后寻找各股票低点和高点。",
        "这份输出用于观察历史节点规律，不直接代表可交易信号。",
        "",
    ]

    for cycle, table in cycle_tables:
        lines.extend(
            [
                f"## {cycle.name}",
                "",
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

    price_data = {stock.name: fetch_stock(stock, start_date, end_date) for stock in STOCKS}

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
