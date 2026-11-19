import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import sqlite3
import pandas as pd
import os


# ----------------------------------------------------------------------
# 1. 智慧讀取資料函式
# ----------------------------------------------------------------------
def load_car_data():
    df = pd.DataFrame()
    db_files = ["auto8891.db", "auto_car_8891.db", "cars.db"]
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                if tables:
                    table_name = tables[0]
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                conn.close()
                break
            except Exception as e:
                print(f"讀取 SQLite 失敗 ({db_file}): {e}")

    if df.empty:
        csv_files = ["8891_cars.csv", "cars.csv"]
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                try:
                    df = pd.read_csv(csv_file, encoding="utf-8-sig")
                    break
                except Exception as e:
                    print(f"讀取 CSV 失敗 ({csv_file}): {e}")

    return df


def get_field_value(row, possible_keys, default="未知"):
    for key in possible_keys:
        if key in row and pd.notna(row[key]):
            val = str(row[key]).strip()
            if val and val != "nan" and val != "None":
                return val
    return default


# ----------------------------------------------------------------------
# 2. 建立 Tkinter 主視窗
# ----------------------------------------------------------------------
root = tk.Tk()
root.title("🚗 8891 中古車智慧管理與估價系統")
root.geometry("900x680")
root.resizable(False, False)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# ======================================================================
# 分頁一：爬蟲與車輛清單管理
# ======================================================================
tab_manage = ttk.Frame(notebook)
notebook.add(tab_manage, text=" 📂 車庫資料與爬蟲管理 ")

# 頂部控制與篩選列
control_frame = ttk.LabelFrame(tab_manage, text=" 資料控制與多維度篩選 ", padding=10)
control_frame.pack(fill="x", padx=10, pady=10)

# 重新載入按鈕
load_btn = ttk.Button(
    control_frame, text="重新載入資料庫", command=lambda: refresh_table()
)
load_btn.pack(side="left", padx=5)

# 縣市篩選
ttk.Label(control_frame, text=" 縣市：").pack(side="left", padx=2)
city_combobox = ttk.Combobox(
    control_frame, values=["全部縣市"], width=10, state="readonly"
)
city_combobox.pack(side="left", padx=2)
city_combobox.set("全部縣市")

# 🌟 新增：關鍵字搜尋輸入框
ttk.Label(control_frame, text=" 關鍵字：").pack(side="left", padx=5)
keyword_entry = ttk.Entry(control_frame, width=15)
keyword_entry.pack(side="left", padx=2)


def on_search_click():
    refresh_table()


search_btn = ttk.Button(control_frame, text="搜尋", command=on_search_click, width=6)
search_btn.pack(side="left", padx=5)


def export_cars_to_csv():
    global current_filtered_df
    if current_filtered_df is None or current_filtered_df.empty:
        messagebox.showwarning("提示", "目前沒有可匯出的車輛資料！")
        return

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = filedialog.asksaveasfilename(
        title="匯出車輛清單為 CSV",
        defaultextension=".csv",
        initialfile=f"車庫車輛清單_{now_str}.csv",
        filetypes=[("CSV 檔案 (*.csv)", "*.csv"), ("所有檔案 (*.*)", "*.*")],
    )

    if not file_path:
        return

    try:
        current_filtered_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        messagebox.showinfo(
            "匯出成功",
            f"已成功匯出 {len(current_filtered_df):,} 筆車輛資料至：\n{file_path}",
        )
    except Exception as e:
        messagebox.showerror("匯出失敗", f"寫入 CSV 時發生錯誤：\n{e}")


export_csv_btn = ttk.Button(
    control_frame, text="💾 匯出清單至 CSV", command=export_cars_to_csv
)
export_csv_btn.pack(side="right", padx=5)

# 表格顯示區 (Treeview) 與捲軸
table_frame = ttk.Frame(tab_manage)
table_frame.pack(padx=10, pady=5, fill="both", expand=True)

columns = ("縣市", "標題", "售價", "年份", "里程")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

