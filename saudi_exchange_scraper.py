import json
import csv
import sys
import time
from typing import List, Dict, Optional
import math

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except Exception:
    WEBDRIVER_MANAGER_AVAILABLE = False

TARGET_URL = "https://www.saudiexchange.sa/wps/portal/saudiexchange/ourmarkets/main-market-watch/main-market-performance/!ut/p/z1/lc_LCsIwEAXQb-kHyFwjSeMyWpr66Mu0WLORrKSgVUT8foO7Up-zG-ZcmEuWGrKdu7cHd2vPnTv6fWfFnisBlkjk2lQKZWyqWTaNx9CgbR_IVAuUmSpzFnLAMLJ_5WEK7kGRTtbY-Lv4LY83o_A9b_tERtHck5VMlsgZRDgAw4p98KLDE3x40rgrXU513aBdjFQQPACfi5Hn/dz/d5/L0lHSkovd0RNQUZrQUVnQSEhLzROVkUvZW4!/"

REPORT_KEYWORDS = ["highest", "low", "percentage", "change"]
REPORT_AR_KEYWORDS = ["أعلى", "أدنى", "نسبة", "تغير"]
REPORT_VALUE_TEXT = "Gainers/Losers by Percentage"
PERIODS = ["1 Year", "9 Months", "6 Months", "3 Months"]


def build_driver(headless: bool = True) -> webdriver.Chrome:
    print("[init] starting Chrome driver")
    opts = Options()
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_argument(f"user-agent={ua}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1400,900")
    if headless:
        opts.add_argument("--headless=new")
    if WEBDRIVER_MANAGER_AVAILABLE:
        service = Service(ChromeDriverManager().install())
    else:
        service = Service()
    driver = webdriver.Chrome(service=service, options=opts)
    return driver


def open_target(driver: webdriver.Chrome) -> WebDriverWait:
    print("[nav] opening target URL")
    driver.get(TARGET_URL)
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "reportList")),
                EC.presence_of_element_located((By.NAME, "reportFilter")),
                EC.presence_of_element_located((By.ID, "periodList")),
                EC.presence_of_element_located((By.NAME, "timeFrameFilter")),
                EC.presence_of_element_located((By.XPATH, "//table")),
            )
        )
    except TimeoutException:
        pass
    try:
        if switch_to_frame_with_table(driver) or switch_to_frame_with_controls(driver):
            return WebDriverWait(driver, 30)
        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()
    return wait


def _has_target_controls(driver: webdriver.Chrome) -> bool:
    try:
        driver.find_element(By.XPATH, "//label[normalize-space()='Report']")
        driver.find_element(By.XPATH, "//label[normalize-space()='Period']")
        return True
    except NoSuchElementException:
        pass
    try:
        selects = driver.find_elements(By.TAG_NAME, "select")
        if len(selects) >= 2:
            return True
    except Exception:
        pass
    try:
        cbs = driver.find_elements(By.XPATH, "//*[@role='combobox']")
        if len(cbs) >= 2:
            return True
    except Exception:
        pass
    return False


def switch_to_frame_with_controls(driver: webdriver.Chrome, max_depth: int = 3) -> bool:
    def _dfs(depth: int) -> bool:
        if depth > max_depth:
            return False
        if _has_target_controls(driver):
            return True
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for fr in frames:
            try:
                driver.switch_to.frame(fr)
                if _dfs(depth + 1):
                    return True
            except Exception:
                pass
            finally:
                driver.switch_to.parent_frame()
        return False

    driver.switch_to.default_content()
    return _dfs(0)


def switch_to_frame_with_table(driver: webdriver.Chrome, max_depth: int = 3) -> bool:
    def _dfs(depth: int) -> bool:
        if depth > max_depth:
            return False
        try:
            tbls = driver.find_elements(By.XPATH, "//table")
            if tbls:
                return True
        except Exception:
            pass
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for fr in frames:
            try:
                driver.switch_to.frame(fr)
                if _dfs(depth + 1):
                    return True
            except Exception:
                pass
            finally:
                driver.switch_to.parent_frame()
        return False

    driver.switch_to.default_content()
    return _dfs(0)


