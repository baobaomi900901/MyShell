import requests
import json
import os
import re
from datetime import datetime, timedelta

# ========== 必填配置（从浏览器复制） ==========
BASE_URL = "https://qywx.kingsware.cn"
COOKIE = "LastLoginPlaceIndex=3; LastLoginPlace=""; JSESSIONID=8A02A69EECA5D528C6EF6E42747C9534; __bid_n=19ae14b62a64912f59fd77; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219ae14b64fa1ca-050d6a1f52f206-26061b51-1821369-19ae14b64fb9e8%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTlhZTE0YjY0ZmExY2EtMDUwZDZhMWY1MmYyMDYtMjYwNjFiNTEtMTgyMTM2OS0xOWFlMTRiNjRmYjllOCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219ae14b64fa1ca-050d6a1f52f206-26061b51-1821369-19ae14b64fb9e8%22%7D; Hm_lvt_1d2cbdc88222087f0ca82a4f939f5b1c=1764716401,1765330974,1765334418,1766656357; _uetvid=a3d39840cfd211f0acdb4bef8029c7b5"          # 从浏览器 DevTools 中复制

# 固定的自定义请求头（除非系统重新生成，否则一般不变）
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "apptoken": "4a9709fae64fccd97a62595b92572fa8",  # 你提供的 token
    "loginid": "tangqingwei",
    "userid": "15175",
    "departmentid": "undefined",
    "Content-Type": "application/json",
    "Cookie": COOKIE                                 # Cookie 放在 headers 里也可以
}

# ========== 填报参数（可按需修改） ==========
USER_ID = 15175
# YEAR, MONTH, TARGET_DATE 由主流程动态获取
CURREMARKPLAN = "3"
REMARK = "4"
CITY = "珠海"
TEAM_ID = "4672"
PROJECT_ID = "377aeb04b0614af1bb82bdd3886efd94"

# ========== 工具函数 ==========
def get_journal_list():
    """调用 DailyCheckInfo 获取当月日志"""
    url = f"{BASE_URL}/OA/human.do"
    params = {
        "method": "DailyCheckInfo",
        "year": YEAR,
        "month": MONTH,
        "userId": USER_ID
    }
    resp = requests.get(url, params=params, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def find_autoid(data, target_date):
    """从返回数据里提取目标日期的 autoid"""
    # 尝试不同可能的列表字段
    records = data.get("data") or data.get("list") or data.get("rows") or data
    if not isinstance(records, list):
        records = []
    for item in records:
        if item.get("workdate") == target_date or item.get("date") == target_date:
            return item.get("autoid") or item.get("autoId") or item.get("id")
    return None

def submit_journal(autoid):
    """提交 / 更新日报"""
    url = f"{BASE_URL}/OA/human.do?method=journal"
    payload = {
        "autoid": autoid,
        "city": CITY,
        "curnoremark": None,
        "curremarkplan": CURREMARKPLAN,
        "nextremark": None,
        "projectid": PROJECT_ID,
        "remark": REMARK,
        "teamid": TEAM_ID,
        "workdate": TARGET_DATE
    }
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()

# ========== 主流程 ==========
if __name__ == "__main__":
    global YEAR, MONTH, TARGET_DATE

    raw = input("请输入日期(yymmdd，回车默认今天，加~表示循环到今天): ").strip()

    # -------------------- 日期解析 --------------------
    task_dates = []  # [(TARGET_DATE, YEAR, MONTH, date_obj), ...]
    today = datetime.now().date()

    if not raw:
        task_dates.append((today.strftime("%Y-%m-%d"), today.year, today.month, today))
    elif raw == "本周":
        # 以星期日作为一周起始
        sunday = today - timedelta(days=today.isoweekday() % 7)
        d = sunday
        while d <= today:
            task_dates.append((d.strftime("%Y-%m-%d"), d.year, d.month, d))
            d += timedelta(days=1)
    elif raw.endswith("~"):
        start_raw = raw[:-1]
        yy = int(start_raw[0:2])
        mm = int(start_raw[2:4])
        dd = int(start_raw[4:6])
        start = datetime(2000 + yy, mm, dd).date()
        d = start
        while d <= today:
            task_dates.append((d.strftime("%Y-%m-%d"), d.year, d.month, d))
            d += timedelta(days=1)
    else:
        yy = int(raw[0:2])
        mm = int(raw[2:4])
        dd = int(raw[4:6])
        d = datetime(2000 + yy, mm, dd).date()
        task_dates.append((d.strftime("%Y-%m-%d"), d.year, d.month, d))

    # -------------------- 读取桌面日报.md --------------------
    journal_path = os.path.join(os.path.expanduser("~"), "Desktop", "日报.md")
    if os.path.exists(journal_path):
        with open(journal_path, "r", encoding="utf-8") as f:
            journal_text = f.read()
        m_plan = re.search(r"今日计划：\s*?\r?\n(.*?)\r?\n---", journal_text, re.DOTALL)
        m_done = re.search(r"今日已完成：\s*?\r?\n(.*?)\r?\n---", journal_text, re.DOTALL)
        if m_plan:
            CURREMARKPLAN = m_plan.group(1)
        if m_done:
            REMARK = m_done.group(1)
    else:
        print("未找到桌面日报.md，使用默认填报值")

    print(f"共 {len(task_dates)} 个日期需要处理")

    # -------------------- 循环处理 --------------------
    prev_month_key = None
    data = None

    for target_date, year, month, d in task_dates:
        TARGET_DATE = target_date
        YEAR, MONTH = year, month

        month_key = f"{year}-{month:02d}"
        if month_key != prev_month_key or data is None:
            print(f"  切换至 {year}年{month}月，重新查询当月日志...")
            data = get_journal_list()
            prev_month_key = month_key

        autoid = find_autoid(data, TARGET_DATE)
        print(f"  [{TARGET_DATE}] autoid = {autoid}（None 表示新增）", end="")

        result = submit_journal(autoid)
        if result.get("code") == "success":
            print(" ✅")
        else:
            print(" ❌: ", json.dumps(result, ensure_ascii=False))