col_widths = [80, 320, 90, 80, 90]
for col, width in zip(columns, col_widths):
    tree.heading(col, text=col)
    tree.column(col, width=width, anchor="w" if col == "標題" else "center")

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# ======================================================================
# 分頁二：AI 智慧中古車估價系統
# ======================================================================
tab_valuation = ttk.Frame(notebook)
notebook.add(tab_valuation, text=" 💰 AI 智慧車價預測估價 ")

val_form = ttk.LabelFrame(tab_valuation, text=" 請輸入欲估價的車輛條件 ", padding=20)
val_form.pack(padx=20, pady=15, fill="x")

ttk.Label(val_form, text="熱門車系：").grid(row=0, column=0, sticky="w", pady=8)
car_brand_combobox = ttk.Combobox(
    val_form,
    values=[
        "Toyota RAV4",
        "Honda CR-V",
        "Toyota Corolla Altis",
        "BMW 3系列",
        "M-Benz A-Class",
    ],
    width=25,
)
car_brand_combobox.grid(row=0, column=1, sticky="ew", pady=8)
car_brand_combobox.set("Toyota RAV4")

ttk.Label(val_form, text="出廠年份：").grid(row=1, column=0, sticky="w", pady=8)
year_spinbox = ttk.Spinbox(val_form, from_=2010, to=2026, width=23)
year_spinbox.grid(row=1, column=1, sticky="ew", pady=8)
year_spinbox.set(2020)

ttk.Label(val_form, text="行駛里程 (公里)：").grid(row=2, column=0, sticky="w", pady=8)
km_entry = ttk.Entry(val_form, width=25)
km_entry.grid(row=2, column=1, sticky="ew", pady=8)
km_entry.insert(0, "50000")

result_frame = ttk.LabelFrame(tab_valuation, text=" 估價結果分析 ", padding=15)
result_frame.pack(padx=20, pady=10, fill="both", expand=True)

result_label = tk.Label(
    result_frame,
    text="請輸入車輛資訊並點擊下方「開始計算預估車價」按鈕...",
    font=("Arial", 11),
    fg="gray",
    justify="left",
)
result_label.pack(anchor="w", padx=10, pady=10)

# 估價歷史紀錄
valuation_history = []


def calculate_price():
    brand = car_brand_combobox.get().strip()
    year = year_spinbox.get().strip()
    km = km_entry.get().strip()

    if not brand:
        messagebox.showwarning("格式錯誤", "請選擇或輸入車款名稱！")
        return

    if not km.isdigit():
        messagebox.showwarning("格式錯誤", "里程數請輸入純數字！")
        return

    try:
        year_int = int(year)
    except ValueError:
        messagebox.showwarning("格式錯誤", "年份請輸入有效西元年份！")
        return

    base_price = 700000 if "Toyota" in brand else 950000
    estimated_price = base_price - (2026 - year_int) * 40000 - int(km) * 1.5
    estimated_price = max(int(estimated_price), 150000)

    low_price = int(estimated_price * 0.95)
    high_price = int(estimated_price * 1.05)
    seller_price = int(low_price * 0.9)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 加入歷史紀錄
    record = {
        "估價時間": now_str,
        "車款": brand,
        "出廠年份": f"{year_int}年",
        "行駛里程(公里)": int(km),
        "基準預估價(元)": estimated_price,
        "行情下限(元)": low_price,
        "行情上限(元)": high_price,
        "預估行情區間": f"NT$ {low_price:,} ~ {high_price:,} 元",
        "買家建議": f"成交價在 NT$ {low_price:,} ~ {high_price:,} 元內屬合理範圍",
        "賣家收購建議": f"收購價約落在下限約 90% 左右（約 NT$ {seller_price:,} 元）",
    }
    valuation_history.append(record)

    result_text = (
        f"🚗 車款：{brand} ({year_int}年式)\n"
        f"📊 行駛里程：{int(km):,} 公里\n"
        f"🕒 估價時間：{now_str}\n"
        f"--------------------------------------------------\n"
        f"💰 預估市場行情區間：新台幣 {low_price:,} ~ {high_price:,} 元\n"
        f"💡 專家建議：\n"
        f"  • 若您是買家，成交價在此區間內屬合理範圍。\n"
        f"  • 若您是賣家，收購價可能會落在下限約 90% 左右（約 {seller_price:,} 元）。\n"
        f"--------------------------------------------------\n"
        f"📁 目前已累計 {len(valuation_history)} 筆估價紀錄，可點擊下方「💾 儲存估價結果為 CSV」進行匯出。"
    )
    result_label.config(text=result_text, fg="#2c3e50")


