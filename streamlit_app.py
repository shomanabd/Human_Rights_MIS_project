import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timezone
import uuid
import os
import json
import folium
from streamlit_folium import st_folium
import plotly.express as px
import io
import base64
import csv
from fpdf import FPDF


API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Human Rights MIS", layout="wide")
st.title("\U0001f6e1️ Human Rights Monitor MIS")

ACCESS_CODES = {"Lawyer": "LEGAL123", "Admin": "ADMIN123"}


def generate_csv_download(data, filename="export.csv"):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    csv_data = output.getvalue()
    b64 = base64.b64encode(csv_data.encode()).decode()
    href = (
        f'<a href="data:file/csv;base64,{b64}" download="{filename}"> Download CSV</a>'
    )
    return href


def generate_pdf_download(data, title="Report", filename="report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)

    for item in data:
        for key, val in item.items():
            pdf.multi_cell(0, 10, f"{key.title()}: {val}")
        pdf.ln(5)

    pdf_data = pdf.output(dest="S").encode("latin-1")
    b64 = base64.b64encode(pdf_data).decode()

    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}"> Download PDF</a>'
    return href


# Create media directory if it doesn't exist
if not os.path.exists("media"):
    os.makedirs("media")

os.makedirs("media/case_evidence", exist_ok=True)  # Ensure directory exists

role = st.sidebar.selectbox(
    "\U0001f464 Select Role", ["Public", "NGO Worker", "Lawyer", "Admin"]
)

access_code_required = role in ACCESS_CODES
if access_code_required:
    st.sidebar.caption("\U0001f511 Example: Admin=ADMIN123, Lawyer=LEGAL123")
    access_code = st.sidebar.text_input("\U0001f510 Enter Access Code", type="password")

    if access_code != ACCESS_CODES[role]:
        st.sidebar.error(
            " Invalid access code" if access_code else "Access code required"
        )
        st.stop()
    else:
        st.session_state["access_code"] = access_code

available_tabs = []
if role == "Public":
    available_tabs = ["\U0001f4cb Incident Reporting"]
elif role == "NGO Worker":
    available_tabs = ["\U0001f4cb Incident Reporting"]
elif role == "Lawyer":
    available_tabs = ["\U0001f4cb Incident Reporting", "\U0001f4c1 Case Management"]
elif role == "Admin":
    available_tabs = [
        "\U0001f4cb Incident Reporting",
        "\U0001f4c1 Case Management",
        "\U0001f5a5 Victim/Witness Database",
        "\U0001f5a5 Analytics Dashboard",
    ]

tabs = st.tabs(available_tabs)

