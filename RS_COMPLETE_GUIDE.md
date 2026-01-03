# دليل شامل لحساب RS Rating - الطريقة الصحيحة

---

## 📚 **جدول المحتويات**

1. [طريقة الحساب الكاملة](#طريقة-الحساب-الكاملة)
2. [التحسينات المقترحة](#التحسينات-المقترحة)
3. [أمثلة عملية](#أمثلة-عملية)

---

# 🎯 **طريقة الحساب الكاملة**

## **الخطوة 1️⃣: حساب Change % لكل فترة**

### **المدخلات:**
- `close` (السعر الحالي)
- `date` (التاريخ الحالي)

### **الطريقة:**

**استخدم `close` (مش `change%`)** لأن:
- الـ `change%` اللي في الـ DB هو التغير اليومي فقط
- إحنا محتاجين التغير على مدى **3, 6, 9, 12 شهر**

### **الحساب:**

```python
from dateutil.relativedelta import relativedelta

def calculate_change_percent(df, symbol, current_date, months):
    """
    حساب Change % لفترة معينة
    
    Args:
        df: DataFrame فيه كل البيانات
        symbol: رمز السهم
        current_date: التاريخ الحالي
        months: عدد الشهور (3, 6, 9, 12)
    
    Returns:
        Change % (عدد عشري، مثلاً 0.15 = 15%)
    """
    # 1. جيب السعر الحالي
    current_row = df[(df['symbol'] == symbol) & (df['date'] == current_date)]
    if current_row.empty:
        return None
    
    current_price = current_row.iloc[0]['close']
    
    # 2. احسب التاريخ القديم (قبل X شهور)
    # استخدام Calendar Months (مش Trading Days)
    past_date = current_date - relativedelta(months=months)
    
    # 3. جيب أقرب سعر قبل أو في التاريخ القديم
    past_data = df[(df['symbol'] == symbol) & (df['date'] <= past_date)]
    if past_data.empty:
        return None
    
    past_price = past_data.iloc[-1]['close']
    
    # 4. احسب Change %
    if past_price and past_price > 0:
        change_percent = (current_price - past_price) / past_price
        return change_percent
    else:
        return None

# مثال:
change_3m = calculate_change_percent(df, '1120', date.today(), 3)
# النتيجة: 0.15 (يعني 15%)
```

### **ملاحظات مهمة:**

1. **استخدم Calendar Months (مش Trading Days):**
   - ❌ غلط: عد 63 يوم تداول للوراء
   - ✅ صح: اطرح 3 شهور من التاريخ (`relativedelta(months=3)`)

2. **ليه Calendar Months؟**
   - لأن موقع تداول بيستخدم Calendar Months
   - عشان تطابق نتائجنا بالظبط

---

## **الخطوة 2️⃣: حساب RS Raw (المتوسط الموزون)**

### **المعادلة:**

```
RS_Raw = (Change_3M × 0.4) + (Change_6M × 0.2) + (Change_9M × 0.2) + (Change_12M × 0.2)
```

### **الأوزان:**
- **3 شهور:** 40% (الأهم)
- **6 شهور:** 20%
- **9 شهور:** 20%
- **12 شهر:** 20%

### **الكود:**

```python
def calculate_rs_raw(change_3m, change_6m, change_9m, change_12m):
    """
    حساب RS Raw من الـ Change %
    
    Args:
        change_3m: Change % لـ 3 شهور (عدد عشري)
        change_6m: Change % لـ 6 شهور
        change_9m: Change % لـ 9 شهور
        change_12m: Change % لـ 12 شهر
    
    Returns:
        RS Raw (عدد عشري)
    """
    # التحقق من وجود القيم
    if any(x is None for x in [change_3m, change_6m, change_9m, change_12m]):
        return None
    
    rs_raw = (
        (change_3m * 0.4) +
        (change_6m * 0.2) +
        (change_9m * 0.2) +
        (change_12m * 0.2)
    )
    
    return rs_raw

# مثال:
rs_raw = calculate_rs_raw(0.15, 0.20, 0.25, 0.30)
# النتيجة: 0.20 (يعني 20%)
```

### **⚠️ خطأ شائع:**

❌ **لا تحسب rs_raw من الـ Ranks!**

```python
# ❌ غلط
rs_raw = (rank_3m * 0.4) + (rank_6m * 0.2) + ...
```

✅ **احسبه من الـ Returns (Change %):**

```python
# ✅ صح
rs_raw = (change_3m * 0.4) + (change_6m * 0.2) + ...
```

---

## **الخطوة 3️⃣: حساب RS Rating (الترتيب المئوي من 1 لـ 99)**

### **المعادلة:**

```
RS_Rating = Percentile_Rank(RS_Raw, All_Stocks_RS_Raw) × 100
```

**يعني:**
- لو السهم في الـ Top 1% → RS = 99
- لو السهم في الـ Top 10% → RS = 90
- لو السهم في الـ Bottom 1% → RS = 1

### **الكود:**

```python
def calculate_rs_rating(df, date):
    """
    حساب RS Rating لكل الأسهم في يوم معين
    
    Args:
        df: DataFrame فيه rs_raw لكل سهم
        date: التاريخ المطلوب
    
    Returns:
        DataFrame مع عمود rs_rating
    """
    # 1. فلتر اليوم المطلوب
    day_data = df[df['date'] == date].copy()
    
    # 2. امسح الأسهم اللي مفيهاش rs_raw
    day_data = day_data.dropna(subset=['rs_raw'])
    
    # 3. احسب الـ Percentile Rank
    day_data['rs_rating'] = (
        day_data['rs_raw']
        .rank(pct=True)  # حول لـ Percentile (0 to 1)
        .mul(100)        # اضرب في 100 (0 to 100)
        .round(0)        # قرب لأقرب رقم صحيح
        .clip(upper=99)  # الحد الأقصى 99
        .astype(int)
    )
    
    return day_data

# مثال:
df_with_rs = calculate_rs_rating(df, date.today())
```

---

## **الخطوة 4️⃣: الكود الكامل (All in One)**

```python
import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text

def calculate_daily_rs(db_url, target_date=None):
    """
    حساب RS لكل الأسهم في يوم معين
    """
    if not target_date:
        target_date = pd.Timestamp.today().date()
    
    # 1. جلب البيانات من الـ DB
    engine = create_engine(db_url)
    
    # نحتاج بيانات آخر سنة عشان نحسب الفترات
    one_year_ago = target_date - relativedelta(years=1)
    
    query = text("""
        SELECT symbol, date, close, company_name
        FROM prices
        WHERE date >= :start_date AND date <= :end_date
        ORDER BY symbol, date
    """)
    
    df = pd.read_sql(query, engine, params={
        'start_date': one_year_ago,
        'end_date': target_date
    })
    
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # 2. حساب Change % لكل فترة
    results = []
    
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol]
        
        # جيب بيانات اليوم الحالي
        current_row = symbol_data[symbol_data['date'] == target_date]
        if current_row.empty:
            continue
        
        current_price = current_row.iloc[0]['close']
        company_name = current_row.iloc[0]['company_name']
        
        # حساب Change % لكل فترة
        changes = {}
        for months in [3, 6, 9, 12]:
            past_date = target_date - relativedelta(months=months)
            past_data = symbol_data[symbol_data['date'] <= past_date]
            
            if not past_data.empty:
                past_price = past_data.iloc[-1]['close']
                if past_price and past_price > 0:
                    changes[f'change_{months}m'] = (current_price - past_price) / past_price
                else:
                    changes[f'change_{months}m'] = None
            else:
                changes[f'change_{months}m'] = None
        
        # حساب RS Raw
        if all(changes.values()):
            rs_raw = (
                (changes['change_3m'] * 0.4) +
                (changes['change_6m'] * 0.2) +
                (changes['change_9m'] * 0.2) +
                (changes['change_12m'] * 0.2)
            )
        else:
            rs_raw = None
        
        results.append({
            'symbol': symbol,
            'company_name': company_name,
            'date': target_date,
            'close': current_price,
            'change_3m': changes['change_3m'],
            'change_6m': changes['change_6m'],
            'change_9m': changes['change_9m'],
            'change_12m': changes['change_12m'],
            'rs_raw': rs_raw
        })
    
    # 3. تحويل لـ DataFrame
    results_df = pd.DataFrame(results)
    
    # 4. حساب RS Rating (Percentile Rank)
    valid_rs = results_df.dropna(subset=['rs_raw'])
    
    if not valid_rs.empty:
        results_df.loc[valid_rs.index, 'rs_rating'] = (
            valid_rs['rs_raw']
            .rank(pct=True)
            .mul(100)
            .round(0)
            .clip(upper=99)
            .astype(int)
        )
    
    # 5. حساب Ranks لكل فترة (للعرض)
    for period in ['3m', '6m', '9m', '12m']:
        col = f'change_{period}'
        valid_data = results_df.dropna(subset=[col])
        
        if not valid_data.empty:
            results_df.loc[valid_data.index, f'rank_{period}'] = (
                valid_data[col]
                .rank(pct=True)
                .mul(100)
                .round(0)
                .clip(upper=99)
                .astype(int)
            )
    
    return results_df

# استخدام
df_rs = calculate_daily_rs("postgresql://...")
print(df_rs.head())
```

---

## 📊 **ملخص الخطوات:**

| الخطوة | المدخل | المخرج | المعادلة |
|--------|--------|--------|----------|
| **1** | `close` (اليوم + قبل X شهور) | `change_%` | `(current - past) / past` |
| **2** | `change_3m, 6m, 9m, 12m` | `rs_raw` | `(3m×0.4) + (6m×0.2) + (9m×0.2) + (12m×0.2)` |
| **3** | `rs_raw` (كل الأسهم) | `rs_rating` | `percentile_rank(rs_raw) × 100` |

---

# 🚀 **التحسينات المقترحة**

## **1. استخدم Adjusted Close (مش Regular Close)**

### **المشكلة:**
- لو شركة عملت **توزيعات أرباح** أو **تجزئة أسهم**، السعر هينزل فجأة.
- ده هيخلي الـ RS يطلع غلط.

**مثال:**
- سهم سعره 100 ريال
- الشركة عملت توزيعات 10 ريال
- السعر نزل لـ 90 ريال (بس القيمة الحقيقية ما تغيرتش)
- لو حسبت RS بالـ Close العادي، هيطلع إن السهم نزل 10%! ❌

### **الحل:**

**احسب Adjusted Close:**

```python
def calculate_adjusted_close(df):
    """
    حساب Adjusted Close بناءً على التوزيعات والتجزئة
    """
    df = df.sort_values(['symbol', 'date'])
    
    # لو عندك جدول للتوزيعات
    dividends = pd.read_sql("SELECT * FROM dividends", engine)
    
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol].copy()
        symbol_divs = dividends[dividends['symbol'] == symbol]
        
        # ابدأ من آخر يوم ورجع للوراء
        adjustment_factor = 1.0
        
        for idx in reversed(symbol_data.index):
            row = symbol_data.loc[idx]
            
            # لو في توزيعات في اليوم ده
            div_row = symbol_divs[symbol_divs['date'] == row['date']]
            if not div_row.empty:
                dividend = div_row.iloc[0]['amount']
                adjustment_factor *= (row['close'] / (row['close'] + dividend))
            
            # احسب Adjusted Close
            df.loc[idx, 'adjusted_close'] = row['close'] * adjustment_factor
    
    return df
```

**أو استخدم مصدر خارجي:**

```python
import yfinance as yf

# جيب Adjusted Close من Yahoo Finance
ticker = yf.Ticker("1120.SR")  # الراجحي
hist = ticker.history(period="1y")
adjusted_close = hist['Close']  # ده Adjusted Close جاهز
```

---

## **2. أضف Index على الأعمدة المهمة**

### **المشكلة:**
- الـ Query بطيء لما تجيب بيانات سنة كاملة

### **الحل:**

```sql
-- عشان الـ Query يكون أسرع
CREATE INDEX idx_prices_symbol_date ON prices(symbol, date);
CREATE INDEX idx_rs_daily_symbol_date ON rs_daily(symbol, date);

-- لو بتفلتر بالـ date كتير
CREATE INDEX idx_prices_date ON prices(date);
```

**الفرق:**
- بدون Index: 10 ثواني ⏱️
- مع Index: 0.5 ثانية ⚡

---

## **3. احفظ الـ Change % في الـ Database**

### **المشكلة:**
- بتحسب Change % كل مرة من الصفر
- ده بطيء جداً لو عندك 900,000 سجل

### **الحل:**

**أضف أعمدة للـ Change %:**

```sql
ALTER TABLE prices ADD COLUMN change_3m DECIMAL(10, 4);
ALTER TABLE prices ADD COLUMN change_6m DECIMAL(10, 4);
ALTER TABLE prices ADD COLUMN change_9m DECIMAL(10, 4);
ALTER TABLE prices ADD COLUMN change_12m DECIMAL(10, 4);
```

**احسبها مرة واحدة واحفظها:**

```python
def update_change_columns(db_url):
    """
    حساب وحفظ Change % لكل الأيام
    """
    engine = create_engine(db_url)
    df = pd.read_sql("SELECT * FROM prices ORDER BY symbol, date", engine)
    
    # حساب Change % (نفس الطريقة اللي فوق)
    # ...
    
    # حفظ في الـ DB
    df.to_sql('prices', engine, if_exists='replace', index=False)
```

**الفايدة:**
- الـ RS Calculation هيبقى **10x أسرع**!

---

## **4. اعمل Incremental Update (مش Full Recalculation)**

### **المشكلة:**
- كل يوم بتحسب RS لكل التاريخ (من 2002 لـ 2025)
- ده waste للوقت والموارد

### **الحل:**

**احسب RS لليوم الحالي بس:**

```python
def calculate_rs_for_today_only(db_url, target_date=None):
    """
    حساب RS لليوم الحالي فقط (مش كل التاريخ)
    """
    if not target_date:
        target_date = datetime.date.today()
    
    # جيب بيانات اليوم + آخر سنة (عشان تحسب الفترات)
    one_year_ago = target_date - relativedelta(years=1)
    
    query = text("""
        SELECT * FROM prices
        WHERE date >= :start_date AND date <= :end_date
    """)
    
    df = pd.read_sql(query, engine, params={
        'start_date': one_year_ago,
        'end_date': target_date
    })
    
    # حساب RS لليوم الحالي بس
    # ...
    
    # حفظ في rs_daily
    results.to_sql('rs_daily', engine, if_exists='append', index=False)
```

**الفرق:**
- Full Recalculation: 5 دقايق ⏱️
- Incremental Update: 10 ثواني ⚡

---

## **5. اعمل Validation على البيانات**

### **المشكلة:**
- ممكن يكون في بيانات غلط (أسعار = 0، Outliers، إلخ)

### **الحل:**

```python
def validate_and_clean_data(df):
    """
    تنظيف البيانات قبل حساب RS
    """
    # 1. امسح الأسعار الصفر
    df = df[df['close'] > 0]
    
    # 2. امسح الأيام اللي مفيهاش تداول
    df = df[df['volume'] > 100]
    
    # 3. امسح الـ Outliers (أسعار شاذة)
    # لو السعر اتغير أكتر من 50% في يوم واحد، ده غالباً خطأ
    df['daily_change'] = df.groupby('symbol')['close'].pct_change()
    df = df[df['daily_change'].abs() < 0.5]
    
    return df
```

---

## **6. اعمل Caching للنتائج**

### **المشكلة:**
- كل مستخدم بيفتح الموقع، بتعمل Query للـ DB
- ده بطيء ومكلف

### **الحل:**

**استخدم Redis للـ Caching:**

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_rs_data(symbol, date):
    """
    جيب RS من الـ Cache أو الـ DB
    """
    # 1. جرب تجيب من الـ Cache
    cache_key = f"rs:{symbol}:{date}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # 2. لو مش موجود، جيب من الـ DB
    data = db.query(RSDaily).filter_by(symbol=symbol, date=date).first()
    
    # 3. احفظ في الـ Cache (لمدة يوم)
    redis_client.setex(
        cache_key,
        86400,  # 24 ساعة
        json.dumps(data)
    )
    
    return data
```

**الفرق:**
- بدون Cache: 100ms ⏱️
- مع Cache: 5ms ⚡ (20x أسرع!)

---

## 📊 **المقارنة النهائية:**

| الميزة | قبل التحسينات | بعد التحسينات |
|--------|---------------|----------------|
| **سرعة الحساب** | 5 دقايق | 10 ثواني |
| **دقة البيانات** | ⚠️ متوسطة | ✅ عالية |
| **سرعة الموقع** | 100ms | 5ms |
| **استهلاك الموارد** | عالي | منخفض |

---

## ✅ **خطة التنفيذ المقترحة:**

### **المرحلة 1: الأساسيات (أسبوع 1)**
1. ✅ تصحيح طريقة الحساب (Calendar Months)
2. ✅ إضافة Indexes
3. ✅ Data Validation

### **المرحلة 2: التحسينات (أسبوع 2)**
4. ⏳ Adjusted Close
5. ⏳ حفظ Change % في الـ DB
6. ⏳ Incremental Updates

### **المرحلة 3: الأداء (أسبوع 3)**
7. ⏳ Redis Caching
8. ⏳ Query Optimization
9. ⏳ Monitoring & Alerts

---

## 🎯 **الخلاصة:**

**الأولويات:**
1. ✅ **صحح طريقة الحساب** (Calendar Months + RS من Returns)
2. ✅ **أضف Indexes** (سهلة وسريعة)
3. ⏳ **Incremental Updates** (توفر وقت كتير)
4. ⏳ **Adjusted Close** (دقة أعلى)
5. ⏳ **Caching** (سرعة أكبر)

**ابدأ بالأولويات الأولى، وبعدين كمل الباقي! 🚀**
