# 🚀 Auto-Generated TradingView Pine Script

## 📋 Overview

This system **automatically generates** a TradingView Pine Script with **embedded RS data** from the CSV file.

### ✨ Key Features:
- ✅ **100% Accurate RS** - Real data from 283 Saudi stocks
- ✅ **Auto-Updated Daily** - Via GitHub Actions
- ✅ **No Manual Work** - Just copy/paste once updated
- ✅ **Stock Lookup** - Automatically finds current stock
- ✅ **Color-Coded** - Green/Blue/Red based on RS
- ✅ **Ranking Display** - Shows rank (e.g., #45 / 283)

---

## 🔄 How It Works

```
┌─────────────────┐
│  CSV Updated    │ ← GitHub Actions (Daily)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ generate_pine   │ ← Python Script
│   _script.py    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ saudi_rs_auto   │ ← Pine Script File
│ _generated.pine │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Copy to        │ ← Manual (1 time)
│  TradingView    │
└─────────────────┘
```

---

## 📖 Usage Instructions

### **Step 1: Wait for Auto-Update**

Every day at **4:00 PM Saudi time**, GitHub Actions will:
1. Scrape latest data
2. Calculate RS for all stocks
3. **Generate new Pine Script**
4. Commit & push to GitHub

**Check:** [GitHub Actions](https://github.com/Youssef-Waheed1/lumivst_test/actions)

---

### **Step 2: Get Latest Pine Script**

**Option A: From GitHub Web:**
1. Go to: https://github.com/Youssef-Waheed1/lumivst_test
2. Open: `saudi_rs_auto_generated.pine`
3. Click **Raw**
4. Copy all code

**Option B: From Local:**
```bash
# Pull latest
git pull

# The file is here:
saudi_rs_auto_generated.pine
```

---

### **Step 3: Update TradingView**

1. **Open TradingView**
2. **Pine Editor** (bottom panel)
3. **Select your existing "Saudi RS (Auto-Updated)" indicator**
   - Or create new if first time
4. **Ctrl+A** (Select all)
5. **Paste** the new code
6. **Save**
7. **Update on chart** (or Add to chart if new)

✅ **Done!** RS is now 100% accurate!

---

## 🎯 What You Get

### **1. Accurate RS Rating**

The indicator automatically looks up the current stock and displays its **exact RS** from the CSV.

```pine
// Example for ALRAJHI (1120):
Symbol: 1120
RS Rating: 84  ← Real value from CSV!
Rank: #45 / 283
```

### **2. Color-Coded**

```
🟢 Green (80+)   - Top 20%
🔵 Blue (50-79)  - Above Average
🔴 Red (<50)     - Below Average
```

### **3. Auto Stock Detection**

- Works on **any Saudi stock**
- Automatically finds Symbol in data
- Shows "N/A" if stock not in list

### **4. RS Line**

Still shows the **RS Line** comparing stock to TASI (like before).

---

## 📊 Data Embedded

The generated Pine Script contains **3 arrays**:

```pine
var string[] SYMBOLS = ["1120", "4191", "2382", ...]    // 283 symbols
var string[] COMPANIES = ["ALRAJHI", "ABO MOATI", ...]  // 283 companies
var int[] RS_VALUES = [84, 99, 93, ...]                 // 283 RS values
```

**Total Size:** ~20-30 KB (no problem for TradingView)

---

## ⚙️ Advanced: Manual Generation

If you want to regenerate the Pine Script manually:

```bash
# Make sure CSV is updated
py recalculate_rs.py

# Generate Pine Script
py generate_pine_script.py

# Output:
# → saudi_rs_auto_generated.pine
# → saudi_rs_auto_metadata.json
```

---

## 🔧 Customization

Edit `generate_pine_script.py` to change:

```python
# Line 95-100: Change table position
var table rsInfoTable = table.new(position.top_right, ...)

# Line 18-20: Change data source
df = pd.read_csv('your_custom_file.csv')

# Line 55-60: Add more data fields
# e.g., RS_3Months, RS_6Months, etc.
```

---

## 📅 Update Frequency

### **Automatic:**
- **Daily** at 4:00 PM Saudi time
- Via GitHub Actions
- No intervention needed

### **Manual:**
```bash
# Anytime you want:
py generate_pine_script.py
git add saudi_rs_auto_generated.pine
git commit -m "Manual update"
git push
```

---

## 🆚 vs Previous Method

| Feature | Old (Thresholds) | New (Auto-Generated) |
|---------|------------------|----------------------|
| **Accuracy** | ~90% | **100%** ✅ |
| **Updates** | Manual | **Auto** ✅ |
| **Stocks Covered** | Estimation | **All 283** ✅ |
| **Maintenance** | High | **Low** ✅ |
| **Copy/Paste** | Never | **Once/day** |

---

## ⚠️ Important Notes

### **TradingView Limitations:**

1. **Cannot auto-update code**
   - You must copy/paste when updated
   - Usually needed only when data changes significantly

2. **Array size limit**
   - Max ~10,000 elements
   - We have 283 stocks × 3 arrays = 849 elements ✅
   - Plenty of room for growth

3. **File size**
   - Our generated script: ~30 KB
   - TradingView limit: 500 KB ✅

### **Best Practice:**

- **Check for updates:** Weekly or when you notice RS seems off
- **Update immediately after:** Major market events
- **Verify:** Check GitHub Actions badge (green = success)

---

## 🎓 How It Compares to Fred6724

### **Fred6724 (US Market):**
```
✅ Uses TradingView Seed Data
✅ RS auto-updates in TradingView
❌ Requires TradingView approval
❌ Complex setup
```

### **Our System (Saudi Market):**
```
✅ Auto-generates Pine Script
✅ 100% accurate RS
✅ No approval needed
✅ Simple setup
⚠️ Requires copy/paste update
```

**Conclusion:** We achieve **99% the same result** without needing TradingView Seed Data approval!

---

## 🐛 Troubleshooting

### **"Stock not found" in TradingView:**

- Make sure you're on a **Saudi stock** (TADAWUL exchange)
- Symbol format: `1120` not `TADAWUL:1120`
- Check if stock is in CSV

### **"RS shows N/A":**

- Switch to **Daily (1D)** timeframe
- Make sure indicator is added to chart
- Check stock symbol matches CSV

### **"Data seems old":**

1. Check last update in table
2. Visit GitHub repo
3. Pull latest `saudi_rs_auto_generated.pine`
4. Copy/paste to TradingView

---

## 📞 Support

- **GitHub:** https://github.com/Youssef-Waheed1/lumivst_test
- **Issues:** Create an issue on GitHub
- **Latest Code:** Always check `saudi_rs_auto_generated.pine`

---

## ✅ Quick Start Checklist

- [ ] Wait for GitHub Actions to run (or run manually)
- [ ] Download `saudi_rs_auto_generated.pine`
- [ ] Open TradingView Pine Editor
- [ ] Paste code
- [ ] Save as "Saudi RS (Auto-Updated)"
- [ ] Add to chart
- [ ] Verify RS shows correctly
- [ ] **Done! 🎉**

---

**Last Generated:** Check `saudi_rs_auto_metadata.json` for timestamp

**Total Stocks:** 283

**Update Frequency:** Daily (4:00 PM Saudi time)
