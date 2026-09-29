import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

from config import APP_NAME, DRUGS

from cv_engine.calibration import decode_image, encode_jpeg
from cv_engine.classifier import analyze_image

from services.hash_service import sha256_bytes, record_hash
from services.pdf_service import build_pdf
from services.storage_service import init_db, save_test, list_tests
from services.location_service import normalize_location


# ============================================================
# GPS
# ============================================================

try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛡️",
    layout="centered"
)


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL APPLICATION BACKGROUND
   ========================================================== */

html,
body {
    background: #f5f8fa !important;
}

.stApp {
    background: #f5f8fa !important;
}

[data-testid="stAppViewContainer"] {
    background: #f5f8fa !important;
}

.main {
    background: #f5f8fa !important;
}


/* ==========================================================
   STREAMLIT TOP BAR
   Hide Deploy / menu / decoration completely.
   This removes the separate strip above the application.
   ========================================================== */

[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    visibility: hidden !important;
}

[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}

#MainMenu {
    display: none !important;
}

footer {
    display: none !important;
}


/* ==========================================================
   MAIN CONTENT AREA
   ========================================================== */

.block-container {
    max-width: 900px !important;

    padding-top: 0.8rem !important;
    padding-bottom: 3rem !important;

    padding-left: 1rem !important;
    padding-right: 1rem !important;

    margin-top: 0 !important;
}


/* ==========================================================
   FORCE READABLE TEXT
   Important for mobile / deployed Streamlit
   ========================================================== */

