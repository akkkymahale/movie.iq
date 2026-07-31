"""
Retail Banking Insights — Streamlit dashboard

Run locally:
    streamlit run app.py
"""

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = "data"

st.set_page_config(page_title="Retail Banking Insights", page_icon="🏦", layout="wide")
sns.set_theme(style="whitegrid")


# ----------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
    accounts = pd.read_csv(os.path.join(DATA_DIR, "accounts.csv"))
    transactions = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"))
    loans = pd.read_csv(os.path.join(DATA_DIR, "loans.csv"))
    digital = pd.read_csv(os.path.join(DATA_DIR, "digital_activity.csv"))
    tickets = pd.read_csv(os.path.join(DATA_DIR, "service_tickets.csv"))

    # Light cleaning
    customers["Region"] = customers["Region"].astype(str).str.strip()
    customers["JoinDate"] = pd.to_datetime(customers["JoinDate"], errors="coerce")
    accounts["OpenDate"] = pd.to_datetime(accounts["OpenDate"], errors="coerce")
    accounts["IsDormant"] = accounts["IsDormant"].astype(str).str.lower() == "true"
    transactions["TransactionDate"] = pd.to_datetime(transactions["TransactionDate"], errors="coerce")
    loans["StartDate"] = pd.to_datetime(loans["StartDate"], errors="coerce")
    loans["DefaultFlag"] = loans["DefaultFlag"].astype(str).str.lower() == "true"
    tickets["RaisedDate"] = pd.to_datetime(tickets["RaisedDate"], errors="coerce")
    tickets["ResolvedDate"] = pd.to_datetime(tickets["ResolvedDate"], errors="coerce")

    return customers, accounts, transactions, loans, digital, tickets


customers, accounts, transactions, loans, digital, tickets = load_data()

# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.title("🏦 Filters")

regions = sorted(customers["Region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Region", options=regions, default=regions)

age_min, age_max = int(customers["Age"].min()), int(customers["Age"].max())
age_range = st.sidebar.slider("Age range", min_value=age_min, max_value=age_max, value=(age_min, age_max))

filtered_customers = customers[
    customers["Region"].isin(selected_regions)
    & customers["Age"].between(age_range[0], age_range[1])
]
customer_ids = filtered_customers["CustomerID"]

filtered_accounts = accounts[accounts["CustomerID"].isin(customer_ids)]
filtered_transactions = transactions[transactions["AccountID"].isin(filtered_accounts["AccountID"])]
filtered_loans = loans[loans["CustomerID"].isin(customer_ids)]
filtered_digital = digital[digital["CustomerID"].isin(customer_ids)]
filtered_tickets = tickets[tickets["CustomerID"].isin(customer_ids)]

st.sidebar.markdown(f"**{len(filtered_customers)}** customers match your filters (of {len(customers)} total)")

# ----------------------------------------------------------------------
# Header + KPIs
# ----------------------------------------------------------------------
st.title("🏦 Retail Banking Insights")
st.caption("Explore customers, accounts, transactions, loans, digital activity, and support tickets.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Customers", len(filtered_customers))
c2.metric("Accounts", len(filtered_accounts))
c3.metric("Avg. balance", f"₹{filtered_accounts['Balance'].mean():,.0f}" if len(filtered_accounts) else "N/A")
c4.metric("Open loans", len(filtered_loans))
c5.metric("Open tickets", int((filtered_tickets["ResolvedDate"].isna()).sum()))

st.divider()

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_overview, tab_accounts, tab_txn, tab_loans, tab_digital, tab_tickets, tab_data = st.tabs(
    ["📊 Overview", "💳 Accounts", "💸 Transactions", "🏠 Loans", "📱 Digital", "🎫 Tickets", "📄 Data"]
)

with tab_overview:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Customers per Region")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=filtered_customers, y="Region", order=filtered_customers["Region"].value_counts().index, ax=ax)
        st.pyplot(fig)
    with col2:
        st.subheader("Age Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(filtered_customers["Age"], bins=15, kde=True, ax=ax)
        st.pyplot(fig)

with tab_accounts:
    st.subheader("Account Types & Balances")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=filtered_accounts, y="AccountType", ax=ax)
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.boxplot(data=filtered_accounts, x="AccountType", y="Balance", ax=ax)
        ax.tick_params(axis="x", rotation=30)
        st.pyplot(fig)
    st.metric("Dormant accounts", int(filtered_accounts["IsDormant"].sum()))

with tab_txn:
    st.subheader("Transaction Trends")
    if len(filtered_transactions):
        monthly = (
            filtered_transactions.set_index("TransactionDate")
            .resample("ME")["Amount"]
            .sum()
        )
        fig, ax = plt.subplots(figsize=(10, 4))
        monthly.plot(ax=ax)
        ax.set_ylabel("Net amount")
        st.pyplot(fig)

        fig, ax = plt.subplots(figsize=(8, 4))
        sns.countplot(data=filtered_transactions, y="TransactionType", ax=ax)
        st.pyplot(fig)
    else:
        st.info("No transactions match the current filters.")

with tab_loans:
    st.subheader("Loan Portfolio")
    if len(filtered_loans):
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.countplot(data=filtered_loans, y="LoanType", ax=ax)
            st.pyplot(fig)
        with col2:
            default_rate = filtered_loans.groupby("LoanType")["DefaultFlag"].mean().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(x=default_rate.values, y=default_rate.index, ax=ax)
            ax.set_xlabel("Default rate")
            st.pyplot(fig)
    else:
        st.info("No loans match the current filters.")

with tab_digital:
    st.subheader("Digital Channel Usage")
    if len(filtered_digital):
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(
            data=filtered_digital.groupby("Channel")["LoginCount"].mean().reset_index(),
            x="LoginCount", y="Channel", ax=ax,
        )
        ax.set_xlabel("Avg. logins")
        st.pyplot(fig)
    else:
        st.info("No digital activity for the current filters.")

with tab_tickets:
    st.subheader("Support Tickets")
    if len(filtered_tickets):
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.countplot(data=filtered_tickets, y="IssueType", ax=ax)
            st.pyplot(fig)
        with col2:
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.countplot(data=filtered_tickets, y="SatisfactionRating", ax=ax)
            st.pyplot(fig)
    else:
        st.info("No tickets match the current filters.")

with tab_data:
    st.subheader("Filtered Customers")
    st.dataframe(filtered_customers, use_container_width=True)
    st.download_button(
        "Download filtered customers as CSV",
        data=filtered_customers.to_csv(index=False),
        file_name="filtered_customers.csv",
        mime="text/csv",
    )
