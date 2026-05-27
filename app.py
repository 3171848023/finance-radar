import streamlit as st
import feedparser
import re
import socket
import concurrent.futures
from datetime import datetime, timedelta

# ==================== 🛠️ 页面配置与性能设置 ====================
socket.setdefaulttimeout(5)  # 强制超时机制，防止源卡死
st.set_page_config(page_title="金融投研情报站", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .card { background: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #2563eb; 
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 16px; }
    .source-tag { background: #dbeafe; color: #1e40af; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .time-tag { color: #64748b; font-size: 11px; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# ==================== 🛠️ 数据处理函数 ====================
def clean_html(raw):
    return re.sub(r'<.*?>', '', raw).strip()[:200] if raw else "暂无描述..."

def fetch_source(name, url, keywords, days_limit):
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:40]: # 深度翻页，获取更多内容
            # 时间解析
            dt = datetime(*entry.get("published_parsed", [2026,1,1])[:6])
            if days_limit and dt < (datetime.now() - timedelta(days=days_limit)): continue
            
            # 关键词过滤逻辑：为空时不拦截，否则匹配标题或摘要
            text = (entry.title + entry.get("summary", "")).lower()
            if not keywords or any(kw.lower() in text for kw in keywords):
                items.append({
                    "source": name, "title": entry.title, "link": entry.link,
                    "time": dt.strftime("%m-%d %H:%M"),
                    "desc": clean_html(entry.get("summary", ""))
                })
        return items
    except: return []

# ==================== 🚀 页面布局 ====================
st.title("📈 金融投研情报站")
left, right = st.columns([1, 3])

with left:
    st.markdown("### 🛠 控制中心")
    q = st.text_input("搜索关键词：", placeholder="巴菲特 / 投资 / 成长史")
    t = st.selectbox("筛选时效：", ["不限", "24小时内", "3天内", "1周内"])
    run = st.button("🚀 极速深度检索", use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption("情报源：雪球精华、36氪、虎嗅、投资界、少数派等。")

with right:
    if run:
        kws = q.split()
        days = {"不限": None, "24小时内": 1, "3天内": 3, "1周内": 7}[t]
        sources = {
            "雪球精华": "https://xueqiu.com/feed/elite",
            "36氪": "https://36kr.com/feed",
            "虎嗅": "https://www.huxiu.com/rss/0.xml",
            "投资界": "https://www.pedaily.cn/rss/news.xml",
            "少数派": "https://sspai.com/feed"
        }
        
        with st.spinner("正在从全网金融源中挖掘情报..."):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(fetch_source, n, u, kws, days) for n, u in sources.items()]
                all_res = []
                for f in concurrent.futures.as_completed(futures): all_res.extend(f.result())
        
        # 去重与排序
        all_res = {item['link']: item for item in all_res}.values()
        sorted_res = sorted(all_res, key=lambda x: x['time'], reverse=True)
        
        if not sorted_res: st.warning("未检索到相关内容，请尝试更换关键词或放宽筛选条件。")
        else:
            for item in sorted_res:
                st.markdown(f"""
                <div class='card'>
                    <span class='source-tag'>{item['source']}</span> 
                    <span class='time-tag'>🕒 {item['time']}</span>
                    <h5 style='margin: 10px 0;'><a href="{item['link']}" target="_blank" style="text-decoration:none; color:#1e293b;">{item['title']}</a></h5>
                    <p style="font-size:13px; color:#475569;">{item['desc']}...</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("👈 请在左侧输入关键词，开始你的金融情报挖掘。")
