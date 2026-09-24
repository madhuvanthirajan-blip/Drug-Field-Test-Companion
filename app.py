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

.stApp {
    background: #f5f8fa;
}

.block-container {
    max-width: 900px;
    padding-top: 3.25rem;
    padding-bottom: 3rem;
}

/* Streamlit top area */
[data-testid="stHeader"] {
    background: #f5f8fa !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
}

[data-testid="stDecoration"] {
    background: transparent !important;
}


/* ==========================================================
   HEADER
   ========================================================== */

.app-header {
    background: #0c4a63;
    color: white;
    padding: 20px 24px;
    border-radius: 14px;
    margin-bottom: 14px;
}

.app-header h1 {
    margin: 0;
    font-size: 30px;
    font-weight: 700;
}

.app-header p {
    margin: 5px 0 0;
    opacity: 0.88;
    font-size: 15px;
}


/* ==========================================================
   STEP BAR
   ========================================================== */

.stepbar {
    display: flex;
    gap: 8px;
    width: 100%;
    margin: 10px 0 18px 0;
}

.step {
    flex: 1;
    text-align: center;
    padding: 10px 4px;
    border-radius: 9px;
    background: #e2eaee;
    color: #3c4b52;
    font-size: 13px;
    line-height: 1.35;
    min-height: 52px;
    box-sizing: border-box;
}

.step.active {
    background: #0c4a63;
    color: white;
    font-weight: 700;
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
    background: white;
}

.result h2 {
    font-size: 34px;
    margin: 0;
}


/* ==========================================================
   DISCLAIMER
   ========================================================== */

.disclaimer {
    background: #fff8e8;
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
    background: white;
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
    border: 1px solid #c8e1e8;
    border-radius: 12px;
    padding: 14px;
    margin: 10px 0;
}

.gps-wait {
    background: #fff8e8;
    border-left: 4px solid #d99a18;
    padding: 12px;
    border-radius: 8px;
    margin: 10px 0;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

div.stButton > button {
    border-radius: 9px;
    min-height: 42px;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 600px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .app-header h1 {
        font-size: 24px;
    }

    .stepbar {
        gap: 4px;
    }

    .step {
        font-size: 10px;
        padding: 8px 2px;
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

    # Build every div as a single line.
    # This prevents Streamlit Markdown from treating
    # the indented HTML as a code block.

    step_items = []

    for i, label in enumerate(labels, start=1):

        if i == active:

            step_items.append(
                f'<div class="step active"><strong>{i}</strong><br>{label}</div>'
            )

        else:

            step_items.append(
                f'<div class="step"><strong>{i}</strong><br>{label}</div>'
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

    for key in list(st.session_state.keys()):

        if key.startswith("test_"):

            keys_to_remove.append(key)

        elif key in ["officer_id", "page"]:

            keys_to_remove.append(key)

    for key in keys_to_remove:

        st.session_state.pop(key, None)


# ============================================================
# HOME
# ============================================================

def home():

    header()

    steps(1)

    st.subheader("Officer workspace")

    officer = st.text_input(
        "Officer ID",
        value=st.session_state.get("officer_id", ""),
        placeholder="Example: OFF-001"
    )

    if st.button(
        "NEXT →",
        type="primary",
        use_container_width=True
    ):

        if officer.strip():

            st.session_state.officer_id = officer.strip()

            st.session_state.page = "new_test"

            st.rerun()

        else:

            st.error(
                "Please enter an Officer ID."
            )

    st.markdown(
        '<div class="disclaimer">'
        'Prototype • Field-test output is presumptive and requires '
        'laboratory confirmation.'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# NEW TEST
# ============================================================

def new_test():

    header()

    steps(2)

    st.subheader("Start a new test")

    st.caption(
        f"Field Officer · {st.session_state.officer_id}"
    )

    drug = st.selectbox(
        "Suspected drug",
        ["Choose a drug"] + DRUGS
    )

    batch = st.text_input(
        "Kit batch / lot number (optional)",
        placeholder="As printed on the kit"
    )

    if drug != "Choose a drug":

        st.info(
            "The selected drug determines the prototype "
            "colour interpretation. It cannot identify "
            "an unknown substance."
        )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "← Back",
            use_container_width=True
        ):

            st.session_state.page = "home"

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

                st.session_state.test_drug = drug

                st.session_state.test_batch = (
                    batch.strip()
                    if batch.strip()
                    else "Not recorded"
                )

                st.session_state.page = "camera"

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

            error = location.get("error", {})

            code = error.get("code")

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

        # Normal format:
        # {
        #   "coords": {
        #       "latitude": ...,
        #       "longitude": ...
        #   }
        # }

        if "coords" in location:

            coords = location["coords"]

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

    st.subheader("Take a test photo")

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
        type=["jpg", "jpeg", "png"]
    )

    image = captured or uploaded

    if image is not None:

        st.image(
            image,
            caption="Captured image",
            use_container_width=True
        )

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        st.subheader("Location")

        lat, lon, gps_message = get_current_location()

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
                value="" if lat is None else str(lat)
            )

        with c2:

            lonm = st.text_input(
                "Longitude (optional)",
                value="" if lon is None else str(lon)
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
                    "Please enter valid latitude and longitude."
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
                st.session_state.test_image = raw

                # Store CV result
                st.session_state.test_cv = cv

                # Timestamp
                st.session_state.test_time = (
                    datetime.now()
                    .astimezone()
                    .strftime(
                        "%d %b %Y, %I:%M:%S %p %Z"
                    )
                )

                # GPS
                st.session_state.test_lat = lat

                st.session_state.test_lon = lon

                # Record ID
                st.session_state.test_record_id = (
                    "FTC-"
                    + uuid.uuid4().hex[:10].upper()
                )

                # Image SHA-256
                st.session_state.test_image_hash = (
                    sha256_bytes(raw)
                )

                # Go to result
                st.session_state.page = "result"

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

    st.subheader("Review result")

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
        encode_jpeg(cv["annotated"]),
        caption=(
            "Processed image — detected reference "
            "and test regions"
        ),
        use_container_width=True
    )

    # Explanation

    st.write(
        cv["explanation"]
    )

    # Metrics

    a, b, c = st.columns(3)

    a.metric(
        "Sample R",
        f'{cv["sample_rgb"]["r"]:.0f}'
    )

    a.metric(
        "Sample G",
        f'{cv["sample_rgb"]["g"]:.0f}'
    )

    b.metric(
        "Sample B",
        f'{cv["sample_rgb"]["b"]:.0f}'
    )

    b.metric(
        "Hue",
        f'{cv["sample_hsv"]["h"]:.0f}'
    )

    c.metric(
        "Saturation",
        f'{cv["sample_hsv"]["s"]:.0f}'
    )

    c.metric(
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

        st.session_state.test_record_hash = rh

        # Generate PDF

        st.session_state.test_pdf = build_pdf(
            test,
            st.session_state.test_image
        )

        # Go to report

        st.session_state.page = "report"

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

            st.session_state.page = "new_test"

            st.rerun()

    with c2:

        if st.button(
            "VIEW ALL RECORDS",
            use_container_width=True
        ):

            st.session_state.page = "records"

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
            "Officer, drug, result, batch or record ID"
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

        st.session_state.page = "new_test"

        st.rerun()


# ============================================================
# PAGE ROUTING
# ============================================================

if "page" not in st.session_state:

    st.session_state.page = "home"


page = st.session_state.page


pages = {
    "home": home,
    "new_test": new_test,
    "camera": camera,
    "result": result,
    "report": report,
    "records": records
}


pages.get(
    page,
    home
)()