def _find_dropdown_by_label(driver: webdriver.Chrome, label_text: str) -> Optional[webdriver.remote.webelement.WebElement]:
    paths = [
        f"//label[normalize-space()='{label_text}']/following::select[1]",
        f"//label[normalize-space()='{label_text}']/following::*[@role='combobox'][1]",
        f"//label[normalize-space()='{label_text}']/following::*[@aria-haspopup='listbox'][1]",
        f"//span[normalize-space()='{label_text}']/following::*[self::select or @role='combobox' or @aria-haspopup='listbox'][1]",
    ]
    for xp in paths:
        els = driver.find_elements(By.XPATH, xp)
        if els:
            return els[0]
    # Fallback: try any select that contains matching options
    selects = driver.find_elements(By.TAG_NAME, "select")
    for sel in selects:
        try:
            opts = sel.find_elements(By.TAG_NAME, "option")
            texts = [o.text.strip() for o in opts]
            lowtexts = [t.lower() for t in texts]
            if label_text.lower() == "report":
                if any(all(k in t for k in [k.lower() for k in REPORT_KEYWORDS]) for t in lowtexts) or \
                   any(all(k in t for k in [k for k in REPORT_AR_KEYWORDS]) for t in texts):
                    return sel
            if label_text.lower() == "period":
                if any(
                    (
                        ("year" in t) or ("سنة" in tt) or ("عام" in tt) or
                        ("months" in t) or ("أشهر" in tt)
                    )
                    for t, tt in zip(lowtexts, texts)
                ):
                    return sel
        except Exception:
            continue
    return None


def _find_select_by_ids_or_names(driver: webdriver.Chrome, ids_or_names: List[str]) -> Optional[webdriver.remote.webelement.WebElement]:
    for idn in ids_or_names:
        try:
            el = driver.find_element(By.ID, idn)
            if el.tag_name.lower() == "select":
                return el
        except Exception:
            pass
        try:
            el = driver.find_element(By.NAME, idn)
            if el.tag_name.lower() == "select":
                return el
        except Exception:
            pass
    return None


def select_any_dropdown_value(driver: webdriver.Chrome, wait: WebDriverWait, values: List[str]) -> bool:
    toggles = driver.find_elements(By.XPATH, 
        "//button[@aria-haspopup='listbox' or contains(@class,'dropdown') or contains(@class,'DropDown') or contains(@class,'c-dropdown')] | "
        "//*[@role='button' and (@aria-haspopup='listbox' or contains(@class,'dropdown'))]"
    )
    for tg in toggles:
        try:
            wait.until(EC.element_to_be_clickable(tg))
            tg.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", tg)
            except Exception:
                continue
        items = driver.find_elements(By.XPATH, 
            "//ul//li | //div[@role='listbox']//div | //div[@role='option'] | //li[@role='option']"
        )
        for v in values:
            vnorm = v.strip().lower()
            for it in items:
                txt = it.text.strip()
                if txt.lower() == vnorm or vnorm in txt.lower():
                    try:
                        wait.until(EC.element_to_be_clickable(it))
                        it.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", it)
                        except Exception:
                            continue
                    return True
    return False


def _select_native_select(el: webdriver.remote.webelement.WebElement, visible_text: Optional[str] = None, keywords: Optional[List[str]] = None) -> bool:
    try:
        sel = Select(el)
        if visible_text:
            try:
                sel.select_by_visible_text(visible_text)
                return True
            except Exception:
                pass
        if keywords:
            for opt in sel.options:
                t_en = opt.text.strip().lower()
                t_ar = opt.text.strip()
                if all(k in t_en for k in [k.lower() for k in keywords]):
                    opt.click()
                    return True
                if all(k in t_ar for k in REPORT_AR_KEYWORDS):
                    opt.click()
                    return True
        return False
    except Exception:
        return False


def _open_combobox(el: webdriver.remote.webelement.WebElement, wait: WebDriverWait) -> None:
    try:
        wait.until(EC.element_to_be_clickable(el))
        el.click()
    except Exception:
        try:
            driver = el.parent
            driver.execute_script("arguments[0].click();", el)
        except Exception:
            pass


def _select_from_combobox(driver: webdriver.Chrome, text: Optional[str] = None, keywords: Optional[List[str]] = None, wait: Optional[WebDriverWait] = None) -> bool:
    candidates = [
        "//ul[contains(@class,'dropdown') or contains(@class,'menu') or contains(@class,'listbox')]//li",
        "//div[contains(@class,'dropdown') or contains(@class,'menu')]//li",
        "//div[@role='listbox']//div|//ul[@role='listbox']//li",
    ]
    items = []
    for xp in candidates:
        items = driver.find_elements(By.XPATH, xp)
        if items:
            break
    if not items:
        return False
    target = None
    if text:
        tnorm = text.strip().lower()
        for it in items:
            if it.text.strip().lower() == tnorm:
                target = it
                break
    if not target and keywords:
        for it in items:
            t = it.text.strip().lower()
            if all(k.lower() in t for k in keywords):
                target = it
                break
    if not target and text:
        for it in items:
            if text.strip().lower() in it.text.strip().lower():
                target = it
                break
    if not target:
        return False
    try:
        if wait:
            wait.until(EC.element_to_be_clickable(target))
        target.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", target)
            return True
        except Exception:
            return False


