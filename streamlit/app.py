import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import pandas as pd

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Service User Registry",
    page_icon="🔐",
    layout="wide"
)

# ── snowflake session ─────────────────────────────────────────────────────────
session = get_active_session()
root    = Root(session)
svc     = (root
           .databases["DB"]
           .schemas["SCHEMA"]
           .cortex_search_services["S7_CPDP_USER_SEARCH_CS"])

# ── urgency colour map ────────────────────────────────────────────────────────
URGENCY_COLOUR = {
    "OVERDUE":          "#7f1d1d",
    "CRITICAL":         "#b91c1c",
    "HIGH":             "#c2410c",
    "MEDIUM":           "#b45309",
    "OK":               "#166534",
    "NO RSA":           "#1e3a5f",
    "NEVER CONFIGURED": "#4c1d95",
}

STATUS_COLOUR = {
    "ACTIVE":   "#166534",
    "DISABLED": "#6b7280",
    "LOCKED":   "#b91c1c",
}

def badge(label: str, colour: str) -> str:
    return (
        f'<span style="background:{colour}20;color:{colour};'
        f'border:1px solid {colour}40;border-radius:4px;'
        f'padding:2px 8px;font-size:12px;font-weight:600">'
        f'{label}</span>'
    )

# ── header ────────────────────────────────────────────────────────────────────
st.title("🔐 Service User Registry")
st.caption("Read-only view powered by Cortex Search — search by user name, app, team, or describe what you're looking for.")

# ── summary metrics (always shown, no search needed) ─────────────────────────
@st.cache_data(ttl=3600)
def load_summary():
    return session.sql("""
        SELECT
            COUNT(*)                                             AS TOTAL,
            SUM(IFF(ACCOUNT_STATUS='ACTIVE',   1, 0))           AS ACTIVE,
            SUM(IFF(ACCOUNT_STATUS='DISABLED', 1, 0))           AS DISABLED,
            SUM(IFF(ACCOUNT_STATUS='LOCKED',   1, 0))           AS LOCKED,
            SUM(IFF(has_rsa_public_key,            1, 0))           AS RSA_ENABLED,
            SUM(IFF(URGENCY_LEVEL IN ('OVERDUE','CRITICAL'),1,0)) AS URGENT_RSA,
            SUM(IFF(PASSWORD_LAST_SET_TIME IS NULL, 1, 0))      AS PWD_NEVER_SET
        FROM EDW_DEV.STG.S6_CPDP_SERVICE_USER_SEARCH
    """).to_pandas().iloc[0]

s = load_summary()
c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
c1.metric("Total users",      int(s["TOTAL"]))
c2.metric("Active",           int(s["ACTIVE"]))
c3.metric("Disabled",         int(s["DISABLED"]))
c4.metric("Locked",           int(s["LOCKED"]))
c5.metric("RSA enabled",      int(s["RSA_ENABLED"]))
c6.metric("⚠ RSA urgent",     int(s["URGENT_RSA"]))
c7.metric("Pwd never set",    int(s["PWD_NEVER_SET"]))

st.divider()

# ── search + filters ──────────────────────────────────────────────────────────
col_search, col_env, col_team, col_status, col_rsa, col_urgency = st.columns([3,1,1,1,1,1])

with col_search:
    query = st.text_input("🔍 Search", placeholder="e.g. Power BI analytics, RSA overdue, ADF production...")
with col_env:
    env_filter = st.selectbox("Environment", ["All","PROD","PPD","DEV","CLONE"])
with col_team:
    team_filter = st.selectbox("Team", ["All","Data Engineering","Analytics","Platform"])
with col_status:
    status_filter = st.selectbox("Status", ["All","ACTIVE","DISABLED","LOCKED"])
with col_rsa:
    rsa_filter = st.selectbox("RSA", ["All","Enabled","Disabled"])
with col_urgency:
    urgency_filter = st.selectbox("RSA urgency", ["All","OVERDUE","CRITICAL","HIGH","MEDIUM","OK"])

