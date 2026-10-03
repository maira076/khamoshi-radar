import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from datetime import datetime
import json

from google import genai

# =========================================================
# GEMINI CONFIGURATION
# =========================================================

GEMINI_MODEL = "gemini-3.8-flash"


def get_gemini_client():

    try:
        api_key = st.secrets["GEMINI_API_KEY"]

        return genai.Client(
            api_key=api_key
        )

    except Exception:
        return None

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Khamoshi Radar",
    page_icon="🌊",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

if "mission_decision" not in st.session_state:
    st.session_state.mission_decision = "PENDING"

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []


def add_audit_event(event, description):
    st.session_state.audit_log.append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Event": event,
        "Description": description
    })


# =========================================================
# DATA
# =========================================================

villages = pd.DataFrame([
    {
        "village_id": "V001",
        "village_name": "Chak 42",
        "latitude": 28.42,
        "longitude": 70.31,
        "population": 3240,
        "rainfall_mm": 165,
        "flood_extent": 0.82,
        "aid_requests": 0,
        "network_status": "DOWN"
    },

    {
        "village_id": "V002",
        "village_name": "Basti Noor",
        "latitude": 28.46,
        "longitude": 70.36,
        "population": 2150,
        "rainfall_mm": 142,
        "flood_extent": 0.71,
        "aid_requests": 14,
        "network_status": "ACTIVE"
    },

    {
        "village_id": "V003",
        "village_name": "Kot Mehr",
        "latitude": 28.38,
        "longitude": 70.27,
        "population": 4100,
        "rainfall_mm": 178,
        "flood_extent": 0.88,
        "aid_requests": 0,
        "network_status": "DOWN"
    },

    {
        "village_id": "V004",
        "village_name": "Basti Aman",
        "latitude": 28.35,
        "longitude": 70.22,
        "population": 1850,
        "rainfall_mm": 45,
        "flood_extent": 0.12,
        "aid_requests": 0,
        "network_status": "ACTIVE"
    },

    {
        "village_id": "V005",
        "village_name": "Chak Rehmat",
        "latitude": 28.51,
        "longitude": 70.40,
        "population": 2800,
        "rainfall_mm": 135,
        "flood_extent": 0.66,
        "aid_requests": 8,
        "network_status": "ACTIVE"
    },

    {
        "village_id": "V006",
        "village_name": "Basti Ali",
        "latitude": 28.33,
        "longitude": 70.34,
        "population": 950,
        "rainfall_mm": 110,
        "flood_extent": 0.61,
        "aid_requests": 0,
        "network_status": "DOWN"
    }
])


resources = pd.DataFrame([
    {
        "organization": "Rescue 1122",
        "latitude": 28.50,
        "longitude": 70.30,
        "boats": 2,
        "capacity": 60,
        "medical": True
    },

    {
        "organization": "Edhi",
        "latitude": 28.55,
        "longitude": 70.42,
        "boats": 1,
        "capacity": 30,
        "medical": True
    },

    {
        "organization": "Al-Khidmat",
        "latitude": 28.39,
        "longitude": 70.18,
        "boats": 1,
        "capacity": 45,
        "medical": True
    },

    {
        "organization": "Local Boat Network",
        "latitude": 28.44,
        "longitude": 70.28,
        "boats": 4,
        "capacity": 80,
        "medical": False
    }
])


# =========================================================
# SILENCE RADAR
# =========================================================

def calculate_silence_score(row):

    flood = row["flood_extent"] * 40

    rain = min(
        row["rainfall_mm"] / 200,
        1
    ) * 20

    population = min(
        row["population"] / 5000,
        1
    ) * 20

    silence = (
        20
        if row["aid_requests"] == 0
        else 0
    )

    return round(
        flood + rain + population + silence,
        2
    )


villages["silence_score"] = villages.apply(
    calculate_silence_score,
    axis=1
)


villages["silent_zone"] = (
    (villages["flood_extent"] >= 0.50)
    &
    (villages["aid_requests"] == 0)
    &
    (villages["population"] > 0)
)


silent_zones = villages[
    villages["silent_zone"]
].copy()


# =========================================================
# VERIFICATION DEMO DATA
# =========================================================