def select_report(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    print("[select] choosing report option")
    el = _find_select_by_ids_or_names(driver, ["reportList", "reportFilter"]) or _find_dropdown_by_label(driver, "Report")
    if not el:
        print("[warn] report dropdown not found — trying global dropdown search")
        # Try global dropdown search for the specific value
        if select_any_dropdown_value(driver, wait, [REPORT_VALUE_TEXT]):
            return
        return
    if el.tag_name.lower() == "select":
        # Prefer exact value if present
        try:
            sel = Select(el)
            try:
                sel.select_by_value("gainersPercentage")
                return
            except Exception:
                pass
            ok = _select_native_select(el, visible_text=REPORT_VALUE_TEXT)
        except Exception:
            ok = False
        if not ok:
            if not _select_native_select(el, keywords=REPORT_KEYWORDS):
                _select_native_select(el, keywords=REPORT_AR_KEYWORDS)
        return
    _open_combobox(el, wait)
    # Try exact value first, then keywords
    if not _select_from_combobox(driver, text=REPORT_VALUE_TEXT, wait=wait):
        if not _select_from_combobox(driver, keywords=REPORT_KEYWORDS, wait=wait):
            _select_from_combobox(driver, keywords=REPORT_AR_KEYWORDS, wait=wait)


def select_period(driver: webdriver.Chrome, wait: WebDriverWait, period_text: str) -> None:
    print(f"[select] period: {period_text}")
    el = _find_select_by_ids_or_names(driver, ["periodList", "periodFilter", "period"]) or _find_dropdown_by_label(driver, "Period")
    if not el:
        print("[warn] period dropdown not found")
        return
    variants = [period_text]
    pt = period_text.lower()
    if "year" in pt:
        variants = ["1 Year", "Year", "سنة", "عام"]
    elif "months" in pt and "9" in pt:
        variants = ["9 Months", "9 أشهر", "٩ أشهر"]
    elif "months" in pt and "6" in pt:
        variants = ["6 Months", "6 أشهر", "٦ أشهر"]
    elif "months" in pt and "3" in pt:
        variants = ["3 Months", "3 أشهر", "٣ أشهر"]
    if el.tag_name.lower() == "select":
        # Prefer direct visible text selection
        ok = False
        try:
            sel = Select(el)
            for v in variants:
                try:
                    sel.select_by_visible_text(v)
                    ok = True
                    break
                except Exception:
                    continue
        except Exception:
            ok = False
        for v in variants:
            ok = _select_native_select(el, visible_text=v)
            if ok:
                break
        if not ok:
            for v in variants:
                if _select_native_select(el, keywords=[v]):
                    ok = True
                    break
        return
    _open_combobox(el, wait)
    for v in variants:
        if _select_from_combobox(driver, text=v, wait=wait):
            return
    for v in variants:
        if _select_from_combobox(driver, keywords=[v], wait=wait):
            return
    # As a last resort, search all dropdowns and pick the value
    select_any_dropdown_value(driver, wait, variants)


def _get_all_tables(driver: webdriver.Chrome) -> List[webdriver.remote.webelement.WebElement]:
    """Get only Gainers (Table 2) and Losers (Table 3) tables"""
    tables = []
    
    # Get marketPerformanceTable 1 (Main), 2 (Gainers), and 3 (Losers)
    for table_id in ["marketPerformanceTable1", "marketPerformanceTable2", "marketPerformanceTable3"]:
        try:
            tbl = driver.find_element(By.ID, table_id)
            if tbl.is_displayed():
                tables.append(tbl)
                print(f"[debug] found visible table by ID: {table_id}")
            else:
                # If it's not displayed but exists, we might still want it if it's the right ID
                # But usually we want visible data. Let's log it.
                print(f"[debug] found hidden table by ID: {table_id} - skipping")
        except Exception:
            pass
    
    if tables:
        return tables
    
    # Fallback removed to ensure we only get the specific tables requested
    return []


def _get_table(driver: webdriver.Chrome) -> Optional[webdriver.remote.webelement.WebElement]:
    """Legacy function - returns first table only"""
    tables = _get_all_tables(driver)
    return tables[0] if tables else None


def _get_tables_via_js(driver: webdriver.Chrome):
    try:
        data = driver.execute_script(
            "return (function(){\n"
            "  const results = [];\n"
            "  function collect(root){\n"
            "    try {\n"
            "      const ts = root.querySelectorAll('table');\n"
            "      ts.forEach(t=>results.push(t));\n"
            "      const all = root.querySelectorAll('*');\n"
            "      all.forEach(el=>{ if (el.shadowRoot) collect(el.shadowRoot); });\n"
            "    } catch(e){}\n"
            "  }\n"
            "  collect(document);\n"
            "  function extract(t){\n"
            "    const headers = Array.from(t.querySelectorAll('thead th')).map(th=>th.innerText.trim());\n"
            "    const rows = Array.from(t.querySelectorAll('tbody tr')).map(tr=>Array.from(tr.querySelectorAll('td')).map(td=>td.innerText.trim()));\n"
            "    return {headers, rows};\n"
            "  }\n"
            "  return results.map(extract);\n"
            "})();"
        )
        return data
    except Exception:
        return None


def _get_grid_via_js(driver: webdriver.Chrome):
    try:
        data = driver.execute_script(
            "return (function(){\n"
            "  const grids = Array.from(document.querySelectorAll('[role=grid]'));\n"
            "  function fromGrid(g){\n"
            "    const headers = Array.from(g.querySelectorAll('[role=columnheader], thead th')).map(x=>x.innerText.trim());\n"
            "    const rows = Array.from(g.querySelectorAll('[role=row]')).map(r => Array.from(r.querySelectorAll('[role=gridcell], td')).map(c=>c.innerText.trim())).filter(r=>r.length>0);\n"
            "    return {headers, rows};\n"
            "  }\n"
            "  return grids.map(fromGrid);\n"
            "})();"
        )
        return data
    except Exception:
        return None


def _first_cell_text(driver: webdriver.Chrome) -> Optional[str]:
    tbl = _get_table(driver)
    if tbl:
        try:
            cell = tbl.find_element(
                By.XPATH,
                ".//tbody/tr[1]/td[1] | .//tr[position()>1][1]/td[1] | .//tr[1]/td[1]"
            )
            return cell.text.strip()
        except Exception:
            pass
    # Try JS candidates
    js_tables = _get_tables_via_js(driver) or []
    js_grids = _get_grid_via_js(driver) or []
    candidates = js_tables + js_grids
    for t in candidates:
        rows = t.get('rows') or []
        if rows and rows[0]:
            return rows[0][0]
    return None


def wait_for_table_update(driver: webdriver.Chrome, wait: WebDriverWait, previous_first_cell: Optional[str]) -> None:
    print(f"[debug] waiting for table update. prev='{previous_first_cell}'")
    try:
        wait.until(lambda d: (_get_table(d) is not None) or (_get_tables_via_js(d) not in (None, [])) or (_get_grid_via_js(d) not in (None, [])))
    except TimeoutException:
        print("[warn] timeout waiting for table presence")
        return
    if previous_first_cell is None:
        try:
            wait.until(lambda d: _first_cell_text(d) not in (None, ""))
        except TimeoutException:
            print("[warn] timeout waiting for first cell content")
            return
        return
    try:
        def check_change(d):
            curr = _first_cell_text(d)
            # print(f"[debug] checking change: '{curr}' vs '{previous_first_cell}'")
            return curr != previous_first_cell
        wait.until(check_change)
    except TimeoutException:
        print(f"[warn] timeout waiting for table cell change (prev='{previous_first_cell}')")
        pass


def scrape_all_tables(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """Scrape all tables on the page (both Gainers and Losers)"""
    all_rows = []
    
    # Disable JS extraction - use Selenium directly to get both tables
    # Try to get all tables via JavaScript first
    # js_tables = _get_tables_via_js(driver) or []
    # js_grids = _get_grid_via_js(driver) or []
    # candidates = js_tables + js_grids
    
    # print(f"[debug] found {len(js_tables)} tables via JS, {len(js_grids)} grids")
    
    # if candidates:
    #     # Filter tables that have company data
    #     valid_tables = []
    #     for idx, t in enumerate(candidates):
    #         hs = [h.lower() for h in (t.get('headers') or [])]
    #         rows_count = len(t.get('rows') or [])
    #         print(f"[debug] table {idx}: {len(hs)} headers, {rows_count} rows, headers: {hs[:3]}")
    #         if any(('company' in h) or ('volume' in h) or ('value traded' in h) for h in hs):
    #             valid_tables.append(t)
    #             print(f"[debug] table {idx} is VALID (has company data)")
    #     
    #     print(f"[debug] {len(valid_tables)} valid tables found")
    #     
    #     if not valid_tables:
    #         print("[warn] no valid tables found via JS")
    #         valid_tables = candidates[:2] if len(candidates) >= 2 else candidates
    #     
    #     # Process all valid tables
    #     for table_idx, table_data in enumerate(valid_tables):
    #         headers = table_data.get('headers') or []
    #         rows_js = table_data.get('rows') or []
    #         print(f"[debug] processing table {table_idx}: {len(rows_js)} rows")
    #         
    #         for r in rows_js:
    #             while len(headers) < len(r):
    #                 headers.append(f"Column {len(headers)+1}")
    #             row = { (headers[i] if i < len(headers) else f"Column {i+1}"): (r[i] if i < len(r) else "") for i in range(len(r)) }
    #             all_rows.append(row)
    #     
    #     print(f"[debug] total rows collected: {len(all_rows)}")
    #     return all_rows
    
    # Use Selenium directly to get both tables
    try:
        tables = _get_all_tables(driver)
        print(f"[info] found {len(tables)} tables via Selenium")
        
        expected_headers = ["Company", "Open", "Highest", "Lowest", "Close", "Change", "Change %", "Volume Traded", "Value Traded"]
        
        for tbl in tables:
            try:
                # Get headers
                headers = []
                try:
                    ths = tbl.find_elements(By.XPATH, ".//thead//th")
                    headers = [th.text.strip() for th in ths if th.text.strip()]
                except Exception:
                    pass
                
                # Use expected headers if needed
                if len(headers) != 9 or (headers and headers[0] != "Company"):
                    headers = expected_headers
                
                # Get rows
                trs = tbl.find_elements(By.XPATH, ".//tbody/tr")
                if not trs:
                    trs = tbl.find_elements(By.XPATH, ".//tr[position()>1]")
                
                print(f"[debug] processing Selenium table: {len(trs)} rows")
                
                for tr in trs:
                    tds = tr.find_elements(By.XPATH, ".//td")
                    if not tds:
                        continue
                    
                    while len(headers) < len(tds):
                        headers.append(f"Column {len(headers)+1}")
                    
                    row = {}
                    for i, td in enumerate(tds):
                        key = headers[i] if i < len(headers) else f"Column {i+1}"
                        row[key] = td.text.strip()
                    
                    all_rows.append(row)
            except Exception as e:
                print(f"[warn] error processing table: {e}")
                continue
    except Exception as e:
        print(f"[error] failed to get tables: {e}")
    
    print(f"[debug] total rows collected from Selenium: {len(all_rows)}")
    return all_rows


def scrape_table(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """Legacy function - now calls scrape_all_tables"""
    return scrape_all_tables(driver)


def save_results_json(results: Dict[str, List[Dict[str, str]]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def save_results_csv(results: Dict[str, List[Dict[str, str]]], path: str) -> None:
    # Define logical order
    logical_order = ["period", "Company", "Open", "Highest", "Lowest", "Close", "Change", "Change %", "Volume Traded", "Value Traded"]
    
    all_headers = set(["period"])
    for period, rows in results.items():
        for r in rows:
            all_headers.update(r.keys())
            
    # Sort headers: logical ones first in order, then any others alphabetically
    remaining = [h for h in all_headers if h not in logical_order]
    headers = [h for h in logical_order if h in all_headers] + sorted(remaining)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for period, rows in results.items():
            for r in rows:
                row = {h: r.get(h, "") for h in headers}
                row["period"] = period
                w.writerow(row)


def calculate_rs_metrics(results: Dict[str, List[Dict[str, str]]], output_path: str) -> None:
    # Flatten data for DataFrame
    data = []
    for period, rows in results.items():
        for r in rows:
            # Clean Change %: remove '%' and convert to float
            try:
                change_pct_str = r.get("Change %", "").replace("%", "").strip()
                change_pct = float(change_pct_str) if change_pct_str else None
            except ValueError:
                change_pct = None
                
            data.append({
                "Company": r.get("Company", ""),
                "period": period,
                "Change %": change_pct
            })
    
    if not data:
        print("[warn] no data to analyze")
        return

    df = pd.DataFrame(data)
    
    # Pivot: Company as index, period as columns, values are Change %
    # We want columns like: "Change %_1 Year", "Change %_9 Months", etc.
    df_pivot = df.pivot(index="Company", columns="period", values="Change %")
    
    # Define periods and weights
    # Weights: 1Y (20%), 9M (20%), 6M (20%), 3M (40%)
    period_map = {
        "1 Year": 0.2,
        "9 Months": 0.2,
        "6 Months": 0.2,
        "3 Months": 0.4
    }
    
    # Calculate RS for each period
    # Formula: MIN(ROUND(PERCENTRANK.INC(AC:AC,AC6)*100,0),99)
    # Pandas rank(pct=True) gives 0.0 to 1.0. We multiply by 100.
    rs_cols = []
    for p, weight in period_map.items():
        if p in df_pivot.columns:
            col_name = f"RS_{p.replace(' ', '')}"
            # Refined logic to match user formula: MIN(ROUND(..., 0), 99)
            df_pivot[col_name] = (df_pivot[p].rank(pct=True) * 100).round(0).clip(upper=99)
            rs_cols.append((col_name, weight))
        else:
            print(f"[warn] period '{p}' not found in data")

    # Calculate Final RS
    # Formula: ROUNDUP(Sum(RS * Weight), 0)
    final_rs_col = "RS"
    weighted_sum = 0
    for col, weight in rs_cols:
        weighted_sum += df_pivot[col].fillna(0) * weight
    
    # ceil is equivalent to ROUNDUP(x, 0)
    df_pivot[final_rs_col] = np.ceil(weighted_sum)
    
    # Select and reorder columns for output
    # We want Company (index), then the RS columns, then the Final RS.
    output_cols = [col for col, _ in rs_cols] + [final_rs_col]
    
    # Save
    # Save as Standard CSV
    df_pivot[output_cols].to_csv(output_path, encoding="utf-8-sig")
    print(f"[analysis] saved RS analysis to {output_path}")

    # Save as Tab Separated (TSV) - Best for copy-pasting to Excel
    tsv_path = output_path.replace(".csv", ".tsv")
    df_pivot[output_cols].to_csv(tsv_path, sep='\t', encoding="utf-8-sig")
    print(f"[analysis] saved TSV analysis to {tsv_path} (Best for copy-paste)")

    # Save as Aligned Text Table - Best for viewing alignment
    txt_path = output_path.replace(".csv", ".txt")
    with open(txt_path, "w", encoding="utf-8-sig") as f:
        f.write(df_pivot[output_cols].to_string())
    print(f"[analysis] saved aligned text analysis to {txt_path}")
    
    # Try saving as Excel (.xlsx)
    try:
        xlsx_path = output_path.replace(".csv", ".xlsx")
        df_pivot[output_cols].to_excel(xlsx_path)
        print(f"[analysis] saved Excel analysis to {xlsx_path}")
    except ImportError:
        pass
    except Exception as e:
        print(f"[warn] could not save Excel file: {e}")


def run(headless: bool = True) -> Dict[str, List[Dict[str, str]]]:
    driver = build_driver(headless=headless)
    try:
        wait = open_target(driver)
        prev_before_report = _first_cell_text(driver)
        select_report(driver, wait)
        wait_for_table_update(driver, wait, prev_before_report)
        results = {}
        for p in PERIODS:
            prev = _first_cell_text(driver)
            select_period(driver, wait, p)
            wait_for_table_update(driver, wait, prev)
            data = scrape_table(driver)
            print(f"[data] rows scraped: {len(data)} for {p}")
            results[p] = data
        print("[save] writing JSON/CSV files")
        save_results_json(results, "saudiexchange_results.json")
        save_results_csv(results, "saudiexchange_results.csv")
        
        if PANDAS_AVAILABLE:
            print("[analysis] calculating RS metrics")
            calculate_rs_metrics(results, "saudiexchange_rs_analysis.csv")
        else:
            print("[warn] pandas not available, skipping RS analysis")

        return results
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    headless = True
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("--show", "--headed", "--no-headless"):
        headless = False
    res = run(headless=headless)
    print(json.dumps(res, ensure_ascii=False, indent=2))