# ── build cortex search filter ────────────────────────────────────────────────
def build_filter(env, team, status, rsa, urgency):
    clauses = []
    if env     != "All": clauses.append({"@eq": {"ENV":            env}})
    if status  != "All": clauses.append({"@eq": {"ACCOUNT_STATUS": status}})
    if urgency != "All": clauses.append({"@eq": {"URGENCY_LEVEL":    urgency}})
    if rsa == "Enabled":  clauses.append({"@eq": {"has_rsa_public_key": True}})
    if rsa == "Disabled": clauses.append({"@eq": {"has_rsa_public_key": False}})
    if not clauses:
        return None
    return {"@and": clauses} if len(clauses) > 1 else clauses[0]

# ── execute search ─────────────────────────────────────────────────────────────
search_query = query.strip() if query.strip() else "service user"

response = svc.search(
    query   = search_query,
    columns = [
        "SERVICE_USER_NAME","ENV",
        "EMAIL","APPLICATION_NAME","ACCOUNT_STATUS",
        "has_rsa_public_key",
        "URGENCY_LEVEL","PASSWORD_LAST_SET_TIME","PWD_DAYS_UNTIL_EXPIRY",
        "created_on"
    ],
    filter  = build_filter(env_filter, team_filter, status_filter, rsa_filter, urgency_filter),
    limit   = 25
)

results = response.results

# ── result count ──────────────────────────────────────────────────────────────
st.markdown(f"**{len(results)} result(s)** found")

if not results:
    st.info("No matching service users found. Try broadening your search or clearing filters.")
    st.stop()

# ── render results as cards ───────────────────────────────────────────────────
for r in results:
    urgency      = r.get("URGENCY_LEVEL", "NO RSA")
    status_val   = r.get("ACCOUNT_STATUS", "")
    urg_col      = URGENCY_COLOUR.get(urgency, "#888")
    stat_col     = STATUS_COLOUR.get(status_val, "#888")
    rsa_on       = r.get("has_rsa_public_key", False)
    days_pwd     = r.get("PWD_DAYS_UNTIL_EXPIRY")
	expiry_dt    = r.get("RSA_EXPIRY_DATE", "—")

    with st.container(border=True):
        left, right = st.columns([3, 1])

        with left:
            st.markdown(
                f"### `{r['SERVICE_USER_NAME']}`&nbsp;&nbsp;"
                + badge(status_val,  stat_col) + "&nbsp;"
                + badge(r.get("ENV",""), "#1e40af")
                + "&nbsp;" + badge(urgency, urg_col),
                unsafe_allow_html=True
            )
            st.markdown(
                f"**App:** {r.get('APPLICATION_NAME','—')} &nbsp;|&nbsp; "
                f"**Contact:** {r.get('EMAIL','—')}"
            )
           
        with right:
            st.markdown("**RSA key**")
            if rsa_on:
                st.markdown(
                    f"Created: `{r.get('PASSWORD_LAST_SET_TIME','—')}`  \n"
                    f"Expires: `{expiry_dt}`  \n"
                    + badge(urgency, urg_col),
                    unsafe_allow_html=True
                )
            else:
                st.markdown("*Not configured*")

            st.markdown("**Password**")
            pwd_raw = r.get("PASSWORD_LAST_SET_TIME")
            if pwd_raw:
                days_label = (
                    f"⚠ {abs(days_pwd)}d overdue" if days_pwd is not None and days_pwd < 0
                    else f"{days_pwd}d remaining" if days_pwd is not None
                    else "—"
                )
                st.markdown(f"Last set: `{str(pwd_raw)[:10]}`  \n{days_label}")
            else:
                st.markdown(badge("Never set", "#7c3aed"), unsafe_allow_html=True)

        st.markdown(f"<small>Created: {r.get('CREATED_ON','—')}</small>", unsafe_allow_html=True)

# ── footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Read-only app · Cortex Search · DB.SCHEMA · Refreshed every hour")