def save_valuation_to_csv():
    if not valuation_history:
        messagebox.showwarning("提示", "目前尚無估價紀錄，請先點擊「開始計算預估車價」！")
        return

    records_to_save = valuation_history
    if len(valuation_history) > 1:
        choice = messagebox.askyesnocancel(
            "儲存選項",
            f"目前累計有 {len(valuation_history)} 筆估價紀錄：\n\n"
            f"• 點選【是 (Yes)】：匯出全部 {len(valuation_history)} 筆紀錄\n"
            f"• 點選【否 (No)】：僅匯出最新 1 筆紀錄\n"
            f"• 點選【取消 (Cancel)】：取消匯出",
        )
        if choice is None:
            return
        elif choice is False:
            records_to_save = [valuation_history[-1]]

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = filedialog.asksaveasfilename(
        title="儲存估價結果為 CSV",
        defaultextension=".csv",
        initialfile=f"車輛估價紀錄_{now_str}.csv",
        filetypes=[("CSV 檔案 (*.csv)", "*.csv"), ("所有檔案 (*.*)", "*.*")],
    )

    if not file_path:
        return

    try:
        out_df = pd.DataFrame(records_to_save)
        out_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        messagebox.showinfo(
            "儲存成功",
            f"已成功將 {len(records_to_save)} 筆估價紀錄儲存至：\n{file_path}",
        )
    except Exception as e:
        messagebox.showerror("儲存失敗", f"寫入 CSV 時發生錯誤：\n{e}")


def clear_valuation_history():
    if not valuation_history:
        messagebox.showinfo("提示", "目前沒有估價紀錄。")
        return

    if messagebox.askyesno("確認清空", f"確定要清空目前累積的 {len(valuation_history)} 筆估價紀錄嗎？"):
        valuation_history.clear()
        result_label.config(
            text="已清空歷史紀錄。請輸入車輛資訊並點擊下方「開始計算預估車價」按鈕...",
            fg="gray",
        )
        messagebox.showinfo("提示", "估價紀錄已清空！")


val_btn_frame = ttk.Frame(tab_valuation)
val_btn_frame.pack(pady=10)

calc_btn = tk.Button(
    val_btn_frame,
    text="✨ 開始計算預估車價",
    bg="#4CAF50",
    fg="white",
    font=("Arial", 11, "bold"),
    command=calculate_price,
    cursor="hand2",
    padx=12,
    pady=4,
)
calc_btn.pack(side="left", padx=8)

save_val_btn = tk.Button(
    val_btn_frame,
    text="💾 儲存估價結果為 CSV",
    bg="#2196F3",
    fg="white",
    font=("Arial", 11, "bold"),
    command=save_valuation_to_csv,
    cursor="hand2",
    padx=12,
    pady=4,
)
save_val_btn.pack(side="left", padx=8)

clear_val_btn = tk.Button(
    val_btn_frame,
    text="🗑️ 清空紀錄",
    bg="#e0e0e0",
    fg="#333333",
    font=("Arial", 10),
    command=clear_valuation_history,
    cursor="hand2",
    padx=10,
    pady=4,
)
clear_val_btn.pack(side="left", padx=8)


# ----------------------------------------------------------------------
# 3. 資料處理與排序核心邏輯
# ----------------------------------------------------------------------
current_filtered_df = pd.DataFrame()
current_sort_col = None
sort_ascending = True


def parse_numeric(val_str, col_name):
    """將帶有單位的字串（如 26.8萬、2019年、2萬公里）轉為純數字供正確排序"""
    import re

    if not val_str or val_str == "未知":
        return 0.0

    s = str(val_str).replace(",", "")

    # 萃取數字
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", s)
    if not numbers:
        return 0.0
    num = float(numbers[0])

    # 根據欄位與單位換算實際數值大小
    if col_name == "售價":
        if "萬" in s:
            num *= 10000
    elif col_name == "里程":
        if "萬" in s:
            num *= 10000
    return num