[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
.stApp label,
.stApp p {
    color: #172033 !important;
}


/* ==========================================================
   HEADER
   ========================================================== */

.app-header {
    background: #0c4a63 !important;

    color: #ffffff !important;

    padding: 20px 24px;

    border-radius: 14px;

    margin-top: 0 !important;

    margin-bottom: 14px;

    box-sizing: border-box;
}

.app-header h1 {
    margin: 0 !important;

    color: #ffffff !important;

    font-size: 30px !important;

    font-weight: 700 !important;

    line-height: 1.2 !important;
}

.app-header p {
    margin: 5px 0 0 !important;

    color: #ffffff !important;

    opacity: 0.88;

    font-size: 15px !important;
}


/* ==========================================================
   STEP BAR
   ========================================================== */

.stepbar {
    display: flex;

    gap: 8px;

    width: 100%;

    margin: 10px 0 18px 0;

    box-sizing: border-box;
}

.step {
    flex: 1;

    text-align: center;

    padding: 10px 4px;

    border-radius: 9px;

    background: #e2eaee !important;

    color: #3c4b52 !important;

    font-size: 13px;

    line-height: 1.35;

    min-height: 52px;

    box-sizing: border-box;
}

.step strong {
    color: inherit !important;
}

.step.active {
    background: #0c4a63 !important;

    color: #ffffff !important;

    font-weight: 700;
}

.step.active strong {
    color: #ffffff !important;
}


/* ==========================================================
   INPUTS
   ========================================================== */

input,
textarea {
    background: #ffffff !important;

    color: #172033 !important;

    -webkit-text-fill-color: #172033 !important;

    border: 1px solid #d7e0e5 !important;

    border-radius: 9px !important;
}

input::placeholder,
textarea::placeholder {
    color: #7a8794 !important;

    opacity: 1 !important;
}


/* ==========================================================
   SELECT BOX
   ========================================================== */

[data-baseweb="select"] {
    background: #ffffff !important;

    color: #172033 !important;

    border-radius: 9px !important;
}

[data-baseweb="select"] * {
    color: #172033 !important;
}

[data-baseweb="select"] input {
    color: #172033 !important;

    -webkit-text-fill-color: #172033 !important;
}


/* Dropdown */

[data-baseweb="popover"] {
    background: #ffffff !important;
}

[data-baseweb="menu"] {
    background: #ffffff !important;
}

[data-baseweb="menu"] * {
    color: #172033 !important;
}

[role="listbox"] {
    background: #ffffff !important;
}

[role="option"] {
    color: #172033 !important;

    background: #ffffff !important;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

div.stButton > button {
    width: 100%;

    border-radius: 9px !important;

    min-height: 42px;

    border: 1px solid #d7e0e5 !important;

    background: #ffffff !important;

    color: #172033 !important;

    font-weight: 600 !important;

    box-shadow: none !important;
}

div.stButton > button p,
div.stButton > button span {
    color: #172033 !important;
}

div.stButton > button:hover {
    border-color: #0c4a63 !important;

    color: #0c4a63 !important;
}


/* Primary button */

div.stButton > button[kind="primary"] {
    background: #0c4a63 !important;

    border-color: #0c4a63 !important;

    color: #ffffff !important;
}

div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span {
    color: #ffffff !important;
}


/* ==========================================================
   CAMERA
   ========================================================== */

[data-testid="stCameraInput"] {
    background: #ffffff !important;

    border-radius: 12px !important;

    overflow: hidden !important;
}


/* ==========================================================
   FILE UPLOADER
   ========================================================== */

[data-testid="stFileUploader"] {
    background: #ffffff !important;

    border-radius: 10px !important;
}

[data-testid="stFileUploader"] * {
    color: #172033 !important;
}


/* ==========================================================
   RESULT
   ========================================================== */

.result {
    padding: 22px;

    border-radius: 15px;

    text-align: center;

    border: 1px solid #d7e0e5;

    margin: 12px 0;

    background: #ffffff;
}

.result h2 {
    font-size: 34px;

    margin: 0;

    color: #172033 !important;
}


/* ==========================================================
   DISCLAIMER
   ========================================================== */

.disclaimer {
    background: #fff8e8;

    color: #172033 !important;

    padding: 13px 15px;

    border-radius: 10px;

    border-left: 4px solid #d99a18;

    font-size: 13px;

    margin-top: 15px;
}


/* ==========================================================
   META CARD
   ========================================================== */

.meta-card {
    background: #ffffff;

    color: #172033 !important;

    border: 1px solid #dfe7eb;

    border-radius: 12px;

    padding: 14px;

    margin: 8px 0;
}


/* ==========================================================
   GPS
   ========================================================== */

.gps-card {
    background: #eef7fa;

    color: #172033 !important;

    border: 1px solid #c8e1e8;

    border-radius: 12px;

    padding: 14px;

    margin: 10px 0;
}

.gps-wait {
    background: #fff8e8;

    color: #172033 !important;

    border-left: 4px solid #d99a18;

    padding: 12px;

    border-radius: 8px;

    margin: 10px 0;
}


/* ==========================================================
   METRICS
   ========================================================== */

[data-testid="stMetric"] {
    background: #ffffff !important;

    border: 1px solid #dfe7eb !important;

    border-radius: 10px !important;
}

[data-testid="stMetricLabel"] {
    color: #687386 !important;
}

[data-testid="stMetricValue"] {
    color: #172033 !important;
}


/* ==========================================================
   DATAFRAME
   ========================================================== */

[data-testid="stDataFrame"] {
    color: #172033 !important;

    border-radius: 10px !important;

    overflow: hidden !important;
}


/* ==========================================================
   ALERTS
   ========================================================== */

[data-testid="stAlert"] p {
    color: inherit !important;
}


/* ==========================================================
   DIVIDERS
   ========================================================== */

hr {
    border: none !important;

    border-top: 1px solid #dfe7eb !important;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 600px) {

    .block-container {
        width: 100% !important;

        max-width: 100% !important;

        padding-top: 0.55rem !important;

        padding-bottom: 2rem !important;

        padding-left: 0.75rem !important;

        padding-right: 0.75rem !important;

        margin-top: 0 !important;
    }


    /* Header */

    .app-header {
        width: 100% !important;

        padding: 16px 17px !important;

        margin-top: 0 !important;

        margin-bottom: 12px !important;

        border-radius: 12px !important;
    }

    .app-header h1 {
        font-size: 23px !important;

        line-height: 1.2 !important;
    }

    .app-header p {
        font-size: 13px !important;
    }


    /* Step bar */

    .stepbar {
        gap: 4px !important;

        margin-top: 8px !important;

        margin-bottom: 14px !important;
    }

    .step {
        min-width: 0 !important;

        min-height: 48px !important;

        padding: 7px 2px !important;

        font-size: 10px !important;

        line-height: 1.25 !important;
    }


    /* Buttons */

    div.stButton > button {
        min-height: 46px !important;

        font-size: 14px !important;
    }


    /* Inputs */

    input,
    textarea,
    [data-baseweb="select"] {
        font-size: 16px !important;
    }


    /* Camera */

    [data-testid="stCameraInput"] {
        width: 100% !important;
    }

}


/* ==========================================================
   VERY SMALL PHONES
   ========================================================== */

@media (max-width: 380px) {

    .block-container {
        padding-top: 0.5rem !important;

        padding-left: 0.55rem !important;

        padding-right: 0.55rem !important;
    }

    .app-header {
        padding: 14px !important;
    }

    .app-header h1 {
        font-size: 21px !important;
    }

    .app-header p {
        font-size: 12px !important;
    }

    .stepbar {
        gap: 3px !important;
    }

    .step {
        font-size: 9px !important;

        min-height: 45px !important;

        padding: 6px 1px !important;
    }

}


</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

def header():

    header_html = (
        '<div class="app-header">'
        f'<h1>🛡️ {APP_NAME}</h1>'
        '<p>Digital companion for field drug testing</p>'
        '</div>'
    )

    st.markdown(
        header_html,
        unsafe_allow_html=True
    )


# ============================================================
# STEP BAR
# ============================================================

def steps(active):

    labels = [
        "Officer",
        "Test details",
        "Take photo",
        "Result",
        "Report"
    ]

    step_items = []

    for i, label in enumerate(
        labels,
        start=1
    ):

        if i == active:

            step_items.append(
                f'<div class="step active">'
                f'<strong>{i}</strong><br>{label}'
                f'</div>'
            )

        else:

            step_items.append(
                f'<div class="step">'
                f'<strong>{i}</strong><br>{label}'
                f'</div>'
            )

    html = (
        '<div class="stepbar">'
        + ''.join(step_items)
        + '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ============================================================
# RESET
# ============================================================

def reset():

    keys_to_remove = []

    for key in list(
        st.session_state.keys()
    ):

        if key.startswith(
            "test_"
        ):

            keys_to_remove.append(
                key
            )

        elif key in [
            "officer_id",
            "page"
        ]:

            keys_to_remove.append(
                key
            )

    for key in keys_to_remove:

        st.session_state.pop(
            key,
            None
        )


# ============================================================
# HOME
# ============================================================

def home():

    header()

    steps(1)

    st.subheader(
        "Officer workspace"
    )

    officer = st.text_input(
        "Officer ID",
        value=st.session_state.get(
            "officer_id",
            ""
        ),
        placeholder="Example: OFF-001"
    )

    if st.button(
        "NEXT →",
        type="primary",
        use_container_width=True
    ):

        if officer.strip():

            st.session_state.officer_id = (
                officer.strip()
            )

            st.session_state.page = (
                "new_test"
            )

            st.rerun()

        else:

            st.error(
                "Please enter an Officer ID."
            )

    st.markdown(
        '<div class="disclaimer">'
        'Prototype • Field-test output is presumptive '
        'and requires laboratory confirmation.'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# NEW TEST
# ============================================================

def new_test():

    header()

    steps(2)

    st.subheader(
        "Start a new test"
    )

    st.caption(
        f"Field Officer · "
        f"{st.session_state.officer_id}"
    )

    drug = st.selectbox(
        "Suspected drug",
        [
            "Choose a drug"
        ] + DRUGS
    )

    batch = st.text_input(
        "Kit batch / lot number (optional)",
        placeholder="As printed on the kit"
    )

    if drug != "Choose a drug":

        st.info(
            "The selected drug determines the "
            "prototype colour interpretation. "
            "It cannot identify an unknown substance."
        )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "← Back",
            use_container_width=True
        ):

            st.session_state.page = (
                "home"
            )

            st.rerun()

    with c2:

        if st.button(
            "CONTINUE TO CAMERA →",
            type="primary",
            use_container_width=True
        ):

            if drug == "Choose a drug":

                st.error(
                    "Please choose a suspected drug."
                )

            else:

                st.session_state.test_drug = (
                    drug
                )

                st.session_state.test_batch = (
                    batch.strip()
                    if batch.strip()
                    else "Not recorded"
                )

                st.session_state.page = (
                    "camera"
                )

                st.rerun()


# ============================================================
# GPS
# ============================================================

def get_current_location():

    lat = None
    lon = None

    if get_geolocation is None:

        return (
            None,
            None,
            "GPS component unavailable."
        )

    try:

        location = get_geolocation()

        if not location:

            return (
                None,
                None,
                "Waiting for GPS permission..."
            )

        # Browser/component error

        if "error" in location:

            error = location.get(
                "error",
                {}
            )

            code = error.get(
                "code"
            )

            message = error.get(
                "message",
                "Unable to obtain location."
            )

            if code == 1:

                return (
                    None,
                    None,
                    "Location permission was denied."
                )

            return (
                None,
                None,
                message
            )

        # Normal format

        if "coords" in location:

            coords = location[
                "coords"
            ]

            latitude = coords.get(
                "latitude"
            )

            longitude = coords.get(
                "longitude"
            )

            if (
                latitude is not None
                and
                longitude is not None
            ):

                lat, lon = normalize_location(
                    latitude,
                    longitude
                )

                return (
                    lat,
                    lon,
                    "GPS location captured automatically."
                )

        # Fallback format

        latitude = location.get(
            "latitude"
        )

        longitude = location.get(
            "longitude"
        )

        if (
            latitude is not None
            and
            longitude is not None
        ):

            lat, lon = normalize_location(
                latitude,
                longitude
            )

            return (
                lat,
                lon,
                "GPS location captured automatically."
            )

    except Exception as e:

        return (
            None,
            None,
            f"GPS error: {e}"
        )

    return (
        None,
        None,
        "Waiting for GPS location..."
    )


# ============================================================
# CAMERA
# ============================================================

def camera():

    header()

    steps(3)

    st.subheader(
        "Take a test photo"
    )

    st.caption(
        f'{st.session_state.test_drug} · '
        f'Batch {st.session_state.test_batch}'
    )

    st.markdown(
        '<div class="meta-card">'
        '<b>Positioning guide</b><br>'
        'Reference colour card on the <b>LEFT</b>, '
        'test strip/reaction area on the <b>RIGHT</b>. '
        'Keep both visible, flat and well lit.'
        '</div>',
        unsafe_allow_html=True
    )

    # Reference guide

    try:

        st.image(
            "assets/reference_card_guide.png",
            use_container_width=True
        )

    except Exception:

        st.warning(
            "Reference guide image not found."
        )

    # Camera

    captured = st.camera_input(
        "Camera"
    )

    uploaded = st.file_uploader(
        "Or upload a saved test photo",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    image = (
        captured
        or uploaded
    )

    if image is not None:

        st.image(
            image,
            caption="Captured image",
            use_container_width=True
        )

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        st.subheader(
            "Location"
        )

        lat, lon, gps_message = (
            get_current_location()
        )

        if (
            lat is not None
            and
            lon is not None
        ):

            st.markdown(
                f'<div class="gps-card">'
                f'<b>📍 GPS location captured automatically</b><br>'
                f'Latitude: {lat:.6f}<br>'
                f'Longitude: {lon:.6f}'
                f'</div>',
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f'<div class="gps-wait">'
                f'📍 {gps_message}<br>'
                f'Please allow location access in your browser.'
                f'</div>',
                unsafe_allow_html=True
            )

        # Manual fallback

        c1, c2 = st.columns(2)

        with c1:

            latm = st.text_input(
                "Latitude (optional)",
                value=(
                    ""
                    if lat is None
                    else str(lat)
                )
            )

        with c2:

            lonm = st.text_input(
                "Longitude (optional)",
                value=(
                    ""
                    if lon is None
                    else str(lon)
                )
            )

        if (
            lat is None
            and
            latm
            and
            lonm
        ):

            try:

                lat, lon = normalize_location(
                    latm,
                    lonm
                )

            except Exception:

                st.warning(
                    "Please enter valid latitude "
                    "and longitude."
                )

        # ----------------------------------------------------
        # PROCESS
        # ----------------------------------------------------

        if st.button(
            "PROCESS PHOTO →",
            type="primary",
            use_container_width=True
        ):

            try:

                raw = image.getvalue()

                decoded_image = decode_image(
                    raw
                )

                cv = analyze_image(
                    decoded_image
                )

                # Store image

                st.session_state.test_image = (
                    raw
                )

                # Store CV result

                st.session_state.test_cv = (
                    cv
                )

                # Timestamp

                st.session_state.test_time = (
                    datetime.now()
                    .astimezone()
                    .strftime(
                        "%d %b %Y, %I:%M:%S %p %Z"
                    )
                )

                # GPS

                st.session_state.test_lat = (
                    lat
                )

                st.session_state.test_lon = (
                    lon
                )

                # Record ID

                st.session_state.test_record_id = (
                    "FTC-"
                    + uuid.uuid4().hex[:10].upper()
                )

                # Image SHA-256

                st.session_state.test_image_hash = (
                    sha256_bytes(
                        raw
                    )
                )

                # Go to result

                st.session_state.page = (
                    "result"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not process image: {e}"
                )


# ============================================================
# RESULT
# ============================================================

def result():

    header()

    steps(4)

    st.subheader(
        "Review result"
    )

    cv = st.session_state.test_cv

    # Result card

    st.markdown(
        f'<div class="result">'
        f'<h2>{cv["result"]}</h2>'
        f'<div>Prototype confidence: '
        f'<b>{cv["confidence"]:.1f}%</b></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Annotated image

    st.image(
        encode_jpeg(
            cv["annotated"]
        ),
        caption=(
            "Processed image — detected "
            "reference and test regions"
        ),
        use_container_width=True
    )

    # Explanation

    st.write(
        cv["explanation"]
    )

    # Metrics

    a, b, c = st.columns(3)

    with a:

        st.metric(
            "Sample R",
            f'{cv["sample_rgb"]["r"]:.0f}'
        )

        st.metric(
            "Sample G",
            f'{cv["sample_rgb"]["g"]:.0f}'
        )

    with b:

        st.metric(
            "Sample B",
            f'{cv["sample_rgb"]["b"]:.0f}'
        )

        st.metric(
            "Hue",
            f'{cv["sample_hsv"]["h"]:.0f}'
        )

    with c:

        st.metric(
            "Saturation",
            f'{cv["sample_hsv"]["s"]:.0f}'
        )

        st.metric(
            "Lighting factor",
            f'{cv["lighting_factor"]:.2f}'
        )

    # GPS

    lat = st.session_state.test_lat

    lon = st.session_state.test_lon

    if (
        lat is not None
        and
        lon is not None
    ):

        gps = (
            f"{lat:.6f}, {lon:.6f}"
        )

    else:

        gps = "Not recorded"

    # Details

    details = {

        "Record ID":
            st.session_state.test_record_id,

        "Officer ID":
            st.session_state.officer_id,

        "Suspected drug":
            st.session_state.test_drug,

        "Kit batch":
            st.session_state.test_batch,

        "Timestamp":
            st.session_state.test_time,

        "GPS":
            gps,

        "Image SHA-256":
            st.session_state.test_image_hash
    }

    st.dataframe(
        pd.DataFrame(
            details.items(),
            columns=[
                "Field",
                "Value"
            ]
        ),
        hide_index=True,
        use_container_width=True
    )

    # Save

    if st.button(
        "SAVE & GENERATE REPORT →",
        type="primary",
        use_container_width=True
    ):

        base = {

            "record_id":
                st.session_state.test_record_id,

            "officer_id":
                st.session_state.officer_id,

            "drug":
                st.session_state.test_drug,

            "batch":
                st.session_state.test_batch,

            "result":
                cv["result"],

            "confidence":
                cv["confidence"],

            "timestamp":
                st.session_state.test_time,

            "latitude":
                lat,

            "longitude":
                lon,

            "image_hash":
                st.session_state.test_image_hash,

            "explanation":
                cv["explanation"]
        }

        # Record hash

        rh = record_hash(
            base
        )

        # Full record

        test = {

            **base,

            "record_hash":
                rh,

            "cv_data": {

                "sample_rgb":
                    cv["sample_rgb"],

                "sample_hsv":
                    cv["sample_hsv"],

                "lighting_factor":
                    cv["lighting_factor"]
            }
        }

        # Save

        save_test(
            test
        )

        # Save hash

        st.session_state.test_record_hash = (
            rh
        )

        # Generate PDF

        st.session_state.test_pdf = (
            build_pdf(
                test,
                st.session_state.test_image
            )
        )

        # Go to report

        st.session_state.page = (
            "report"
        )

        st.rerun()


# ============================================================
# REPORT
# ============================================================

def report():

    header()

    steps(5)

    st.subheader(
        "Digital record created"
    )

    st.success(
        "Test saved locally and a tamper-evident "
        "record was generated."
    )

    st.write(
        "Record SHA-256 hash:"
    )

    st.code(
        st.session_state.test_record_hash,
        language="text"
    )

    # PDF

    st.download_button(
        "⬇ DOWNLOAD PDF REPORT",

        data=st.session_state.test_pdf,

        file_name=(
            f'{st.session_state.test_record_id}.pdf'
        ),

        mime="application/pdf",

        type="primary",

        use_container_width=True
    )

    # Existing records

    rows = list_tests()

    if rows:

        df = pd.DataFrame(
            rows
        )

        required_columns = [

            "record_id",

            "officer_id",

            "drug",

            "result",

            "confidence",

            "timestamp",

            "latitude",

            "longitude"
        ]

        available_columns = [

            column

            for column in required_columns

            if column in df.columns
        ]

        st.dataframe(
            df[available_columns],
            hide_index=True,
            use_container_width=True
        )

    # Buttons

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "START NEW TEST",
            use_container_width=True
        ):

            reset()

            st.session_state.page = (
                "new_test"
            )

            st.rerun()

    with c2:

        if st.button(
            "VIEW ALL RECORDS",
            use_container_width=True
        ):

            st.session_state.page = (
                "records"
            )

            st.rerun()


# ============================================================
# RECORDS
# ============================================================

def records():

    header()

    st.subheader(
        "Test records"
    )

    search = st.text_input(
        "Search records",

        placeholder=(
            "Officer, drug, result, "
            "batch or record ID"
        )
    )

    rows = list_tests(
        search
    )

    if rows:

        df = pd.DataFrame(
            rows
        )

        columns = [

            "record_id",

            "officer_id",

            "drug",

            "batch",

            "result",

            "confidence",

            "timestamp",

            "latitude",

            "longitude",

            "image_hash",

            "record_hash"
        ]

        available_columns = [

            column

            for column in columns

            if column in df.columns
        ]

        st.dataframe(
            df[available_columns],

            hide_index=True,

            use_container_width=True
        )

    else:

        st.info(
            "No records found."
        )

    if st.button(
        "← BACK TO NEW TEST",
        use_container_width=True
    ):

        st.session_state.page = (
            "new_test"
        )

        st.rerun()


# ============================================================
# PAGE ROUTING
# ============================================================

if "page" not in st.session_state:

    st.session_state.page = "home"


page = st.session_state.page


pages = {

    "home":
        home,

    "new_test":
        new_test,

    "camera":
        camera,

    "result":
        result,

    "report":
        report,

    "records":
        records
}


pages.get(
    page,
    home
)()