if "\U0001f4c1 Case Management" in available_tabs:
    with tabs[available_tabs.index("\U0001f4c1 Case Management")]:
        st.header("\U0001f4c1 Case Management")
        if role == "Admin":
            cm_tab = st.radio(
                "Choose action:",
                [" Add Case", " View Cases", " Edit Case", " Delete Case"],
                horizontal=True,
            )
        else:
            cm_tab = st.radio("Choose action:", [" View Cases"])

        if cm_tab == " Add Case":
            with st.form("add_case_form", clear_on_submit=True):
                case_id = f"HRM-{uuid.uuid4().hex[:6]}"
                title = st.text_input("Case Title*", help="Required field")
                description = st.text_area("Description*", help="Required field")
                violations = st.multiselect(
                    "Violation Types*",
                    [
                        "arbitrary_detention",
                        "torture",
                        "forced_displacement",
                        "property_destruction",
                        "discrimination",
                        "arbitrary_arrest",
                        "freedom_of_expression_violation",
                        "sexual_violence",
                        "extrajudicial_killing",
                        "enforced_disappearance",
                        "child_rights_violation",
                        "economic_exploitation",
                    ],
                    help="Select at least one violation type",
                )
                priority = st.selectbox(
                    "Priority*", ["low", "medium", "high"], help="Required field"
                )
                status = st.selectbox(
                    "Status*",
                    ["new", "under_investigation", "resolved"],
                    help="Required field",
                    key="status_add_case",
                )

                country = st.text_input("Country*", help="Required field")
                region = st.text_input("Region/City")
                lat = st.number_input("Latitude", value=31.9, format="%.6f")
                lon = st.number_input("Longitude", value=35.2, format="%.6f")
                date_occurred = st.date_input(
                    "Date of Violation*", help="Required field"
                )
                date_reported = st.date_input(
                    "Date Reported*", value=datetime.now().date(), help="Required field"
                )
                created_by = st.session_state.get("access_code", "anonymous")
                report_id_link = st.text_input("Linked Incident Report ID (Optional)")
                files = st.file_uploader(
                    "Upload Evidence (Max 10MB each)",
                    type=["jpg", "png", "mp4", "pdf", "docx"],
                    accept_multiple_files=True,
                )

                submit = st.form_submit_button("Submit Case")
                if submit:
                    if not title or not description or not violations or not country:
                        st.error("Please fill all required fields (marked with *)")
                    else:

                        evidence_list = []
                        upload_tuples = []

                        os.makedirs("media/case_evidence", exist_ok=True)

                        for file in files:
                            if file.size > 10 * 1024 * 1024:
                                st.error(f"File {file.name} is too large (max 10MB)")
                                continue

                            file_path = f"media/case_evidence/{file.name}"
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())

                            evidence_list.append(
                                {
                                    "type": (
                                        file.type.split("/")[0]
                                        if file.type
                                        else "unknown"
                                    ),
                                    "url": f"/{file_path}",
                                    "description": file.name,
                                    "date_captured": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                }
                            )

                            upload_tuples.append(
                                ("evidence_files", (file.name, file, file.type))
                            )

                        # Prepare the main case payload
                        data = {
                            "case_id": case_id,
                            "title": title,
                            "description": description,
                            "violation_types": violations,
                            "status": status,
                            "priority": priority,
                            "location": {
                                "country": country,
                                "region": region,
                                "coordinates": {
                                    "type": "Point",
                                    "coordinates": [lon, lat],
                                },
                            },
                            "date_occurred": date_occurred.isoformat(),
                            "date_reported": date_reported.isoformat(),
                            "victims": [],
                            "perpetrators": [],
                            "evidence": evidence_list,
                            "created_by": created_by,
                            "incident_report_id": (
                                report_id_link if report_id_link else None
                            ),
                        }

                        # Send to FastAPI
                        res = requests.post(
                            f"{API_BASE}/cases/",
                            data={"case": json.dumps(data)},
                            files=upload_tuples,
                        )

                        if res.ok:
                            st.success(" Case created successfully!")
                        else:
                            st.error(f" Error creating case: {res.text}")

        elif cm_tab == " View Cases":
            st.subheader(" Filter Cases")
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.selectbox(
                    "Status",
                    ["All"] + ["new", "under_investigation", "resolved"],
                    key="status_filter_cases",
                )

            with col2:
                country_filter = st.text_input("Country")
            with col3:
                violation_filter = st.selectbox(
                    "Violation Type",
                    ["All"]
                    + [
                        "arbitrary_detention",
                        "torture",
                        "forced_displacement",
                        "property_destruction",
                        "discrimination",
                        "arbitrary_arrest",
                        "freedom_of_expression_violation",
                        "sexual_violence",
                        "extrajudicial_killing",
                        "enforced_disappearance",
                        "child_rights_violation",
                        "economic_exploitation",
                    ],
                )

            params = {}
            if status_filter != "All":
                params["status"] = status_filter
            if country_filter:
                params["country"] = country_filter
            if violation_filter != "All":
                params["violation"] = violation_filter

            res = requests.get(f"{API_BASE}/cases/", params=params)
            if res.ok:
                cases = res.json()
                if not cases:
                    st.info("No cases found matching your criteria.")
                else:
                    st.write(f"Found {len(cases)} cases")
                    flat_cases = [
                        {
                            "Case ID": c["case_id"],
                            "Title": c["title"],
                            "Status": c["status"],
                            "Country": c["location"].get("country", ""),
                            "Region": c["location"].get("region", ""),
                            "Priority": c.get("priority", ""),
                            "Date Occurred": c.get("date_occurred", "")[:10],
                            "Description": c.get("description", "")[:100],
                        }
                        for c in cases
                    ]

            st.markdown("### Export Cases")
            st.markdown(
                generate_csv_download(flat_cases, filename="cases.csv"),
                unsafe_allow_html=True,
            )
            st.markdown(
                generate_pdf_download(flat_cases, title="Cases", filename="cases.pdf"),
                unsafe_allow_html=True,
            )

            for case in cases:
                with st.expander(
                    f"{case['case_id']} – {case['title']} ({case['status'].replace('_', ' ').title()})"
                ):

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(
                            " **Violation Date:**",
                            case.get("date_occurred", "N/A")[:10],
                        )
                        st.write(
                            " **Reported Date:**",
                            case.get("date_reported", "N/A")[:10],
                        )
                        st.write(
                            " **Violation Types:**",
                            ", ".join(case.get("violation_types", [])),
                        )
                        st.write(
                            " **Location:**",
                            f"{case['location'].get('region', '')}, {case['location'].get('country', '')}",
                        )
                        st.write(
                            " **Priority:**",
                            case.get("priority", "N/A").title(),
                        )
                    with col2:
                        st.write(" **Description:**")
                        st.write(case.get("description", "No description provided"))

                    coords = (
                        case["location"]
                        .get("coordinates", {})
                        .get("coordinates", [0, 0])
                    )
                    if coords != [0, 0]:
                        m = folium.Map(location=[coords[1], coords[0]], zoom_start=8)
                        folium.Marker(
                            [coords[1], coords[0]], tooltip=case["title"]
                        ).add_to(m)
                        st_folium(
                            m,
                            width=700,
                            height=300,
                            key=f"case_map_{case['case_id']}",
                        )

                    if case.get("evidence"):
                        st.subheader(" Evidence")
                        for ev in case["evidence"]:
                            if ev["type"] == "image":
                                st.image(
                                    f"{API_BASE}{ev['url']}",
                                    caption=ev["description"],
                                )
                            else:
                                st.markdown(
                                    f"[📎 {ev['description']}]({API_BASE}{ev['url']})"
                                )

        elif cm_tab == " Edit Case" and role == "Admin":
            st.subheader("Edit Case Status")
            res = requests.get(f"{API_BASE}/cases/")
            if res.ok:
                cases = res.json()
                case_options = {
                    f"{case['case_id']} - {case['title']}": case["case_id"]
                    for case in cases
                }
                selected_case = st.selectbox(
                    "Select Case", options=list(case_options.keys())
                )
                case_id = case_options[selected_case]

                current_status = next(
                    (case["status"] for case in cases if case["case_id"] == case_id),
                    "new",
                )
                new_status = st.selectbox(
                    "Update Status",
                    ["new", "under_investigation", "resolved"],
                    index=["new", "under_investigation", "resolved"].index(
                        current_status
                    ),
                    key="status_edit_case",
                )

                if st.button("Update Case Status"):
                    res = requests.patch(
                        f"{API_BASE}/cases/{case_id}", params={"status": new_status}
                    )
                    if res.ok:
                        st.success(" Case status updated successfully!")
                    else:
                        st.error(f" Error updating case: {res.text}")

        elif cm_tab == " Delete Case" and role == "Admin":
            st.subheader("Delete Case")
            st.warning(
                " This action cannot be undone. Deleted cases cannot be recovered."
            )
            res = requests.get(f"{API_BASE}/cases/")
            if res.ok:
                cases = res.json()
                case_options = {
                    f"{case['case_id']} - {case['title']}": case["case_id"]
                    for case in cases
                }
                selected_case = st.selectbox(
                    "Select Case to Delete", options=list(case_options.keys())
                )
                case_id = case_options[selected_case]

                if st.button("Confirm Delete"):
                    res = requests.delete(f"{API_BASE}/cases/{case_id}")
                    if res.ok:
                        st.success(" Case deleted successfully!")
                    else:
                        st.error(f" Error deleting case: {res.text}")


