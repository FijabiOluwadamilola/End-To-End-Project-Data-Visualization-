import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Retail Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_csv("cleaned_online_retail.csv")

    # Convert InvoiceDate to datetime
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Extract date and time information
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["Dayname"] = df["InvoiceDate"].dt.day_name()
    df["Monthname"] = df["InvoiceDate"].dt.month_name()
    df["Hour"] = df["InvoiceDate"].dt.hour

    # Create YearMonth
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    # Convert CustomerID to string
    df["CustomerID"] = df["CustomerID"].astype(str)

    # Create Revenue
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    return df


# =========================================================
# CUSTOMER CLASSIFICATION
# =========================================================

def classify_customer(revenue):

    if revenue >= 10000:
        return "High Value Customer"

    elif revenue >= 5000:
        return "Medium Value Customer"

    else:
        return "Low Value Customer"


# =========================================================
# LOAD DATA
# =========================================================

df = load_data()


# =========================================================
# HEADER
# =========================================================

st.title("📊 Retail Intelligence Dashboard")

st.write(
    "Sales, customers, and product performance analysis"
)

st.divider()


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Sales Analysis",
        "Customer Analysis",
        "Product Analysis",
        "Time Intelligence",
        "Data Explorer"
    ]
)


# =========================================================
# SIDEBAR COUNTRY FILTER
# =========================================================

countries = ["ALL"] + sorted(
    df["Country"].dropna().unique().tolist()
)

selected_country = st.sidebar.selectbox(
    "Country",
    countries
)


# =========================================================
# APPLY FILTER
# =========================================================

filtered_df = df.copy()

if selected_country != "ALL":

    filtered_df = filtered_df[
        filtered_df["Country"] == selected_country
    ]


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    st.header("Sales Overview")

    total_revenue = filtered_df["Revenue"].sum()
    total_orders = filtered_df["InvoiceNo"].nunique()
    total_customers = filtered_df["CustomerID"].nunique()
    total_products = filtered_df["StockCode"].nunique()
    total_quantity = filtered_df["Quantity"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Revenue",
            f"${total_revenue:,.0f}"
        )

    with col2:
        st.metric(
            "Total Orders",
            f"{total_orders:,}"
        )

    with col3:
        st.metric(
            "Total Customers",
            f"{total_customers:,}"
        )

    with col4:
        st.metric(
            "Total Products",
            f"{total_products:,}"
        )

    with col5:
        st.metric(
            "Total Quantity",
            f"{total_quantity:,}"
        )

    st.divider()

    # Monthly revenue
    monthly_revenue = (
        filtered_df
        .groupby("YearMonth")["Revenue"]
        .sum()
        .reset_index()
    )

    fig = px.area(
        monthly_revenue,
        x="YearMonth",
        y="Revenue",
        title="Monthly Revenue Trend",
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# SALES ANALYSIS
# =========================================================

elif page == "Sales Analysis":

    st.header("Sales Analysis")

    # Revenue by country
    country_sales = (
        filtered_df
        .groupby("Country")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig_country = px.bar(
        country_sales,
        x="Revenue",
        y="Country",
        orientation="h",
        title="Top 10 Countries by Revenue"
    )

    fig_country.update_layout(
        yaxis={
            "categoryorder": "total ascending"
        }
    )

    st.plotly_chart(
        fig_country,
        use_container_width=True
    )

    # Revenue by product
    product_revenue = (
        filtered_df
        .groupby("Description")
        .agg(
            Revenue=("Revenue", "sum"),
            Quantity=("Quantity", "sum")
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(10)
        .reset_index()
    )

    fig_product = px.bar(
        product_revenue,
        x="Revenue",
        y="Description",
        orientation="h",
        title="Top 10 Products by Revenue"
    )

    fig_product.update_layout(
        yaxis={
            "categoryorder": "total ascending"
        }
    )

    st.plotly_chart(
        fig_product,
        use_container_width=True
    )


# =========================================================
# CUSTOMER ANALYSIS
# =========================================================

elif page == "Customer Analysis":

    st.header("Customer Analysis")

    customer_revenue = (
        filtered_df
        .groupby("CustomerID")["Revenue"]
        .sum()
        .reset_index()
    )

    customer_revenue["CustomerType"] = (
        customer_revenue["Revenue"]
        .apply(classify_customer)
    )

    customer_count = (
        customer_revenue["CustomerType"]
        .value_counts()
        .reset_index()
    )

    customer_count.columns = [
        "CustomerType",
        "Count"
    ]

    fig = px.bar(
        customer_count,
        x="CustomerType",
        y="Count",
        title="Customer Value Segmentation"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("Top Customers")

    top_customers = (
        customer_revenue
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(10)
    )

    st.dataframe(
        top_customers,
        use_container_width=True
    )


# =========================================================
# PRODUCT ANALYSIS
# =========================================================

elif page == "Product Analysis":

    st.header("Product Performance")

    product = (
        filtered_df
        .groupby("Description")
        .agg(
            Revenue=("Revenue", "sum"),
            UnitsSold=("Quantity", "sum"),
            Orders=("InvoiceNo", "nunique"),
            AveragePrice=("UnitPrice", "mean")
        )
        .reset_index()
    )

    metric = st.selectbox(
        "Rank products by",
        [
            "Revenue",
            "UnitsSold",
            "Orders",
            "AveragePrice"
        ]
    )

    top_products = (
        product
        .sort_values(
            metric,
            ascending=False
        )
        .head(10)
    )

    fig = px.bar(
        top_products,
        x=metric,
        y="Description",
        orientation="h",
        title=f"Top Products by {metric}"
    )

    fig.update_layout(
        yaxis={
            "categoryorder": "total ascending"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# TIME INTELLIGENCE
# =========================================================

elif page == "Time Intelligence":

    st.header("Time Intelligence")

    hourly_sales = (
        filtered_df
        .groupby("Hour")["Revenue"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        hourly_sales,
        x="Hour",
        y="Revenue",
        markers=True,
        title="Revenue by Hour"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    monthly_sales = (
        filtered_df
        .groupby("Monthname")["Revenue"]
        .sum()
        .reset_index()
    )

    fig2 = px.bar(
        monthly_sales,
        x="Monthname",
        y="Revenue",
        title="Revenue by Month"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# =========================================================
# DATA EXPLORER
# =========================================================

elif page == "Data Explorer":

    st.header("Data Explorer")

    st.write(
        f"Showing {len(filtered_df):,} records"
    )

    st.dataframe(
        filtered_df,
        use_container_width=True
    )