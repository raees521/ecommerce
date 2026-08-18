import streamlit as st
import pandas as pd
import sqlite3
import os

# Page Configuration
st.set_page_config(page_title="Advanced Ecommerce Analytics", layout="wide")

st.title("📊 Enterprise Business Intelligence Dashboard")
st.markdown("---")

# 1. Database Connection Engine (SQLite)
def get_connection():
    # Looks for ecommerce.db in the same directory as this script
    db_path = os.path.join(os.path.dirname(__file__), "ecommerce.db")
    return sqlite3.connect(db_path)

try:
    conn = get_connection()
    
    # ==========================================
    # SECTION 1: GLOBAL HIGH-LEVEL PERFORMANCE KPIs
    # ==========================================
    st.subheader("💵 Financial Performance Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    df_kpi = pd.read_sql(
        "SELECT COUNT(order_id) as total_orders, SUM(total_amount) as total_rev, AVG(total_amount) as aov FROM orders", 
        conn
    )
    
    # Calculate retention metric from DB (SQLite syntax)
    df_retention = pd.read_sql("""
        WITH counts AS (
            SELECT customer_id, COUNT(order_id) as o_count 
            FROM orders 
            GROUP BY customer_id
        )
        SELECT ROUND(100.0 * COUNT(CASE WHEN o_count > 1 THEN 1 END) / COUNT(*), 2) as rate 
        FROM counts
    """, conn)
    
    col1.metric("Total Net Revenue", f"${df_kpi['total_rev'].iloc[0]:,.2f}")
    col2.metric("Total Volume Orders", f"{df_kpi['total_orders'].iloc[0]}")
    col3.metric("Average Order Value (AOV)", f"${df_kpi['aov'].iloc[0]:,.2f}")
    col4.metric("Customer Retention Rate", f"{df_retention['rate'].iloc[0]:,.1f}%")
    
    st.markdown("---")

    # ==========================================
    # SECTION 2: TIME-SERIES AND GEOGRAPHIC RANKINGS
    # ==========================================
    left_chart_col, right_chart_col = st.columns(2)
    
    with left_chart_col:
        st.subheader("📈 Monthly Sales Volume Trends")
        # SQLite uses strftime instead of DATE_FORMAT
        revenue_query = """
            SELECT strftime('%Y-%m', order_date) AS order_month, SUM(total_amount) AS monthly_revenue
            FROM orders GROUP BY order_month ORDER BY order_month;
        """
        df_rev = pd.read_sql(revenue_query, conn)
        st.line_chart(data=df_rev, x="order_month", y="monthly_revenue", color="#29b5e8")
        
    with right_chart_col:
        st.subheader("🌎 Net Profit Performance by Region")
        regional_query = """
            SELECT o.region, SUM(oi.quantity * (oi.unit_price - p.unit_cost)) AS margin_profit
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            GROUP BY o.region ORDER BY margin_profit DESC;
        """
        df_region = pd.read_sql(regional_query, conn)
        st.bar_chart(data=df_region, x="region", y="margin_profit", color="#1f77b4")

    st.markdown("---")

    # ==========================================
    # SECTION 3: USER SEGMENTATION (RFM DATA MODEL)
    # ==========================================
    st.subheader("👥 Dynamic Customer Segmentation (RFM Mapping)")
    
    rfm_query = """
        WITH rfm_summary AS (
            SELECT customer_id, COUNT(order_id) AS order_frequency, SUM(total_amount) AS total_spent
            FROM orders GROUP BY customer_id
        )
        SELECT 
            customer_id, order_frequency, total_spent,
            CASE 
                WHEN total_spent >= 250 THEN 'VIP High Spender'
                WHEN order_frequency >= 2 THEN 'Loyal Repeat Customer'
                ELSE 'Casual / Occasional Shopper'
            END AS customer_segment
        FROM rfm_summary ORDER BY total_spent DESC;
    """
    df_rfm = pd.read_sql(rfm_query, conn)
    
    col_rfm_chart, col_rfm_table = st.columns([1, 2])
    with col_rfm_chart:
        st.scatter_chart(data=df_rfm, x="order_frequency", y="total_spent", color="customer_segment")
    with col_rfm_table:
        st.dataframe(df_rfm, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # SECTION 4: PRODUCT MARGINS & DISCOUNT OPTIMIZATION
    # ==========================================
    st.subheader("🎯 Discount Threshold Optimization Analysis")
    
    discount_query = """
        SELECT 
            o.discount_amount AS discount_applied,
            COUNT(o.order_id) AS order_count,
            AVG(o.total_amount) AS current_aov,
            SUM(o.total_amount - (
                SELECT SUM(p.unit_cost * oi.quantity) 
                FROM order_items oi 
                JOIN products p ON oi.product_id = p.product_id 
                WHERE oi.order_id = o.order_id
            )) AS actual_net_profit
        FROM orders o
        GROUP BY o.discount_amount
        ORDER BY o.discount_amount ASC;
    """
    df_discount = pd.read_sql(discount_query, conn)
    
    col_disc_chart, col_disc_table = st.columns([2, 1])
    with col_disc_chart:
        st.bar_chart(data=df_discount, x="discount_applied", y="actual_net_profit", color="#ff7f0e")
    with col_disc_table:
        st.dataframe(df_discount, use_container_width=True)
        st.caption("Insight: Deep discounts increase total gross scale volume, but middle-tier margins preserve net return ceilings.")

    conn.close()

except Exception as e:
    st.error(f"❌ Database Query Error: {e}")