if "\U0001f4cb Incident Reporting" in available_tabs:
    with tabs[available_tabs.index("\U0001f4cb Incident Reporting")]:
        st.header("\U0001f4cb Incident Reporting")

        if role == "Public":
            ir_tab = st.radio(
                "Choose action:", [" Submit Report", " Analytics"], horizontal=True
            )
        elif role == "NGO Worker":
            ir_tab = st.radio("Choose action:", [" Submit Report", " View Reports"])
        else:
            ir_tab = st.radio(
                "Choose action:",
                [" Submit Report", " View Reports", " Analytics"],
                horizontal=True,
            )

        if ir_tab == " Submit Report":

            anonymous = st.checkbox(
                "Report Anonymously", value=True, key="anonymous_checkbox"
            )

            if not st.session_state.get("anonymous_checkbox", True):
                col1, col2 = st.columns(2)
                with col1:
                    email = st.text_input("Email", key="email_field")
                with col2:
                    phone = st.text_input("Phone", key="phone_field")
                contact_method = st.selectbox(
                    "Preferred Contact Method",
                    ["email", "phone"],
                    key="contact_method_field",
                )
            else:
                email = phone = contact_method = None

            with st.form("report_form", clear_on_submit=True):
                report_id = f"IR-{uuid.uuid4().hex[:6]}"
                reporter_type = st.selectbox(
                    "Reporter Type*",
                    ["victim", "witness", "ngo_worker"],
                    help="Required field",
                )

                st.subheader("Incident Details")
                col1, col2 = st.columns(2)
                with col1:
                    country = st.text_input("Country*", help="Required field")
                with col2:
                    city = st.text_input("City/Town")

                col1, col2 = st.columns(2)
                with col1:
                    lat = st.number_input("Latitude*", value=31.9, format="%.6f")
                with col2:
                    lon = st.number_input("Longitude*", value=35.2, format="%.6f")

                date = st.date_input(
                    "Incident Date*", value=datetime.now().date(), help="Required field"
                )
                description = st.text_area(
                    "Incident Description*", help="Required field"
                )
                violations = st.multiselect(
                    "Violation Types*",
                    [
                        "arbitrary_detention",
                        "torture",
                        "forced_displacement",
                        "property_destruction",
                        "discrimination",
                        "arbitrary_arrest",
                        "freedom_of_expression_violation",
                        "sexual_violence",
                        "extrajudicial_killing",
                        "enforced_disappearance",
                        "child_rights_violation",
                        "economic_exploitation",
                    ],
                    help="Select at least one violation type",
                )

                files = st.file_uploader(
                    "Upload Evidence (Max 10MB each)",
                    type=["jpg", "png", "mp4", "pdf", "docx"],
                    accept_multiple_files=True,
                    help="Upload any supporting evidence",
                )

                submit = st.form_submit_button("Submit Report")
                if submit:
                    # Validate required fields
                    if (
                        not description
                        or not violations
                        or not country
                        or not date
                        or lat is None
                        or lon is None
                    ):
                        st.error("Please fill all required fields (marked with *)")
                    else:
                        try:
                            form_data = {
                                "report_id": report_id,
                                "reporter_type": reporter_type,
                                "anonymous": str(
                                    st.session_state.get("anonymous_checkbox", True)
                                ).lower(),
                                "contact_info": (
                                    {
                                        "email": email,
                                        "phone": phone,
                                        "preferred_contact": contact_method,
                                    }
                                    if not st.session_state.get(
                                        "anonymous_checkbox", True
                                    )
                                    else None
                                ),
                                "date": date.isoformat(),
                                "country": country,
                                "lat": lat,
                                "lon": lon,
                                "description": description,
                                "violation_types_str": ",".join(violations),
                            }

                            # Prepare files for upload
                            files_to_upload = []
                            for file in files:
                                if file.size > 10 * 1024 * 1024:
                                    st.error(
                                        f"File {file.name} is too large (max 10MB)"
                                    )
                                    continue
                                files_to_upload.append(
                                    (
                                        "evidence_files",
                                        (file.name, file.getvalue(), file.type),
                                    )
                                )

                            # Submit report
                            res = requests.post(
                                f"{API_BASE}/reports/",
                                data=form_data,
                                files=files_to_upload,
                            )
                            if res.ok:
                                st.success(" Report submitted successfully!")
                            else:
                                st.error(f" Error submitting report: {res.text}")
                        except Exception as e:
                            st.error(f" An error occurred: {str(e)}")

        elif ir_tab == " View Reports":
            st.subheader(" Filter Reports")
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_status = st.selectbox(
                    "Status",
                    ["All"] + ["new", "under_investigation", "resolved"],
                    key="status_filter_ir",
                )

            with col2:
                selected_location = st.text_input("Location (Country or City)")
            with col3:
                selected_date = st.date_input("Filter by Incident Date", value=None)

            params = {}
            if selected_status != "All":
                params["status"] = selected_status
            if selected_location:
                params["location"] = selected_location
            if selected_date:
                params["date"] = selected_date.isoformat()

            res = requests.get(f"{API_BASE}/reports/", params=params)
            if res.ok:
                reports = res.json()
                if not reports:
                    st.info("No reports found matching your criteria.")
                else:
                    st.write(f"Found {len(reports)} reports")

                    flat_reports = [
                        {
                            "Report ID": r["report_id"],
                            "Status": r.get("status", ""),
                            "Date": r["incident_details"].get("date", ""),
                            "Country": r["incident_details"]["location"].get(
                                "country", ""
                            ),
                            "City": r["incident_details"]["location"].get("city", ""),
                            "Description": r["incident_details"].get("description", "")[
                                :100
                            ],
                        }
                        for r in reports
                    ]

                    st.markdown("### Export Reports")
                    st.markdown(
                        generate_csv_download(
                            flat_reports, filename="incident_reports.csv"
                        ),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        generate_pdf_download(
                            flat_reports,
                            title="Incident Reports",
                            filename="incident_reports.pdf",
                        ),
                        unsafe_allow_html=True,
                    )

                    for report in reports:
                        d = report["incident_details"]
                        with st.expander(
                            f"{report['report_id']} - {d['description'][:50]}... ({report.get('status', 'new').replace('_', ' ').title()})"
                        ):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(
                                    " **Location:**",
                                    f"{d['location'].get('city', '')}, {d['location'].get('country', '')}",
                                )
                                st.write(" **Date:**", d.get("date", "N/A")[:10])
                                st.write(
                                    "👤 **Reporter Type:**",
                                    report.get("reporter_type", "N/A")
                                    .replace("_", " ")
                                    .title(),
                                )
                            with col2:
                                st.write(
                                    " **Violations:**",
                                    ", ".join(d.get("violation_types", [])),
                                )
                                if not report.get("anonymous", True):
                                    contact_info = report.get("contact_info", {})
                                    st.write(
                                        " **Contact:**",
                                        contact_info.get(
                                            "preferred_contact", "N/A"
                                        ).title(),
                                    )
                                    if contact_info and contact_info.get("email"):
                                        st.write(" **Email:**", contact_info["email"])
                                    if contact_info and contact_info.get("phone"):
                                        st.write(" **Phone:**", contact_info["phone"])

                            coords = (
                                d.get("location", {})
                                .get("coordinates", {})
                                .get("coordinates", [0, 0])
                            )
                            if coords != [0, 0]:
                                m = folium.Map(
                                    location=[coords[1], coords[0]], zoom_start=10
                                )
                                folium.Marker(
                                    [coords[1], coords[0]], tooltip="Incident Location"
                                ).add_to(m)
                                st_folium(
                                    m,
                                    width=700,
                                    height=300,
                                    key=f"report_map_{report['report_id']}",
                                )

                            st.write(" **Full Description:**")
                            st.write(d.get("description", "No description provided"))

                            if report.get("evidence"):
                                st.subheader(" Evidence")
                                for ev in report["evidence"]:
                                    if ev["type"] == "image":
                                        st.image(
                                            f"{API_BASE}{ev['url']}",
                                            caption=ev["description"],
                                        )
                                    else:
                                        st.markdown(
                                            f"[ {ev['description']}]({API_BASE}{ev['url']})"
                                        )

        elif ir_tab == " Analytics":
            st.subheader(" Violation Types Distribution")
            res = requests.get(f"{API_BASE}/reports/analytics")
            if res.ok and res.json():
                df = pd.DataFrame(res.json())
                df = df.rename(
                    columns={"violation_type": "Violation Type", "count": "Count"}
                )
                df["Violation Type"] = (
                    df["Violation Type"].str.replace("_", " ").str.title()
                )
                fig = px.bar(
                    df,
                    x="Violation Type",
                    y="Count",
                    title="Reported Violation Types",
                    color="Violation Type",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No violation data available yet.")

            st.subheader(" Timeline of Reports")
            res2 = requests.get(f"{API_BASE}/reports/analytics/timeline")
            if res2.ok and res2.json():
                timeline_df = pd.DataFrame(res2.json())
                timeline_df["date"] = pd.to_datetime(timeline_df["date"])
                fig = px.line(
                    timeline_df,
                    x="date",
                    y="count",
                    title="Reports Over Time",
                    labels={"date": "Date", "count": "Number of Reports"},
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timeline data available.")

            st.subheader(" Incident Heatmap")
            geo = requests.get(f"{API_BASE}/reports/analytics/geodata")
            if geo.ok and geo.json():
                geo_df = pd.DataFrame(geo.json())
                if not geo_df.empty:
                    m = folium.Map(
                        location=[geo_df["lat"].mean(), geo_df["lon"].mean()],
                        zoom_start=5,
                    )

                    # Add heatmap
                    from folium.plugins import HeatMap

                    heat_data = [
                        [row["lat"], row["lon"]] for index, row in geo_df.iterrows()
                    ]
                    HeatMap(heat_data).add_to(m)

                    # Add individual markers
                    for _, row in geo_df.iterrows():
                        folium.Marker(
                            location=[row["lat"], row["lon"]],
                            tooltip=row.get("description", "Incident")[:50],
                            popup=f"<b>Violations:</b> {', '.join(row.get('violations', []))}<br><b>Date:</b> {row.get('date', 'N/A')}",
                        ).add_to(m)

                    st_folium(m, width=1000, height=600, key="analytics_map")
                else:
                    st.info("No geodata available yet.")
            else:
                st.info("No geodata available yet.")


if "\U0001f5a5 Victim/Witness Database" in available_tabs and role == "Admin":
    with tabs[available_tabs.index("\U0001f5a5 Victim/Witness Database")]:
        st.header("\U0001f5a5 Victim/Witness Database Management")
        st.write(
            "This module is under development. Functionality to add, view, edit, and delete victim/witness records will be implemented here."
        )


if "\U0001f5a5 Analytics Dashboard" in available_tabs:
    with tabs[available_tabs.index("\U0001f5a5 Analytics Dashboard")]:
        st.header("\U0001f5a5 System Analytics Dashboard")

        # Summary statistics
        st.subheader("\U0001f4ca System Overview")
        res = requests.get(f"{API_BASE}/analytics/summary")
        if res.ok:
            stats = res.json()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Cases", stats["cases"]["total"])
                st.metric("Total Reports", stats["reports"]["total"])
            with col2:
                st.write("**Case Status Distribution**")
                case_status_df = pd.DataFrame(stats["cases"]["by_status"])
                if not case_status_df.empty:
                    st.bar_chart(case_status_df.set_index("_id"))

                st.write("**Report Status Distribution**")
                report_status_df = pd.DataFrame(stats["reports"]["by_status"])
                if not report_status_df.empty:
                    st.bar_chart(report_status_df.set_index("_id"))

        # Violation analysis
        st.subheader("\U0001f4c8 Violation Analysis")
        col1, col2 = st.columns(2)
        with col1:
            source = st.selectbox("Data Source", ["reports", "cases"])
        with col2:
            time_range = st.selectbox(
                "Time Range", ["All", "7 days", "30 days", "90 days"]
            )

        days = None
        if time_range != "All":
            days = int(time_range.split()[0])

        res = requests.get(
            f"{API_BASE}/analytics/violations", params={"source": source, "days": days}
        )
        if res.ok and res.json():
            df = pd.DataFrame(res.json())
            df = df.rename(
                columns={"violation_type": "Violation Type", "count": "Count"}
            )
            df["Violation Type"] = (
                df["Violation Type"].str.replace("_", " ").str.title()
            )

            fig = px.pie(
                df,
                values="Count",
                names="Violation Type",
                title=f"Violation Types Distribution ({source.title()})",
            )
            st.plotly_chart(fig, use_container_width=True)

            fig2 = px.bar(
                df,
                x="Violation Type",
                y="Count",
                title=f"Violation Types Count ({source.title()})",
                color="Violation Type",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No violation data available yet.")

        # Timeline analysis
        st.subheader("\U0001f4c6 Timeline Analysis")
        col1, col2 = st.columns(2)
        with col1:
            timeline_source = st.selectbox("Timeline Source", ["reports", "cases"])
        with col2:
            time_group = st.selectbox("Group By", ["day", "week", "month", "year"])

        res = requests.get(
            f"{API_BASE}/analytics/timeline",
            params={"source": timeline_source, "time_period": time_group},
        )
        if res.ok and res.json():
            timeline_df = pd.DataFrame(res.json())
            timeline_df["date"] = pd.to_datetime(timeline_df["date"])

            fig = px.line(
                timeline_df,
                x="date",
                y="count",
                title=f"{timeline_source.title()} Over Time (Grouped by {time_group})",
                labels={"date": "Date", "count": "Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available yet.")

        # Geographic analysis
        st.subheader("\U0001f5fa Geographic Distribution")
        geo_source = st.selectbox("Map Source", ["reports", "cases"])

        res = requests.get(
            f"{API_BASE}/analytics/geodata", params={"source": geo_source}
        )
        if res.ok and res.json():
            geo_df = pd.DataFrame(res.json())

            m = folium.Map(
                location=[geo_df["lat"].mean(), geo_df["lon"].mean()],
                zoom_start=5,
            )

            # Add heatmap
            from folium.plugins import HeatMap

            heat_data = [[row["lat"], row["lon"]] for _, row in geo_df.iterrows()]
            HeatMap(heat_data).add_to(m)

            # Add markers
            for _, row in geo_df.iterrows():
                folium.Marker(
                    [row["lat"], row["lon"]],
                    tooltip=f"{', '.join(row['violations'])}",
                    popup=row["description"],
                ).add_to(m)

            st_folium(m, width=1000, height=600, key="analytics_map")
        else:
            st.info("No geographic data available yet.")