verification_data = {
    "V001": {
        "status": "VERIFIED_EMERGENCY",
        "confidence": 0.95,
        "reports": [
            "Basti Noor: Flooding confirmed",
            "Chak Rehmat: Flooding confirmed"
        ]
    },

    "V003": {
        "status": "LIKELY_EMERGENCY",
        "confidence": 0.70,
        "reports": [
            "Basti Aman: Flooding reported"
        ]
    },

    "V006": {
        "status": "INSUFFICIENT_INFORMATION",
        "confidence": 0.40,
        "reports": [
            "Basti Aman: Situation unknown"
        ]
    }
}


# =========================================================
# RESOURCE BIDDING
# =========================================================

def calculate_bid(village, resource):

    distance = geodesic(
        (
            village["latitude"],
            village["longitude"]
        ),
        (
            resource["latitude"],
            resource["longitude"]
        )
    ).km

    distance_score = max(
        0,
        35 - distance
    )

    capacity_score = min(
        resource["capacity"] / 100 * 30,
        30
    )

    boat_score = min(
        resource["boats"] * 5,
        20
    )

    medical_score = (
        15
        if resource["medical"]
        else 0
    )

    total = (
        distance_score
        + capacity_score
        + boat_score
        + medical_score
    )

    eta = round(
        (distance / 30) * 60
    )

    return {
        "Organization":
            resource["organization"],

        "Distance (km)":
            round(distance, 2),

        "ETA (min)":
            eta,

        "Boats":
            resource["boats"],

        "Capacity":
            resource["capacity"],

        "Medical":
            resource["medical"],

        "Bid Score":
            round(total, 2)
    }

# =========================================================
# LIVE GEMINI COORDINATOR
# =========================================================

