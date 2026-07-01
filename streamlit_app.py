from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

import streamlit as st


MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


@dataclass(frozen=True)
class AgmRow:
    agm_num: int
    fy_end: date
    deadline: date
    is_current: bool
    is_first: bool


def format_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def add_months(value: date, months: int) -> date:
    total_months = value.month - 1 + months
    target_year = value.year + total_months // 12
    target_month = total_months % 12 + 1
    last_day = calendar.monthrange(target_year, target_month)[1]
    return date(target_year, target_month, min(value.day, last_day))


def get_first_fy_end(incorporation_date: date) -> date:
    return date(incorporation_date.year + 1, 3, 31)


def fy_label(fy_end: date) -> str:
    start_year = fy_end.year - 1
    return f"{start_year}-{str(fy_end.year)[-2:]}"


def current_fy_end_year(today: date) -> int:
    return today.year if today.month < 4 else today.year + 1


def build_agm_rows(incorporation_date: date, today: date) -> list[AgmRow]:
    rows: list[AgmRow] = []
    fy_end = get_first_fy_end(incorporation_date)
    last_fy_end = date(2031, 3, 31)
    agm_num = 1
    current_year = current_fy_end_year(today)

    while fy_end <= last_fy_end:
        rows.append(
            AgmRow(
                agm_num=agm_num,
                fy_end=fy_end,
                deadline=add_months(fy_end, 9 if agm_num == 1 else 6),
                is_current=fy_end.year == current_year,
                is_first=agm_num == 1,
            )
        )
        fy_end = date(fy_end.year + 1, 3, 31)
        agm_num += 1

    return rows


def render_metric(label: str, value: str) -> None:
    st.markdown(f"**{label}**")
    st.write(value)


st.set_page_config(page_title="AGM Calculator", page_icon="AGM", layout="wide")

st.title("AGM Calculator")
st.caption("Annual General Meeting schedule under the Companies Act, 2013 | Section 96")

with st.container(border=True):
    incorporation_date = st.date_input(
        "Date of Incorporation",
        value=date(2024, 4, 1),
        min_value=date(1956, 1, 1),
        max_value=date.today(),
    )
    calculate = st.button("Calculate AGMs", type="primary")

if calculate:
    rows = build_agm_rows(incorporation_date, date.today())
    first_row = rows[0]

    with st.container(border=True):
        st.subheader("Company Details")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            render_metric("Date of Incorporation", format_date(incorporation_date))
        with col2:
            render_metric("First Financial Year", fy_label(first_row.fy_end))
        with col3:
            render_metric("First FY Closes On", format_date(first_row.fy_end))
        with col4:
            render_metric("First AGM Deadline", format_date(first_row.deadline))
        with col5:
            render_metric("Total AGMs", str(len(rows)))

        st.warning(
            f"Year of Incorporation ({incorporation_date.year}): If the first AGM is held "
            f"on or before {format_date(first_row.deadline)}, the company is not required "
            f"to hold any AGM in {incorporation_date.year}."
        )

    table_rows = []
    for row in rows:
        agm_type = "1st AGM" if row.is_first else "Regular"
        if row.is_current:
            agm_type = f"{agm_type}; Current FY"
        table_rows.append(
            {
                "AGM No.": f"{ordinal(row.agm_num)} AGM",
                "Financial Year": fy_label(row.fy_end),
                "FY Closes On": format_date(row.fy_end),
                "Basis": "9 months from FY end" if row.is_first else "6 months from FY end",
                "Last Date to Hold AGM": format_date(row.deadline),
                "Type": agm_type,
            }
        )

    with st.container(border=True):
        st.subheader("AGM Schedule - First FY to FY 2030-31")
        st.dataframe(table_rows, hide_index=True, use_container_width=True)
        st.info(
            "15-Month Gap Rule: In addition to the above deadlines, the gap between any two "
            "consecutive AGMs must not exceed 15 months [Sec 96(1)]. Verify against the "
            "actual date of the previous AGM for compliance."
        )

with st.container(border=True):
    st.subheader("Key Rules - Companies Act, 2013")
    st.markdown(
        """
- Every company except a One Person Company (OPC) must hold an AGM every year [Sec 96(1)].
- The meeting must be specifically called and identified as an "Annual General Meeting" in the notice.
- First AGM: must be held within 9 months from the close of the first financial year.
- Subsequent AGMs: must be held within 6 months from the close of each financial year.
- The gap between any two consecutive AGMs must not exceed 15 months.
- Financial year ends on 31 March every year.
- Registrar of Companies may grant an extension of up to 3 months for holding an AGM, other than the first AGM.
- If the first AGM is held within the prescribed period, no AGM is required in the year of incorporation.
"""
    )

st.caption("For reference only. Verify with a qualified Company Secretary for compliance advice.")