def populate_tree_from_df(df):
    for row_id in tree.get_children():
        tree.delete(row_id)

    for _, row in df.iterrows():
        city = get_field_value(row, ["縣市地區", "縣市", "地區", "city"], "未知")
        title = get_field_value(
            row, ["車輛標題", "標題", "車款", "title", "name"], "未知"
        )
        price = get_field_value(row, ["售價", "價格", "price"], "未知")
        year = get_field_value(row, ["年份", "出廠年份", "year"], "未知")
        km = get_field_value(row, ["里程", "行駛里程", "km"], "未知")

        tree.insert("", "end", values=(city, title, price, year, km))


def refresh_table(sort_col=None):
    global current_sort_col, sort_ascending, current_filtered_df

    df = load_car_data()
    if df.empty:
        return

    # 1. 縣市篩選
    selected_city = city_combobox.get()
    city_col = next(
        (col for col in ["縣市地區", "縣市", "地區", "city"] if col in df.columns), None
    )
    if selected_city != "全部縣市" and city_col:
        df = df[df[city_col] == selected_city]

    # 2. 關鍵字搜尋篩選
    keyword = keyword_entry.get().strip()
    if keyword:
        title_col = next(
            (
                col
                for col in ["車輛標題", "標題", "車款", "title", "name"]
                if col in df.columns
            ),
            None,
        )
        if title_col:
            df = df[
                df[title_col].astype(str).str.contains(keyword, case=False, na=False)
            ]

    # 更新縣市下拉選單清單
    if city_col and len(city_combobox["values"]) <= 1:
        cities = ["全部縣市"] + sorted(
            load_car_data()[city_col].dropna().unique().tolist()
        )
        city_combobox["values"] = cities

    # 3. 排序處理 (針對售價、年份、里程進行點擊切換大小排序)
    if sort_col:
        if current_sort_col == sort_col:
            sort_ascending = (
                not sort_ascending
            )  # 再次點擊反轉排序方向 (由大到小 / 從小到大)
        else:
            current_sort_col = sort_col
            sort_ascending = True  # 預設首次點擊由小到大

        # 欄位名稱對應資料庫欄位
        col_key_map = {
            "售價": ["售價", "價格", "price"],
            "年份": ["年份", "出廠年份", "year"],
            "里程": ["里程", "行駛里程", "km"],
        }
        actual_col = None
        for k in col_key_map.get(sort_col, []):
            if k in df.columns:
                actual_col = k
                break

        if actual_col:
            # 透過自訂數值轉換函數進行精準排序
            df["_sort_temp"] = df[actual_col].apply(
                lambda x: parse_numeric(x, sort_col)
            )
            df = df.sort_values(by="_sort_temp", ascending=sort_ascending)
            df = df.drop(columns=["_sort_temp"])

            # 更新表頭箭頭指示提示
            arrow = " 🔼" if sort_ascending else " 🔽"
            for c in columns:
                base_text = c.replace(" 🔼", "").replace(" 🔽", "")
                if c == sort_col:
                    tree.heading(
                        c,
                        text=base_text + arrow,
                        command=lambda col=c: refresh_table(col),
                    )
                else:
                    tree.heading(
                        c, text=base_text, command=lambda col=c: refresh_table(col)
                    )
    else:
        # 初始化表頭點擊事件繫結
        for c in columns:
            if c in ["售價", "年份", "里程"]:
                tree.heading(c, text=c, command=lambda col=c: refresh_table(col))
            else:
                tree.heading(c, text=c, command=lambda col=c: None)

    current_filtered_df = df.copy()
    populate_tree_from_df(df)


# 縣市選單變動自動重新整理
city_combobox.bind("<<ComboboxSelected>>", lambda e: refresh_table())

# 4. 初始化：啟動時載入資料
refresh_table()

# 5. 啟動主迴圈
if __name__ == "__main__":
    root.mainloop()