def get_gemini_coordination(
    village,
    verification,
    selected_resources
):

    client = get_gemini_client()

    if client is None:
        return None

    resources_for_prompt = []

    for _, resource in selected_resources.iterrows():

        resources_for_prompt.append({
            "organization":
                resource["Organization"],

            "distance_km":
                resource["Distance (km)"],

            "eta_minutes":
                resource["ETA (min)"],

            "boats":
                resource["Boats"],

            "capacity":
                resource["Capacity"],

            "medical_support":
                bool(resource["Medical"])
        })

    prompt = f"""
You are the Coordinator Agent of Khamoshi Radar,
an AI-assisted flood emergency coordination system.

Use ONLY the information supplied below.

Do not invent:
- casualties
- stranded people
- infrastructure damage
- resources
- dispatch activity

The system has NOT dispatched anything.
A human coordinator must make the final decision.

INCIDENT

Village:
{village['village_name']}

Population:
{int(village['population'])}

Flood extent:
{float(village['flood_extent']) * 100:.0f}%

Rainfall:
{float(village['rainfall_mm'])} mm

Aid requests:
{int(village['aid_requests'])}

Network:
{village['network_status']}

Silence score:
{float(village['silence_score'])}/100

Neighbor verification:
{verification['status']}

Verification confidence:
{verification['confidence'] * 100:.0f}%

PROPOSED RESOURCES

{json.dumps(resources_for_prompt, indent=2)}

TASK

Provide a concise operational recommendation for the
human emergency coordinator.

Explain:

1. Why this incident deserves attention.
2. Why these resources are appropriate.
3. Any important limitation or uncertainty.
4. What the human coordinator should do next.

Do not claim that dispatch has already happened.

Keep the response under 180 words.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        return response.text

    except Exception as e:

        return None

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("KHAMOSHI RADAR")

st.sidebar.caption(
    "AI-Assisted Flood Emergency Coordination"
)

st.sidebar.divider()

mode = st.sidebar.selectbox(
    "AI Mode",
    [
        "DEMO MODE",
        "LIVE GEMINI"
    ]
)

if mode == "DEMO MODE":

    st.sidebar.info(
        "🔵 Demo Coordinator active"
    )

else:

    if get_gemini_client() is not None:

        st.sidebar.success(
            "🟢 Gemini API configured"
        )

    else:

        st.sidebar.error(
            "🔴 Gemini API key unavailable"
        )

st.sidebar.divider()

selected_village_name = st.sidebar.selectbox(
    "Select Silent Zone",
    silent_zones["village_name"].tolist()
)


selected_village = silent_zones[
    silent_zones["village_name"]
    == selected_village_name
].iloc[0]


# =========================================================
# HEADER
# =========================================================

st.title("🌊 Khamoshi Radar")

st.write(
    "**When silence becomes the emergency signal.**"
)

st.caption(
    "Hackathon prototype — simulated operational data"
)

st.divider()


# =========================================================
# METRICS
# =========================================================

verified_count = sum(
    1
    for item in verification_data.values()
    if item["status"] == "VERIFIED_EMERGENCY"
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Silent Zones",
    len(silent_zones)
)

col2.metric(
    "Verified Emergencies",
    verified_count
)

col3.metric(
    "Population in Silent Zones",
    f"{silent_zones['population'].sum():,}"
)

col4.metric(
    "AI Mode",
    "DEMO" if mode == "DEMO MODE" else "LIVE"
)


st.divider()


# =========================================================
# MAP + INCIDENT DETAILS
# =========================================================

left, right = st.columns(
    [1.6, 1]
)


with left:

    st.subheader("Flood Intelligence Map")

    flood_map = folium.Map(
        location=[
            villages["latitude"].mean(),
            villages["longitude"].mean()
        ],
        zoom_start=10
    )

    for _, village in villages.iterrows():

        if village["silent_zone"]:
            marker_color = "red"

        elif village["flood_extent"] >= 0.50:
            marker_color = "orange"

        else:
            marker_color = "green"

        popup = f"""
        <b>{village['village_name']}</b><br>
        Population: {village['population']}<br>
        Flood: {village['flood_extent'] * 100:.0f}%<br>
        Requests: {village['aid_requests']}<br>
        Network: {village['network_status']}
        """

        folium.Marker(
            [
                village["latitude"],
                village["longitude"]
            ],
            popup=popup,
            tooltip=village["village_name"],
            icon=folium.Icon(
                color=marker_color
            )
        ).add_to(flood_map)

    st_folium(
        flood_map,
        width=None,
        height=470
    )


with right:

    st.subheader("Silent Zone Alert")

    st.error(
        f"⚠️ {selected_village['village_name']}"
    )

    st.metric(
        "Population",
        f"{selected_village['population']:,}"
    )

    a, b = st.columns(2)

    a.metric(
        "Flood Extent",
        f"{selected_village['flood_extent'] * 100:.0f}%"
    )

    b.metric(
        "Rainfall",
        f"{selected_village['rainfall_mm']} mm"
    )

    a.metric(
        "Aid Requests",
        selected_village["aid_requests"]
    )

    b.metric(
        "Network",
        selected_village["network_status"]
    )

    st.metric(
        "Silence Score",
        f"{selected_village['silence_score']}/100"
    )

    st.warning(
        "Flood evidence exists while no aid requests "
        "are being received. Silence cannot be treated "
        "as evidence of safety."
    )


st.divider()


# =========================================================
# NEIGHBOR VERIFICATION
# =========================================================

st.subheader("📡 Neighbor Verification Agent")


verification = verification_data.get(
    selected_village["village_id"]
)


if verification:

    status = verification["status"]

    if status == "VERIFIED_EMERGENCY":

        st.error(
            "🚨 VERIFIED EMERGENCY"
        )

    elif status == "LIKELY_EMERGENCY":

        st.warning(
            "⚠️ LIKELY EMERGENCY"
        )

    else:

        st.info(
            "ℹ️ INSUFFICIENT INFORMATION"
        )


    st.progress(
        verification["confidence"]
    )

    st.write(
        f"Verification confidence: "
        f"**{verification['confidence'] * 100:.0f}%**"
    )


    for report in verification["reports"]:

        st.write("✓", report)


st.divider()


# =========================================================
# RESOURCE NEGOTIATION
# =========================================================

st.subheader("🤖 Negotiating Resource Agents")


if (
    verification
    and verification["status"]
    == "VERIFIED_EMERGENCY"
):

    bids = []

    for _, resource in resources.iterrows():

        bids.append(
            calculate_bid(
                selected_village,
                resource
            )
        )

    bids_df = pd.DataFrame(bids)

    bids_df = bids_df.sort_values(
        "Bid Score",
        ascending=False
    )

    st.dataframe(
        bids_df,
        use_container_width=True,
        hide_index=True
    )


    # Top resources
    selected_resources = (
        bids_df.head(3)
    )

    st.write(
        "### Proposed Resource Combination"
    )

    for _, resource in selected_resources.iterrows():

        st.success(
            f"{resource['Organization']} — "
            f"ETA {resource['ETA (min)']} min — "
            f"Capacity {resource['Capacity']} — "
            f"{resource['Boats']} boat(s)"
        )


    st.divider()


    # =====================================================
    # COORDINATOR
    # =====================================================

    st.subheader(
        "🧠 Coordinator Agent"
    )

    total_capacity = int(
        selected_resources[
            "Capacity"
        ].sum()
    )

    total_boats = int(
        selected_resources[
            "Boats"
        ].sum()
    )

    selected_names = (
        selected_resources[
            "Organization"
        ].tolist()
    )


      if mode == "LIVE GEMINI":

                with st.spinner(
                    "Gemini Coordinator analyzing incident..."
                ):
        
                    gemini_recommendation = get_gemini_coordination(
                        selected_village,
                        verification,
                        selected_resources
                    )
                    
      if mode == "LIVE GEMINI":

                        with st.spinner(
                            "Gemini Coordinator analyzing incident..."
                        ):
                
                            gemini_recommendation = get_gemini_coordination(
                                selected_village,
                                verification,
                                selected_resources
                            )

        if gemini_recommendation:

            st.success(
                "🟢 LIVE GEMINI COORDINATOR"
            )

            st.write(
                gemini_recommendation
            )

        else:

            st.warning(
                "🟡 Gemini is currently unavailable "
                "or quota-limited. Demo fallback activated."
            )

            st.info(
                "The Coordinator recommends reviewing "
                "the highest-scoring available resources "
                "based on distance, capacity, boat "
                "availability and medical capability."
            )

        else:
    
            st.info(
                "🔵 DEMO COORDINATOR\n\n"
                "The Coordinator recommends reviewing "
                "the highest-scoring available resources "
                "based on distance, capacity, boat "
                "availability and medical capability."
            )
            

    c1, c2 = st.columns(2)

    c1.metric(
        "Combined Capacity",
        total_capacity
    )

    c2.metric(
        "Combined Boats",
        total_boats
    )


    st.write(
        "**Selected organizations:** "
        + ", ".join(selected_names)
    )


    st.warning(
        "This is an AI-assisted recommendation only. "
        "No dispatch occurs until a human coordinator "
        "reviews the proposal."
    )


    # =====================================================
    # HUMAN APPROVAL
    # =====================================================

    st.write(
        "### Human Coordinator Decision"
    )

    approve_col, modify_col, reject_col = (
        st.columns(3)
    )


    if approve_col.button(
        "✅ Approve Mission",
        use_container_width=True
    ):

        st.session_state.mission_decision = (
            "APPROVED"
        )

        add_audit_event(
            "HUMAN_APPROVAL",
            (
                f"Mission for "
                f"{selected_village_name} approved."
            )
        )


    if modify_col.button(
        "✏️ Modify Plan",
        use_container_width=True
    ):

        st.session_state.mission_decision = (
            "MODIFY"
        )

        add_audit_event(
            "HUMAN_MODIFICATION",
            (
                f"Mission for "
                f"{selected_village_name} "
                f"requires modification."
            )
        )


    if reject_col.button(
        "❌ Reject Mission",
        use_container_width=True
    ):

        st.session_state.mission_decision = (
            "REJECTED"
        )

        add_audit_event(
            "HUMAN_REJECTION",
            (
                f"Mission for "
                f"{selected_village_name} rejected."
            )
        )


    decision = (
        st.session_state.mission_decision
    )


    if decision == "APPROVED":

        st.success(
            "Mission approved by human coordinator."
        )

    elif decision == "MODIFY":

        st.warning(
            "Mission returned for modification."
        )

    elif decision == "REJECTED":

        st.error(
            "Mission rejected by human coordinator."
        )

    else:

        st.info(
            "Awaiting human coordinator decision."
        )


else:

    st.info(
        "Resource negotiation will begin only after "
        "the incident reaches VERIFIED_EMERGENCY status."
    )


# =========================================================
# AUDIT TRAIL
# =========================================================

st.divider()

st.subheader("📋 Decision Audit Trail")


if st.session_state.audit_log:

    audit_df = pd.DataFrame(
        st.session_state.audit_log
    )

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.caption(
        "No human decisions recorded yet."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Khamoshi Radar | Hackathon Prototype | "
    "Flood and resource information currently simulated."
)
