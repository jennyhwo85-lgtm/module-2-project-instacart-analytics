"""Interactive Streamlit dashboard on the findings from notebook/EDA_01.ipynb.

Reuses the same warehouse (fact_order_items, dim_departments, dim_products) and the
same SQL patterns as the notebook, parameterized so the "cuts" (top-N, minimum-order
floors) that the notebook hard-coded become sliders here.
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from scripts.util import db_connection  # noqa: E402

DB_PATH = ROOT_DIR / "warehouse" / "instacart.duckdb"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
MUTED = "#898781"
GRID = "#e1e0d9"
BLUE_SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]

st.set_page_config(page_title="Instacart Behavior Dashboard", page_icon="🛒", layout="wide")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

@st.cache_resource
def get_connection():
    return db_connection(str(DB_PATH), read_only=True)


try:
    db = get_connection()
except duckdb.IOException as exc:
    st.error(
        "Could not open the DuckDB warehouse at `warehouse/instacart.duckdb` (read-only). "
        "This usually means another process — e.g. a Jupyter kernel with the EDA notebook "
        "open — is holding a write lock on the file. Close that connection and rerun the app.\n\n"
        f"Details: {exc}"
    )
    st.stop()


# ---------------------------------------------------------------------------
# Query helpers (cached — reruns only refetch when their own parameters change)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_kpis():
    basket = db.sql("""
        with basket as (
            select order_id, count(*) as basket_size
            from fact_order_items
            group by order_id
        )
        select count(*) as n_orders, sum(basket_size) as n_items, avg(basket_size) as avg_basket_size
        from basket
    """).df().iloc[0]
    reorder_rate = db.sql("select avg(reordered) as r from fact_order_items").df()["r"].iloc[0]
    return {
        "n_orders": int(basket["n_orders"]),
        "n_items": int(basket["n_items"]),
        "avg_basket_size": float(basket["avg_basket_size"]),
        "reorder_rate": float(reorder_rate),
    }


@st.cache_data(show_spinner=False)
def load_department_counts():
    return db.sql("""
        select
            d.department_name,
            count(*) as item_count,
            sum(f.reordered) as reorder_count
        from fact_order_items f
        join dim_departments d on f.department_id = d.department_id
        group by d.department_name
        order by item_count desc
    """).df()


@st.cache_data(show_spinner=False)
def load_basket_by_dow():
    return db.sql("""
        with basket as (
            select order_id, order_dow, count(*) as basket_size
            from fact_order_items
            group by order_id, order_dow
        )
        select order_dow, avg(basket_size) as avg_basket_size, count(*) as order_count
        from basket
        group by order_dow
        order by order_dow
    """).df()


@st.cache_data(show_spinner=False)
def load_basket_by_hour():
    return db.sql("""
        with basket as (
            select order_id, order_hour_of_day, count(*) as basket_size
            from fact_order_items
            group by order_id, order_hour_of_day
        )
        select order_hour_of_day, avg(basket_size) as avg_basket_size, count(*) as order_count
        from basket
        group by order_hour_of_day
        order by order_hour_of_day
    """).df()


@st.cache_data(show_spinner=False)
def load_dept_dow_share(selected_departments: tuple):
    dept_filter = ""
    if selected_departments:
        dept_list_sql = ", ".join(f"'{d}'" for d in selected_departments)
        dept_filter = f"where d.department_name in ({dept_list_sql})"
    dept_dow = db.sql(f"""
        select
            d.department_name,
            f.order_dow,
            count(*) as item_count
        from fact_order_items f
        join dim_departments d on f.department_id = d.department_id
        {dept_filter}
        group by d.department_name, f.order_dow
    """).df()
    pivot = dept_dow.pivot(index="department_name", columns="order_dow", values="item_count").fillna(0)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    return pivot.div(pivot.sum(axis=1), axis=0) * 100


@st.cache_data(show_spinner=False)
def load_department_products(department_name: str, top_n: int):
    agg = db.sql(f"""
        select
            p.product_name,
            count(*) as item_count,
            sum(f.reordered) as reorder_count
        from fact_order_items f
        join dim_products p on f.product_id = p.product_id
        join dim_departments d on f.department_id = d.department_id
        where d.department_name = '{department_name}'
        group by p.product_name
    """).df()
    return agg.nlargest(top_n, "item_count"), agg.nlargest(top_n, "reorder_count")


@st.cache_data(show_spinner=False)
def load_dept_atc():
    df = db.sql("""
        select
            d.department_name,
            avg(f.add_to_cart_order) as avg_add_to_cart_order,
            count(*) as item_count
        from fact_order_items f
        join dim_departments d on f.department_id = d.department_id
        group by d.department_name
        order by avg_add_to_cart_order
    """).df()
    median = df["avg_add_to_cart_order"].median()
    df["group"] = df["avg_add_to_cart_order"].apply(lambda v: "Added earlier" if v <= median else "Added later")
    return df


@st.cache_data(show_spinner=False)
def load_product_atc(top_n: int):
    earliest = db.sql(f"""
        select p.product_name, avg(f.add_to_cart_order) as avg_add_to_cart_order, count(*) as item_count
        from fact_order_items f join dim_products p on f.product_id = p.product_id
        group by p.product_name order by avg_add_to_cart_order asc limit {top_n}
    """).df()
    latest = db.sql(f"""
        select p.product_name, avg(f.add_to_cart_order) as avg_add_to_cart_order, count(*) as item_count
        from fact_order_items f join dim_products p on f.product_id = p.product_id
        group by p.product_name order by avg_add_to_cart_order desc limit {top_n}
    """).df()
    earliest["group"] = "Earliest"
    latest["group"] = "Latest"
    return pd.concat([earliest, latest]).sort_values("avg_add_to_cart_order")


@st.cache_data(show_spinner=False)
def load_dept_days_since_prior():
    return db.sql("""
        select
            d.department_name,
            avg(f.days_since_prior_order) as avg_days_since_prior,
            count(*) as item_count
        from fact_order_items f
        join dim_departments d on f.department_id = d.department_id
        group by d.department_name
        order by avg_days_since_prior asc
    """).df()


@st.cache_data(show_spinner=False)
def load_product_days_since_prior_by_volume(top_n: int):
    return db.sql(f"""
        select
            p.product_name,
            count(*) as item_count,
            avg(f.days_since_prior_order) as avg_days_since_prior
        from fact_order_items f
        join dim_products p on f.product_id = p.product_id
        group by p.product_name
        order by item_count desc
        limit {top_n}
    """).df().sort_values("avg_days_since_prior")


@st.cache_data(show_spinner=False)
def load_product_days_since_prior_extremes(top_n: int, min_orders: int):
    bottom = db.sql(f"""
        select p.product_name, count(*) as item_count, avg(f.days_since_prior_order) as avg_days_since_prior
        from fact_order_items f join dim_products p on f.product_id = p.product_id
        group by p.product_name
        having count(*) >= {min_orders}
        order by avg_days_since_prior asc limit {top_n}
    """).df()
    top = db.sql(f"""
        select p.product_name, count(*) as item_count, avg(f.days_since_prior_order) as avg_days_since_prior
        from fact_order_items f join dim_products p on f.product_id = p.product_id
        group by p.product_name
        having count(*) >= {min_orders}
        order by avg_days_since_prior desc limit {top_n}
    """).df()
    bottom["group"] = "Shortest cycle"
    top["group"] = "Longest cycle"
    return pd.concat([bottom, top]).sort_values("avg_days_since_prior")


@st.cache_data(show_spinner=False)
def load_reorder_rate_extremes(top_n: int, min_orders: int):
    rates = db.sql(f"""
        select
            p.product_name,
            count(*) as total_count,
            sum(f.reordered) as reorder_count,
            avg(f.reordered) as reorder_rate
        from fact_order_items f
        join dim_products p on f.product_id = p.product_id
        group by p.product_name
        having count(*) >= {min_orders}
    """).df()
    top = rates.nlargest(top_n, "reorder_rate").copy()
    top["group"] = "Most rebought"
    bottom = rates.nsmallest(top_n, "reorder_rate").copy()
    bottom["group"] = "Least rebought"
    combined = pd.concat([top, bottom]).sort_values("reorder_rate")
    combined["reorder_rate_pct"] = combined["reorder_rate"] * 100
    return combined


# ---------------------------------------------------------------------------
# Chart helpers (Plotly — hover tooltips ship by default)
# ---------------------------------------------------------------------------

def bar_fig(x, y, color=BLUE, xlabel="", ylabel="", value_fmt=",.2f", height=420, tickangle=-45):
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=color,
        hovertemplate="%{x}<br><b>%{y:" + value_fmt + "}</b><extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=12),
        xaxis=dict(title=xlabel, tickangle=tickangle, showgrid=False),
        yaxis=dict(title=ylabel, gridcolor=GRID, zeroline=False),
        margin=dict(t=10, b=10, l=10, r=10),
        height=height,
        bargap=0.3,
    )
    return fig


def grouped_bar_fig(x, series: dict, colors: dict, xlabel="", ylabel="", height=460):
    fig = go.Figure()
    for name, values in series.items():
        fig.add_bar(
            x=x, y=values, name=name, marker_color=colors[name],
            hovertemplate="%{x}<br>" + name + ": <b>%{y:,.0f}</b><extra></extra>",
        )
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=12),
        xaxis=dict(title=xlabel, tickangle=-45, showgrid=False),
        yaxis=dict(title=ylabel, gridcolor=GRID, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=40, b=10, l=10, r=10),
        height=height,
        bargap=0.3,
    )
    return fig


def diverging_fig(df: pd.DataFrame, label_col: str, value_col: str, group_col: str,
                   color_map: dict, xlabel="", value_fmt=",.2f", height=None):
    order = df[label_col].tolist()
    height = height or max(320, 28 * len(order))
    fig = go.Figure()
    for group_name, color in color_map.items():
        sub = df[df[group_col] == group_name]
        if sub.empty:
            continue
        fig.add_bar(
            x=sub[value_col], y=sub[label_col], orientation="h",
            name=group_name, marker_color=color,
            hovertemplate="%{y}<br><b>%{x:" + value_fmt + "}</b><extra></extra>",
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=12),
        xaxis=dict(title=xlabel, showgrid=True, gridcolor=GRID, zeroline=False),
        yaxis=dict(categoryorder="array", categoryarray=order, autorange="reversed"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=40, b=10, l=10, r=10),
        height=height,
    )
    return fig


def heatmap_fig(pivot_df: pd.DataFrame, xlabel="", ylabel="", height=None):
    height = height or max(320, 28 * len(pivot_df))
    colorscale = [[i / (len(BLUE_SEQUENTIAL) - 1), c] for i, c in enumerate(BLUE_SEQUENTIAL)]
    fig = go.Figure(go.Heatmap(
        z=pivot_df.values,
        x=[str(c) for c in pivot_df.columns],
        y=pivot_df.index,
        colorscale=colorscale,
        hovertemplate="%{y}<br>day code %{x}<br><b>%{z:.1f}%</b><extra></extra>",
        colorbar=dict(title="% of dept's items", tickfont=dict(color=MUTED)),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=12),
        xaxis=dict(title=xlabel),
        yaxis=dict(title=ylabel, autorange="reversed"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=height,
    )
    return fig


def table_expander(df: pd.DataFrame, label="View data table"):
    with st.expander(label):
        st.dataframe(df, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🛒 Instacart Behavior")
    st.caption(
        "Interactive companion to `notebook/EDA_01.ipynb`. Same warehouse "
        "(`fact_order_items`), same SQL patterns — the notebook's hard-coded "
        "top-N and minimum-order cuts are sliders here."
    )
    st.divider()
    st.subheader("Ranking floor")
    min_orders = st.slider(
        "Minimum orders per product",
        min_value=100, max_value=5000, value=1000, step=100,
        help="Applies to every rate- or cadence-based product ranking below (days-since-prior "
             "extremes, % reordered extremes). Excludes low-volume products where one or two "
             "orders can swing the rate to a fake 0% or 100%.",
    )
    st.divider()
    st.caption(
        "**Data boundary:** this dataset has no prices, quantities, calendar dates, or "
        "customer demographics — every number here is a volume/behavior/timing metric, "
        "never revenue."
    )

# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------

st.title("Instacart Order & Reorder Behavior")

kpis = load_kpis()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total orders", f"{kpis['n_orders']:,}")
c2.metric("Total items ordered", f"{kpis['n_items']:,}")
c3.metric("Avg basket size", f"{kpis['avg_basket_size']:.2f} items")
c4.metric("Overall reorder rate", f"{kpis['reorder_rate'] * 100:.1f}%")

dept_counts = load_department_counts()
all_departments = dept_counts["department_name"].tolist()

tab_overview, tab_departments, tab_products = st.tabs(
    ["📦 Order Activity", "🏬 Departments", "🛍️ Products"]
)

# ---------------------------------------------------------------------------
# Tab 1 — Order Activity (when do people order, and how much)
# ---------------------------------------------------------------------------

with tab_overview:
    st.subheader("Basket size by day of week and by hour of day")
    st.caption(
        "No cut applied — the day-of-week and hour-of-day domains are fixed and small "
        "(7 codes, 24 hours), so every value is shown. Basket size = items per order."
    )
    col1, col2 = st.columns(2)
    with col1:
        bdow = load_basket_by_dow()
        st.plotly_chart(
            bar_fig(bdow["order_dow"], bdow["avg_basket_size"], color=BLUE,
                    xlabel="order_dow code (0-6, no official weekday mapping)",
                    ylabel="Avg items per order", tickangle=0),
            width="stretch",
        )
        table_expander(bdow)
    with col2:
        bhour = load_basket_by_hour()
        st.plotly_chart(
            bar_fig(bhour["order_hour_of_day"], bhour["avg_basket_size"], color=ORANGE,
                    xlabel="Hour of day (0-23)", ylabel="Avg items per order", tickangle=0),
            width="stretch",
        )
        table_expander(bhour)

    st.divider()
    st.subheader("Order volume by department and day of week — timing for a sale")
    st.caption(
        "**Data limitation:** `order_dow` is a numeric code (0–6); Instacart has not published "
        "a mapping to actual weekdays, so results are reported by code only. Each row is "
        "normalized to that department's own items, so departments compare on *pattern* "
        "regardless of size."
    )
    dept_filter_choice = st.multiselect(
        "Filter departments shown in the heatmap (leave empty for all ~21)",
        options=all_departments, default=[],
    )
    share = load_dept_dow_share(tuple(sorted(dept_filter_choice)))
    st.plotly_chart(
        heatmap_fig(share, xlabel="order_dow code (0-6, no official weekday mapping)",
                    ylabel="Department"),
        width="stretch",
    )
    table_expander(share.reset_index())

# ---------------------------------------------------------------------------
# Tab 2 — Departments
# ---------------------------------------------------------------------------

with tab_departments:
    st.subheader("All departments — items ordered vs. reordered")
    st.caption("No filtering — with only ~21 departments, every one fits on a single chart.")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            bar_fig(dept_counts["department_name"], dept_counts["item_count"], color=BLUE,
                    xlabel="Department", ylabel="Item count", value_fmt=",.0f"),
            width="stretch",
        )
    with col2:
        by_reorder = dept_counts.sort_values("reorder_count", ascending=False)
        st.plotly_chart(
            bar_fig(by_reorder["department_name"], by_reorder["reorder_count"], color=ORANGE,
                    xlabel="Department", ylabel="Reorder count", value_fmt=",.0f"),
            width="stretch",
        )
    table_expander(dept_counts)

    st.divider()
    st.subheader("Top N departments — ordered vs. reordered (clustered)")
    top_n_dept = st.slider("Number of departments", min_value=3, max_value=len(all_departments),
                            value=10, key="top_n_dept")
    st.caption(
        f"Cut to the top {top_n_dept} of ~21 departments by item count — two bars per department "
        "crowd the chart past that point, and the head end already captures most of the volume."
    )
    top_dept = dept_counts.head(top_n_dept)
    st.plotly_chart(
        grouped_bar_fig(
            top_dept["department_name"].tolist(),
            {"Items ordered": top_dept["item_count"].tolist(), "Items reordered": top_dept["reorder_count"].tolist()},
            colors={"Items ordered": BLUE, "Items reordered": ORANGE},
            xlabel="Department", ylabel="Item count",
        ),
        width="stretch",
    )
    table_expander(top_dept)

    st.divider()
    st.subheader("Drill into a department's top products")
    col1, col2 = st.columns([2, 1])
    with col1:
        chosen_dept = st.selectbox("Department", options=all_departments, index=0)
    with col2:
        top_n_products = st.slider("Products per chart", min_value=3, max_value=15, value=5)
    st.caption(
        "Pick any department (defaults to the highest-volume one) and see its own top products "
        "by item count and by reorder count — a live version of the notebook's fixed top-5-departments drill-down."
    )
    top_items, top_reordered = load_department_products(chosen_dept, top_n_products)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            bar_fig(top_items["product_name"], top_items["item_count"], color=BLUE,
                    xlabel="Product", ylabel="Item count", value_fmt=",.0f", tickangle=20),
            width="stretch",
        )
    with col2:
        st.plotly_chart(
            bar_fig(top_reordered["product_name"], top_reordered["reorder_count"], color=ORANGE,
                    xlabel="Product", ylabel="Reorder count", value_fmt=",.0f", tickangle=20),
            width="stretch",
        )

    st.divider()
    st.subheader("Add-to-cart timing by department")
    st.caption(
        "No cut — every department shown; a lower position means items from that department "
        "tend to be dropped into the basket earlier in the trip."
    )
    dept_atc = load_dept_atc()
    st.plotly_chart(
        diverging_fig(dept_atc, "department_name", "avg_add_to_cart_order", "group",
                      color_map={"Added earlier": BLUE, "Added later": ORANGE},
                      xlabel="Avg add-to-cart position"),
        width="stretch",
    )
    table_expander(dept_atc)

    st.divider()
    st.subheader("Average days since prior order, by department")
    st.caption("No cut — all ~21 departments shown. Lower = that department's buyers shop on a shorter cycle.")
    dept_days = load_dept_days_since_prior()
    st.plotly_chart(
        bar_fig(dept_days["department_name"], dept_days["avg_days_since_prior"], color=BLUE,
                xlabel="Department", ylabel="Avg days since prior order"),
        width="stretch",
    )
    table_expander(dept_days)

# ---------------------------------------------------------------------------
# Tab 3 — Products
# ---------------------------------------------------------------------------

with tab_products:
    st.subheader("Add-to-cart timing by product")
    top_n_atc = st.slider("Products per side (earliest / latest)", min_value=5, max_value=25, value=10)
    st.caption(
        f"Out of ~50k products, limited to the {top_n_atc} added earliest and {top_n_atc} added "
        "latest on average, to keep the chart readable."
    )
    product_atc = load_product_atc(top_n_atc)
    st.plotly_chart(
        diverging_fig(product_atc, "product_name", "avg_add_to_cart_order", "group",
                      color_map={"Earliest": BLUE, "Latest": ORANGE},
                      xlabel="Avg add-to-cart position"),
        width="stretch",
    )
    table_expander(product_atc)

    st.divider()
    st.subheader("Average days since prior order — top products by volume")
    top_n_volume = st.slider("Number of most-ordered products", min_value=5, max_value=40, value=20)
    st.caption(
        f"First cut: out of ~50k products, narrows to the {top_n_volume} with the highest raw "
        "item_count — asking whether popularity also comes with a tight repurchase cadence. "
        "No order-count floor needed since these are already the highest-volume products."
    )
    product_days_volume = load_product_days_since_prior_by_volume(top_n_volume)
    st.plotly_chart(
        bar_fig(product_days_volume["product_name"], product_days_volume["avg_days_since_prior"], color=ORANGE,
                xlabel="Product", ylabel="Avg days since prior order"),
        width="stretch",
    )
    table_expander(product_days_volume)

    st.divider()
    st.subheader("Shortest vs. longest repurchase cycle, by product")
    top_n_cadence = st.slider("Products per side (shortest / longest cycle)", min_value=5, max_value=40, value=20)
    st.caption(
        f"A different cut: ranks *all* products (with at least {min_orders:,} orders — set in the "
        f"sidebar) by average days since prior order and takes the {top_n_cadence} lowest and "
        f"{top_n_cadence} highest. Together these span the true min/max of the repurchase-cadence "
        "range — the volume-ranked chart above only covers its popularity-weighted middle."
    )
    days_extremes = load_product_days_since_prior_extremes(top_n_cadence, min_orders)
    st.plotly_chart(
        diverging_fig(days_extremes, "product_name", "avg_days_since_prior", "group",
                      color_map={"Shortest cycle": BLUE, "Longest cycle": ORANGE},
                      xlabel="Avg days since prior order"),
        width="stretch",
    )
    table_expander(days_extremes)

    st.divider()
    st.subheader("Top and bottom products by % reordered")
    top_n_reorder = st.slider("Products per side (most / least rebought)", min_value=3, max_value=15, value=5)
    st.caption(
        f"`% reordered = reorder_count / total_count`, restricted to products with at least "
        f"{min_orders:,} orders (sidebar) so the ranking isn't won by a couple of reorders on a "
        "low-volume product. Kept narrow since the extremes alone already tell the story."
    )
    reorder_extremes = load_reorder_rate_extremes(top_n_reorder, min_orders)
    st.plotly_chart(
        diverging_fig(reorder_extremes, "product_name", "reorder_rate_pct", "group",
                      color_map={"Most rebought": ORANGE, "Least rebought": BLUE},
                      xlabel="% reordered", value_fmt=".1f"),
        width="stretch",
    )
    table_expander(reorder_extremes[["product_name", "total_count", "reorder_count", "reorder_rate_pct", "group"]])
