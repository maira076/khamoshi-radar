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
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# PROFESSIONAL FRONTEND CSS
# =========================================================

st.markdown("""
<style>

/* ========================================================
   GLOBAL
======================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 90% 0%,
            rgba(14, 165, 233, 0.07),
            transparent 26%
        ),
        radial-gradient(
            circle at 5% 80%,
            rgba(37, 99, 235, 0.05),
            transparent 25%
        ),
        #07111f;
    color: #e5edf7;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.4rem;
    padding-bottom: 4rem;
    padding-left: 2rem;
    padding-right: 2rem;
}


/* ========================================================
   HIDE STREAMLIT DEFAULT CHROME
======================================================== */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}


/* ========================================================
   TYPOGRAPHY
======================================================== */

h1,
h2,
h3 {
    color: #f8fafc !important;
    letter-spacing: -0.02em;
}

p {
    color: #cbd5e1;
}

[data-testid="stCaptionContainer"] {
    color: #7f8ea3 !important;
}


/* ========================================================
   SIDEBAR
======================================================== */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #081524 0%,
            #07111f 100%
        );

    border-right: 1px solid #1c3045;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.3rem;
}

section[data-testid="stSidebar"] h1 {
    font-size: 1.35rem !important;
    letter-spacing: 0.07em;
}

section[data-testid="stSidebar"] label {
    color: #91a4b9 !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}


/* ========================================================
   SELECT BOX
======================================================== */

div[data-baseweb="select"] > div {
    background: #0d1b2c !important;
    border: 1px solid #263b52 !important;
    border-radius: 10px !important;
    color: white !important;
}


/* ========================================================
   METRIC CARDS
======================================================== */

div[data-testid="stMetric"] {

    background:
        linear-gradient(
            145deg,
            rgba(15, 31, 49, 0.98),
            rgba(9, 22, 37, 0.98)
        );

    border: 1px solid #1d354d;

    padding: 1.15rem 1.2rem;

    border-radius: 14px;

    min-height: 118px;

    box-shadow:
        0 8px 24px
        rgba(0, 0, 0, 0.15);
}

div[data-testid="stMetricLabel"] {
    color: #8da1b7 !important;
    font-size: 0.76rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-weight: 700 !important;
}


/* ========================================================
   ALERTS
======================================================== */

div[data-testid="stAlert"] {
    border-radius: 12px;
    border-width: 1px;
}


/* ========================================================
   BUTTONS
======================================================== */

.stButton > button {

    border-radius: 10px;

    min-height: 45px;

    font-weight: 650;

    border: 1px solid #2b435c;

    background: #102238;

    color: #f8fafc;

    transition: all 0.18s ease;
}

.stButton > button:hover {

    border-color: #38bdf8;

    background: #142d48;

    color: white;

    transform: translateY(-1px);
}

.stButton > button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #0369a1,
            #0284c7
        );

    border: 1px solid #0ea5e9;

    color: white;
}


/* ========================================================
   DATAFRAME
======================================================== */

[data-testid="stDataFrame"] {

    border: 1px solid #1f374f;

    border-radius: 12px;

    overflow: hidden;
}


/* ========================================================
   DIVIDERS
======================================================== */

hr {
    border-color: #1a2d42 !important;
    margin-top: 2rem !important;
    margin-bottom: 2rem !important;
}


/* ========================================================
   MAP
======================================================== */

iframe {
    border-radius: 14px !important;
}


/* ========================================================
   HEADER
======================================================== */

.kr-header {

    background:
        linear-gradient(
            115deg,
            rgba(14, 35, 57, 0.98),
            rgba(8, 20, 34, 0.98)
        );

    border: 1px solid #203a54;

    border-radius: 18px;

    padding: 28px 30px;

    margin-bottom: 14px;

    box-shadow:
        0 14px 35px
        rgba(0, 0, 0, 0.18);
}

.kr-eyebrow {

    color: #38bdf8;

    font-size: 0.72rem;

    font-weight: 750;

    letter-spacing: 0.16em;

    text-transform: uppercase;

    margin-bottom: 9px;
}

.kr-title {

    color: #ffffff;

    font-size: 2.3rem;

    font-weight: 780;

    line-height: 1.05;

    margin-bottom: 9px;
}

.kr-subtitle {

    color: #a1b1c5;

    font-size: 0.98rem;

    max-width: 760px;
}

.kr-status {

    display: inline-flex;

    align-items: center;

    gap: 8px;

    padding: 7px 11px;

    margin-top: 17px;

    border-radius: 999px;

    background:
        rgba(34, 197, 94, 0.08);

    border:
        1px solid
        rgba(34, 197, 94, 0.25);

    color: #86efac;

    font-size: 0.72rem;

    font-weight: 700;

    letter-spacing: 0.04em;
}

.kr-dot {

    width: 7px;

    height: 7px;

    border-radius: 50%;

    background: #22c55e;

    box-shadow:
        0 0 10px
        rgba(34, 197, 94, 0.8);
}


/* ========================================================
   SIMULATION NOTICE
======================================================== */

.kr-simulation {

    padding: 9px 12px;

    border-radius: 9px;

    background:
        rgba(245, 158, 11, 0.055);

    border:
        1px solid
        rgba(245, 158, 11, 0.18);

    color: #fbbf24;

    font-size: 0.74rem;

    margin-bottom: 25px;
}


/* ========================================================
   SECTION TITLES
======================================================== */

.kr-section {

    color: #7dd3fc;

    font-size: 0.70rem;

    font-weight: 750;

    letter-spacing: 0.14em;

    text-transform: uppercase;

    margin-bottom: 5px;
}

.kr-panel-title {

    color: #f8fafc;

    font-size: 1.35rem;

    font-weight: 700;

    margin-bottom: 4px;
}

.kr-panel-subtitle {

    color: #8193a9;

    font-size: 0.84rem;

    margin-bottom: 18px;
}


/* ========================================================
   WORKFLOW
======================================================== */

.kr-workflow {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 8px;

    padding: 14px 18px;

    background: #0b1929;

    border: 1px solid #1d354d;

    border-radius: 12px;

    margin-top: 10px;

    margin-bottom: 28px;
}

.kr-step {

    color: #b8c7d8;

    font-size: 0.76rem;

    font-weight: 650;

    text-align: center;
}

.kr-arrow {

    color: #37536e;

    font-size: 0.9rem;
}


/* ========================================================
   SIDEBAR BRAND
======================================================== */

.kr-side-brand {

    padding: 5px 0 16px 0;
}

.kr-side-title {

    color: #ffffff;

    font-size: 1.25rem;

    font-weight: 800;

    letter-spacing: 0.08em;
}

.kr-side-subtitle {

    color: #71869c;

    font-size: 0.72rem;

    margin-top: 4px;
}

.kr-side-label {

    color: #60758c;

    font-size: 0.67rem;

    font-weight: 750;

    text-transform: uppercase;

    letter-spacing: 0.12em;

    margin-top: 15px;

    margin-bottom: 8px;
}

.kr-side-status {

    padding: 10px 11px;

    background: rgba(34,197,94,0.06);

    border:
        1px solid
        rgba(34,197,94,0.18);

    border-radius: 9px;

    color: #86efac;

    font-size: 0.76rem;
}


/* ========================================================
   FOOTER
======================================================== */

.kr-footer {

    text-align: center;

    color: #60758c;

    font-size: 0.73rem;

    padding: 18px 0 5px 0;
}


/* ========================================================
   RESPONSIVE
======================================================== */

@media (max-width: 768px) {

    .block-container {

        padding-left: 1rem;

        padding-right: 1rem;
    }

    .kr-title {

        font-size: 1.75rem;
    }

    .kr-header {

        padding: 21px;
    }

    .kr-workflow {

        display: block;
    }

    .kr-step {

        margin: 8px 0;
    }

    .kr-arrow {

        display: none;
    }
}

</style>
""", unsafe_allow_html=True)


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
        flood
        + rain
        + population
        + silence,
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

        "status":
            "VERIFIED_EMERGENCY",

        "confidence":
            0.95,

        "reports": [
            "Basti Noor: Flooding confirmed",
            "Chak Rehmat: Flooding confirmed"
        ]
    },

    "V003": {

        "status":
            "LIKELY_EMERGENCY",

        "confidence":
            0.70,

        "reports": [
            "Basti Aman: Flooding reported"
        ]
    },

    "V006": {

        "status":
            "INSUFFICIENT_INFORMATION",

        "confidence":
            0.40,

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

    except Exception:
        return None


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    """
    <div class="kr-side-brand">

        <div class="kr-side-title">
            KHAMOSHI RADAR
        </div>

        <div class="kr-side-subtitle">
            Emergency Intelligence Command Center
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.markdown(
    """
    <div class="kr-side-label">
        Command System
    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.markdown(
    """
    <div class="kr-side-status">
        ● &nbsp; SYSTEM OPERATIONAL
    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.divider()


mode = st.sidebar.selectbox(
    "AI Engine",
    [
        "DEMO MODE",
        "LIVE GEMINI"
    ]
)


if mode == "DEMO MODE":

    st.sidebar.info(
        "Demo Coordinator active"
    )

else:

    if get_gemini_client() is not None:

        st.sidebar.success(
            "Gemini API connected"
        )

    else:

        st.sidebar.error(
            "Gemini API unavailable"
        )


st.sidebar.divider()


selected_village_name = st.sidebar.selectbox(
    "Active Incident",
    silent_zones[
        "village_name"
    ].tolist()
)


selected_village = silent_zones[
    silent_zones["village_name"]
    == selected_village_name
].iloc[0]


st.sidebar.divider()


st.sidebar.markdown(
    """
    <div class="kr-side-label">
        Operational Layers
    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.markdown(
    """
    <div style="
        color:#91a4b9;
        font-size:0.80rem;
        line-height:2.15;
    ">
        ◉ &nbsp; Emergency Overview<br>
        ◉ &nbsp; Flood Intelligence<br>
        ◉ &nbsp; Ground Verification<br>
        ◉ &nbsp; Resource Coordination<br>
        ◉ &nbsp; AI Decision Support<br>
        ◉ &nbsp; Human Authorization<br>
        ◉ &nbsp; Audit Trail
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    """
    <div class="kr-header">

        <div class="kr-eyebrow">
            Emergency Intelligence Platform
        </div>

        <div class="kr-title">
            KHAMOSHI RADAR
        </div>

        <div class="kr-subtitle">
            AI-assisted flood emergency detection,
            ground verification and resource coordination
            for communities that have gone silent.
        </div>

        <div class="kr-status">
            <span class="kr-dot"></span>
            SYSTEM OPERATIONAL
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="kr-simulation">
        SIMULATION ENVIRONMENT &nbsp;•&nbsp;
        Flood, village and resource information shown
        in this prototype is demonstration data.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# WORKFLOW
# =========================================================

st.markdown(
    """
    <div class="kr-workflow">

        <div class="kr-step">
            01 &nbsp; SILENCE DETECTION
        </div>

        <div class="kr-arrow">→</div>

        <div class="kr-step">
            02 &nbsp; VERIFICATION
        </div>

        <div class="kr-arrow">→</div>

        <div class="kr-step">
            03 &nbsp; RESOURCE NEGOTIATION
        </div>

        <div class="kr-arrow">→</div>

        <div class="kr-step">
            04 &nbsp; AI COORDINATION
        </div>

        <div class="kr-arrow">→</div>

        <div class="kr-step">
            05 &nbsp; HUMAN APPROVAL
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# METRICS
# =========================================================

verified_count = sum(
    1
    for item in verification_data.values()
    if item["status"]
    == "VERIFIED_EMERGENCY"
)


st.markdown(
    """
    <div class="kr-section">
        Operational Overview
    </div>

    <div class="kr-panel-title">
        Emergency Situation
    </div>

    <div class="kr-panel-subtitle">
        Current silence detection and
        emergency verification status
    </div>
    """,
    unsafe_allow_html=True
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
    "AI Engine",
    "DEMO"
    if mode == "DEMO MODE"
    else "GEMINI"
)


st.divider()


# =========================================================
# MAP + INCIDENT DETAILS
# =========================================================

left, right = st.columns(
    [1.65, 1],
    gap="large"
)


with left:

    st.markdown(
        """
        <div class="kr-section">
            Geospatial Intelligence
        </div>

        <div class="kr-panel-title">
            Flood Intelligence Map
        </div>

        <div class="kr-panel-subtitle">
            Geographic view of monitored communities
            and detected silent zones
        </div>
        """,
        unsafe_allow_html=True
    )


    flood_map = folium.Map(
        location=[
            villages["latitude"].mean(),
            villages["longitude"].mean()
        ],
        zoom_start=10,
        tiles="CartoDB dark_matter"
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
        Population: {village['population']:,}<br>
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

            tooltip=
                village["village_name"],

            icon=folium.Icon(
                color=marker_color,
                icon="info-sign"
            )

        ).add_to(flood_map)


    st_folium(
        flood_map,
        width=None,
        height=500
    )


with right:

    st.markdown(
        """
        <div class="kr-section">
            Active Incident
        </div>

        <div class="kr-panel-title">
            Silent Zone Intelligence
        </div>

        <div class="kr-panel-subtitle">
            Priority incident currently
            under assessment
        </div>
        """,
        unsafe_allow_html=True
    )


    st.error(
        f"🚨 {selected_village['village_name']} "
        f"— SILENT ZONE"
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
        selected_village[
            "aid_requests"
        ]
    )


    b.metric(
        "Network",
        selected_village[
            "network_status"
        ]
    )


    st.metric(
        "Silence Risk Score",
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

st.markdown(
    """
    <div class="kr-section">
        Ground Intelligence
    </div>

    <div class="kr-panel-title">
        Neighbor Verification
    </div>

    <div class="kr-panel-subtitle">
        Cross-community confirmation of conditions
        inside the selected silent zone
    </div>
    """,
    unsafe_allow_html=True
)


verification = verification_data.get(
    selected_village[
        "village_id"
    ]
)


if verification:

    status = verification[
        "status"
    ]


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
        verification[
            "confidence"
        ]
    )


    st.write(
        "Verification confidence: "
        f"**{verification['confidence'] * 100:.0f}%**"
    )


    for report in verification[
        "reports"
    ]:

        st.write(
            "✓",
            report
        )


st.divider()


# =========================================================
# RESOURCE NEGOTIATION
# =========================================================

st.markdown(
    """
    <div class="kr-section">
        Response Coordination
    </div>

    <div class="kr-panel-title">
        Resource Negotiation
    </div>

    <div class="kr-panel-subtitle">
        Candidate response organizations ranked
        by proximity, capacity, boats and
        medical capability
    </div>
    """,
    unsafe_allow_html=True
)


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


    bids_df = pd.DataFrame(
        bids
    )


    bids_df = bids_df.sort_values(
        "Bid Score",
        ascending=False
    )


    st.dataframe(
        bids_df,
        use_container_width=True,
        hide_index=True
    )


    selected_resources = (
        bids_df.head(3)
    )


    st.write(
        "### Proposed Response Team"
    )


    for _, resource in selected_resources.iterrows():

        st.success(
            f"**{resource['Organization']}**"
            f"  •  ETA {resource['ETA (min)']} min"
            f"  •  Capacity {resource['Capacity']}"
            f"  •  {resource['Boats']} boat(s)"
        )


    st.divider()


    # =====================================================
    # COORDINATOR
    # =====================================================

    st.markdown(
        """
        <div class="kr-section">
            AI Decision Support
        </div>

        <div class="kr-panel-title">
            Coordinator Intelligence
        </div>

        <div class="kr-panel-subtitle">
            Operational recommendation prepared
            for human review and authorization
        </div>
        """,
        unsafe_allow_html=True
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

        st.success(
            "🟢 GEMINI COORDINATOR READY"
        )


        st.caption(
            "Gemini runs only when the "
            "Analyze button is selected."
        )


        result_key = (
            f"gemini_result_"
            f"{selected_village['village_id']}"
        )


        if st.button(
            "Analyze Incident with Gemini",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "Gemini Coordinator "
                "analyzing incident..."
            ):

                gemini_recommendation = (
                    get_gemini_coordination(
                        selected_village,
                        verification,
                        selected_resources
                    )
                )


            if gemini_recommendation:

                st.session_state[
                    result_key
                ] = gemini_recommendation


                add_audit_event(
                    "GEMINI_COORDINATOR",
                    (
                        "Gemini analyzed incident at "
                        f"{selected_village['village_name']}."
                    )
                )


            else:

                st.session_state[
                    result_key
                ] = None


                st.warning(
                    "Gemini is currently unavailable "
                    "or quota-limited."
                )


        if (
            result_key
            in st.session_state
            and st.session_state[
                result_key
            ]
        ):

            st.write(
                "### AI Operational Recommendation"
            )


            st.info(
                st.session_state[
                    result_key
                ]
            )


            st.caption(
                "AI-generated recommendation. "
                "Human approval is required "
                "before dispatch."
            )


        elif (
            result_key
            not in st.session_state
        ):

            st.info(
                "Select **Analyze Incident with Gemini** "
                "to generate an operational recommendation."
            )


        else:

            st.warning(
                "No Gemini recommendation is currently "
                "available. The deterministic workflow "
                "remains active."
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
        "**Proposed organizations:** "
        + ", ".join(
            selected_names
        )
    )


    st.warning(
        "AI ADVISORY — This is an AI-assisted "
        "recommendation only. No dispatch occurs "
        "until a human coordinator reviews and "
        "authorizes the proposal."
    )


    st.divider()


    # =====================================================
    # HUMAN APPROVAL
    # =====================================================

    st.markdown(
        """
        <div class="kr-section">
            Human-in-the-Loop Control
        </div>

        <div class="kr-panel-title">
            Mission Authorization
        </div>

        <div class="kr-panel-subtitle">
            AI recommendations cannot trigger deployment.
            Final authority remains with the
            human coordinator.
        </div>
        """,
        unsafe_allow_html=True
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
            "✓ Mission approved by "
            "human coordinator."
        )


    elif decision == "MODIFY":

        st.warning(
            "Mission returned for modification."
        )


    elif decision == "REJECTED":

        st.error(
            "Mission rejected by "
            "human coordinator."
        )


    else:

        st.info(
            "Awaiting human coordinator decision."
        )


else:

    st.info(
        "Resource negotiation is currently locked. "
        "It will begin only after the selected incident "
        "reaches VERIFIED_EMERGENCY status."
    )


# =========================================================
# AUDIT TRAIL
# =========================================================

st.divider()


st.markdown(
    """
    <div class="kr-section">
        Accountability Layer
    </div>

    <div class="kr-panel-title">
        Decision Audit Trail
    </div>

    <div class="kr-panel-subtitle">
        Traceable record of AI analysis
        and human authorization events
    </div>
    """,
    unsafe_allow_html=True
)


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
        "No AI analysis or human "
        "authorization events recorded yet."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()


st.markdown(
    """
    <div class="kr-footer">

        KHAMOSHI RADAR
        &nbsp;•&nbsp;
        AI-Assisted Emergency Intelligence
        &nbsp;•&nbsp;
        Human-Controlled Response
        <br><br>

        Demonstration environment —
        no real-world dispatch occurs from this prototype.

    </div>
    """,
    unsafe_allow_html=True
)
