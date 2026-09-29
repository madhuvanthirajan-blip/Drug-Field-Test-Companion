import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

from config import APP_NAME, DRUGS

from cv_engine.calibration import decode_image
from cv_engine.classifier import analyze_image

from services.hash_service import sha256_bytes, record_hash
from services.pdf_service import build_pdf
from services.storage_service import init_db, save_test, list_tests

try:
    from streamlit_js_eval import get_geolocation
    GEO_AVAILABLE = True
except Exception:
    GEO_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PROFESSIONAL RESPONSIVE CSS
# ============================================================

st.markdown(
    """
    <style>

    /* =====================================================
       MAIN APPLICATION BACKGROUND
       ===================================================== */

    .stApp {
        background-color: #f5f7fa !important;
    }

    .main {
        background-color: #f5f7fa !important;
    }

    .block-container {
        max-width: 920px !important;
        padding-top: 0.8rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }


    /* =====================================================
       STREAMLIT TOP HEADER
       Make Deploy area blend with application
       ===================================================== */

    [data-testid="stHeader"] {
        background-color: #f5f7fa !important;
        border-bottom: 1px solid #e5e7eb !important;
        box-shadow: none !important;
    }

    [data-testid="stToolbar"] {
        background-color: transparent !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }


    /* =====================================================
       GLOBAL TEXT
       ===================================================== */

    .stApp {
        color: #172033 !important;
    }

    .stApp p,
    .stApp span,
    .stApp label,
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6 {
        color: #172033 !important;
    }


    /* =====================================================
       CAPTIONS
       ===================================================== */

    [data-testid="stCaptionContainer"] {
        color: #687386 !important;
    }

    [data-testid="stCaptionContainer"] p {
        color: #687386 !important;
    }


    /* =====================================================
       MAIN TITLE
       ===================================================== */

    .app-title-text {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.5px;
        color: #172033;
        margin-top: 0;
        margin-bottom: 0.2rem;
    }


    /* =====================================================
       HEADINGS
       ===================================================== */

    h1 {
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.45rem !important;
        font-weight: 750 !important;
    }

    h3 {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
    }


    /* =====================================================
       INPUTS
       ===================================================== */

    input,
    textarea {
        background-color: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #d8dee8 !important;
        border-radius: 10px !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #8a94a6 !important;
    }


    /* =====================================================
       SELECT BOX
       ===================================================== */

    [data-baseweb="select"] {
        background-color: #ffffff !important;
        border-radius: 10px !important;
    }

    [data-baseweb="select"] * {
        color: #172033 !important;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {
        width: 100%;
        min-height: 46px;
        border-radius: 11px !important;
        border: 1px solid #d7dce5 !important;
        background-color: #ffffff !important;
        color: #172033 !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
        box-shadow: none !important;
    }

    .stButton > button:hover {
        border-color: #4f46e5 !important;
        color: #4f46e5 !important;
    }

    .stButton > button[kind="primary"] {
        background-color: #4f46e5 !important;
        border-color: #4f46e5 !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: #ffffff !important;
    }


    /* =====================================================
       CAMERA
       ===================================================== */

    [data-testid="stCameraInput"] {
        background-color: #ffffff !important;
        border-radius: 14px !important;
        padding: 0.5rem !important;
    }


    /* =====================================================
       FILE UPLOADER
       ===================================================== */

    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
    }


    /* =====================================================
       METRICS
       ===================================================== */

    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e5ec !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
    }

    [data-testid="stMetricLabel"] {
        color: #687386 !important;
    }

    [data-testid="stMetricValue"] {
        color: #172033 !important;
    }


    /* =====================================================
       DATAFRAME
       ===================================================== */

    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden !important;
    }


    /* =====================================================
       DIVIDERS
       ===================================================== */

    hr {
        border: none !important;
        border-top: 1px solid #e1e5eb !important;
        margin: 1rem 0 !important;
    }


    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 600px) {

        .block-container {
            max-width: 100% !important;
            padding-top: 0.5rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }

        .app-title-text {
            font-size: 1.65rem;
        }

        h1 {
            font-size: 1.6rem !important;
        }

        h2 {
            font-size: 1.3rem !important;
        }

        .stButton > button {
            min-height: 48px !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "home",
    "officer_id": "",
    "drug": "",
    "batch": "",
    "image_bytes": None,
    "processed_image": None,
    "result": None,
    "confidence": 0.0,
    "notes": "",
    "latitude": None,
    "longitude": None,
    "record_id": None,
    "timestamp": None,
    "image_hash": None,
    "record_hash": None,
    "report_bytes": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HEADER
# ============================================================

def header():

    # Native Streamlit components only.
    # No custom HTML is used here.

    st.markdown("### 🛡️")

    st.markdown(
        '<div class="app-title-text">Field Test Companion</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Digital companion for field drug testing"
    )


# ============================================================
# PROGRESS
# ============================================================

def progress_bar(step):

    labels = [
        "Officer",
        "Test details",
        "Photo",
        "Result",
        "Report",
    ]

    st.progress(step / 5)

    st.caption(
        f"STEP {step} OF 5  •  {labels[step - 1]}"
    )


# ============================================================
# PAGE TITLE
# ============================================================

def page_title(title, subtitle=None):

    st.subheader(title)

    if subtitle:
        st.caption(subtitle)


# ============================================================
# RESET TEST
# ============================================================

def reset_test():

    officer = st.session_state.get(
        "officer_id",
        "",
    )

    for key, value in DEFAULTS.items():

        if key == "officer_id":
            continue

        st.session_state[key] = value

    st.session_state.officer_id = officer
    st.session_state.page = "new_test"


# ============================================================
# LOCATION
# ============================================================

def get_browser_location():

    latitude = None
    longitude = None

    if not GEO_AVAILABLE:
        return latitude, longitude

    try:

        location = get_geolocation()

        if location:

            coords = location.get(
                "coords",
                {},
            )

            latitude = coords.get(
                "latitude"
            )

            longitude = coords.get(
                "longitude"
            )

    except Exception:
        pass

    return latitude, longitude


# ============================================================
# HOME
# ============================================================

def home():

    header()

    progress_bar(1)

    st.divider()

    page_title(
        "Officer identification",
        "Enter the officer ID to begin a new field test.",
    )

    officer_id = st.text_input(
        "Officer ID",
        value=st.session_state.officer_id,
        placeholder="Example: OFF-1024",
        max_chars=50,
    )

    st.session_state.officer_id = officer_id.strip()

    st.write("")

    if st.button(
        "Continue →",
        type="primary",
        use_container_width=True,
    ):

        if not st.session_state.officer_id:

            st.error(
                "Please enter the officer ID."
            )

        else:

            st.session_state.page = "new_test"
            st.rerun()

    st.write("")

    with st.container(border=True):

        st.markdown(
            "### Prototype notice"
        )

        st.caption(
            "This system is a prototype decision-support "
            "tool. Field test results should not be treated "
            "as definitive laboratory confirmation."
        )


# ============================================================
# NEW TEST
# ============================================================

def new_test():

    header()

    progress_bar(2)

    st.divider()

    page_title(
        "Test details",
        "Select the suspected substance before taking the test image.",
    )

    drug_options = [
        "Select a drug"
    ] + list(DRUGS)

    if st.session_state.drug in DRUGS:

        selected_index = drug_options.index(
            st.session_state.drug
        )

    else:

        selected_index = 0

    st.session_state.drug = st.selectbox(
        "Suspected drug",
        options=drug_options,
        index=selected_index,
    )

    st.session_state.batch = st.text_input(
        "Batch / sample reference (optional)",
        value=st.session_state.batch,
        placeholder="Example: SAMPLE-2026-001",
    )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "← Back",
            use_container_width=True,
        ):

            st.session_state.page = "home"
            st.rerun()

    with col2:

        if st.button(
            "Continue →",
            type="primary",
            use_container_width=True,
        ):

            if st.session_state.drug == "Select a drug":

                st.error(
                    "Please select a suspected drug."
                )

            else:

                st.session_state.page = "camera"
                st.rerun()


# ============================================================
# CAMERA
# ============================================================

def camera():

    header()

    progress_bar(3)

    st.divider()

    page_title(
        "Capture test image",
        "Place the reference colour card and test strip clearly inside the frame.",
    )

    with st.container(border=True):

        st.markdown(
            "### Before taking the photo"
        )

        st.markdown(
            """
            - Keep the reference colour card visible.
            - Keep the test strip completely visible.
            - Use good, even lighting.
            - Avoid shadows and reflections.
            - Keep the camera steady.
            """
        )

    st.write("")

    st.markdown("### Camera")

    camera_image = st.camera_input(
        "Take test photo",
        key="camera_input",
    )

    st.caption(
        "On mobile, this opens the phone camera. "
        "On a laptop, use the webcam if available."
    )

    with st.expander(
        "Use an existing image instead"
    ):

        uploaded_image = st.file_uploader(
            "Upload test image",
            type=[
                "jpg",
                "jpeg",
                "png",
            ],
            key="uploaded_test_image",
        )

    selected_image = (
        camera_image
        if camera_image is not None
        else uploaded_image
    )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    st.divider()

    st.markdown("### Location")

    latitude, longitude = (
        get_browser_location()
    )

    if (
        latitude is not None
        and longitude is not None
    ):

        st.session_state.latitude = latitude
        st.session_state.longitude = longitude

        st.success(
            f"Location captured: "
            f"{latitude:.6f}, "
            f"{longitude:.6f}"
        )

    else:

        st.info(
            "Automatic location is unavailable. "
            "You can enter coordinates manually."
        )

        location_col1, location_col2 = (
            st.columns(2)
        )

        with location_col1:

            manual_lat = st.number_input(
                "Latitude",
                value=float(
                    st.session_state.latitude
                    or 0.0
                ),
                format="%.6f",
            )

        with location_col2:

            manual_lon = st.number_input(
                "Longitude",
                value=float(
                    st.session_state.longitude
                    or 0.0
                ),
                format="%.6f",
            )

        if (
            manual_lat != 0.0
            or manual_lon != 0.0
        ):

            st.session_state.latitude = manual_lat
            st.session_state.longitude = manual_lon

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if selected_image is not None:

        image_bytes = selected_image.getvalue()

        st.session_state.image_bytes = image_bytes

        st.divider()

        st.markdown("### Preview")

        st.image(
            image_bytes,
            caption="Captured test image",
            use_container_width=True,
        )

        st.write("")

        if st.button(
            "Analyze test →",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "Analyzing test image..."
            ):

                try:

                    image = decode_image(
                        image_bytes
                    )

                    if image is None:

                        st.error(
                            "The image could not be decoded."
                        )

                        return

                    analysis = analyze_image(
                        image,
                        st.session_state.drug,
                    )

                    if isinstance(
                        analysis,
                        dict,
                    ):

                        result = analysis.get(
                            "result",
                            analysis.get(
                                "classification",
                                "Inconclusive",
                            ),
                        )

                        confidence = analysis.get(
                            "confidence",
                            0.0,
                        )

                        processed = analysis.get(
                            "processed_image",
                            analysis.get(
                                "image",
                                image,
                            ),
                        )

                        notes = analysis.get(
                            "notes",
                            "",
                        )

                    else:

                        result = str(analysis)
                        confidence = 0.0
                        processed = image
                        notes = ""

                    st.session_state.result = (
                        str(result)
                    )

                    try:

                        st.session_state.confidence = (
                            float(
                                confidence or 0.0
                            )
                        )

                    except Exception:

                        st.session_state.confidence = 0.0

                    st.session_state.processed_image = (
                        processed
                    )

                    st.session_state.notes = str(
                        notes
                    )

                    st.session_state.timestamp = (
                        datetime.now().isoformat()
                    )

                    st.session_state.image_hash = (
                        sha256_bytes(
                            image_bytes
                        )
                    )

                    st.session_state.record_id = (
                        f"FTC-"
                        f"{uuid.uuid4().hex[:10].upper()}"
                    )

                    record_data = {

                        "record_id":
                            st.session_state.record_id,

                        "officer_id":
                            st.session_state.officer_id,

                        "drug":
                            st.session_state.drug,

                        "batch":
                            st.session_state.batch,

                        "result":
                            st.session_state.result,

                        "confidence":
                            st.session_state.confidence,

                        "timestamp":
                            st.session_state.timestamp,

                        "latitude":
                            st.session_state.latitude,

                        "longitude":
                            st.session_state.longitude,

                        "image_hash":
                            st.session_state.image_hash,
                    }

                    try:

                        st.session_state.record_hash = (
                            record_hash(
                                record_data
                            )
                        )

                    except Exception:

                        st.session_state.record_hash = (
                            sha256_bytes(
                                str(
                                    record_data
                                ).encode()
                            )
                        )

                    st.session_state.page = "result"

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Analysis failed: {e}"
                    )

    st.write("")

    if st.button(
        "← Back",
        use_container_width=True,
    ):

        st.session_state.page = "new_test"
        st.rerun()


# ============================================================
# RESULT
# ============================================================

def result():

    header()

    progress_bar(4)

    st.divider()

    page_title(
        "Test result",
        "Review the analysis before saving the digital record.",
    )

    result_value = (
        st.session_state.result
        or "Inconclusive"
    )

    confidence = (
        st.session_state.confidence
        or 0.0
    )

    result_lower = result_value.lower()

    if "positive" in result_lower:

        st.error(
            f"### Result: {result_value}"
        )

    elif "negative" in result_lower:

        st.success(
            f"### Result: {result_value}"
        )

    else:

        st.warning(
            f"### Result: {result_value}"
        )

    st.write("")

    metric_col1, metric_col2 = (
        st.columns(2)
    )

    with metric_col1:

        confidence_text = (
            f"{confidence * 100:.1f}%"
            if confidence <= 1
            else f"{confidence:.1f}%"
        )

        st.metric(
            "Confidence",
            confidence_text,
        )

    with metric_col2:

        st.metric(
            "Record ID",
            st.session_state.record_id
            or "—",
        )

    if (
        st.session_state.processed_image
        is not None
    ):

        st.divider()

        st.markdown(
            "### Processed image"
        )

        try:

            st.image(
                st.session_state.processed_image,
                use_container_width=True,
            )

        except Exception:
            pass

    st.divider()

    st.markdown(
        "### Test details"
    )

    details = pd.DataFrame(
        {
            "Field": [
                "Officer ID",
                "Suspected drug",
                "Batch / sample",
                "Timestamp",
                "Latitude",
                "Longitude",
            ],

            "Value": [
                st.session_state.officer_id,

                st.session_state.drug,

                st.session_state.batch or "—",

                st.session_state.timestamp or "—",

                (
                    f"{st.session_state.latitude:.6f}"
                    if st.session_state.latitude
                    is not None
                    else "—"
                ),

                (
                    f"{st.session_state.longitude:.6f}"
                    if st.session_state.longitude
                    is not None
                    else "—"
                ),
            ],
        }
    )

    st.dataframe(
        details,
        hide_index=True,
        use_container_width=True,
    )

    with st.container(border=True):

        st.markdown(
            "### Important"
        )

        st.caption(
            "This is a prototype field decision-support "
            "system. The result is presumptive and should "
            "not replace laboratory confirmation."
        )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "← Retake photo",
            use_container_width=True,
        ):

            st.session_state.page = "camera"
            st.session_state.result = None
            st.rerun()

    with col2:

        if st.button(
            "Save & generate report",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "Saving record..."
            ):

                try:

                    test_record = {

                        "record_id":
                            st.session_state.record_id,

                        "officer_id":
                            st.session_state.officer_id,

                        "drug":
                            st.session_state.drug,

                        "batch":
                            st.session_state.batch,

                        "result":
                            st.session_state.result,

                        "confidence":
                            st.session_state.confidence,

                        "timestamp":
                            st.session_state.timestamp,

                        "latitude":
                            st.session_state.latitude,

                        "longitude":
                            st.session_state.longitude,

                        "image_hash":
                            st.session_state.image_hash,

                        "record_hash":
                            st.session_state.record_hash,

                        "notes":
                            st.session_state.notes,
                    }

                    try:

                        save_test(
                            test_record
                        )

                    except TypeError:

                        save_test(
                            st.session_state.record_id,
                            st.session_state.officer_id,
                            st.session_state.drug,
                            st.session_state.result,
                            st.session_state.timestamp,
                        )

                    try:

                        pdf = build_pdf(
                            test_record
                        )

                    except TypeError:

                        pdf = build_pdf(
                            record_id=
                                st.session_state.record_id,

                            officer_id=
                                st.session_state.officer_id,

                            drug=
                                st.session_state.drug,

                            result=
                                st.session_state.result,

                            confidence=
                                st.session_state.confidence,

                            timestamp=
                                st.session_state.timestamp,

                            latitude=
                                st.session_state.latitude,

                            longitude=
                                st.session_state.longitude,

                            record_hash=
                                st.session_state.record_hash,
                        )

                    st.session_state.report_bytes = pdf

                    st.session_state.page = "report"

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to save record: {e}"
                    )


# ============================================================
# REPORT
# ============================================================

def report():

    header()

    progress_bar(5)

    st.divider()

    page_title(
        "Digital report",
        "The field test record has been saved.",
    )

    st.success(
        "Record saved successfully."
    )

    st.write("")

    with st.container(border=True):

        st.markdown(
            "### Record"
        )

        st.write(
            f"**Record ID:** "
            f"{st.session_state.record_id}"
        )

        st.write(
            f"**Officer:** "
            f"{st.session_state.officer_id}"
        )

        st.write(
            f"**Drug:** "
            f"{st.session_state.drug}"
        )

        st.write(
            f"**Result:** "
            f"{st.session_state.result}"
        )

        st.write(
            f"**Timestamp:** "
            f"{st.session_state.timestamp}"
        )

    st.write("")

    st.markdown(
        "### Tamper-evident record"
    )

    st.code(
        st.session_state.record_hash
        or "Unavailable",
        language="text",
    )

    st.caption(
        "SHA-256 hash generated for the digital record."
    )

    if st.session_state.report_bytes:

        st.write("")

        st.download_button(
            label="⬇ Download PDF report",
            data=st.session_state.report_bytes,
            file_name=(
                f"{st.session_state.record_id}.pdf"
            ),
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "＋ New test",
            type="primary",
            use_container_width=True,
        ):

            reset_test()
            st.rerun()

    with col2:

        if st.button(
            "View records",
            use_container_width=True,
        ):

            st.session_state.page = "records"
            st.rerun()


# ============================================================
# RECORDS
# ============================================================

def records():

    header()

    st.divider()

    page_title(
        "Test records",
        "Search previously saved field test records.",
    )

    try:

        records_data = list_tests()

    except Exception as e:

        st.error(
            f"Unable to load records: {e}"
        )

        records_data = []

    if records_data:

        if isinstance(
            records_data,
            pd.DataFrame,
        ):

            df = records_data.copy()

        else:

            df = pd.DataFrame(
                records_data
            )

        search = st.text_input(
            "Search",
            placeholder=(
                "Search officer, drug, "
                "result or record ID"
            ),
        )

        if search:

            search_lower = search.lower()

            mask = df.astype(str).apply(
                lambda row:
                    row.str.lower()
                    .str.contains(
                        search_lower,
                        na=False,
                    ).any(),
                axis=1,
            )

            df = df[mask]

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
        )

    else:

        with st.container(border=True):

            st.markdown(
                "### No records yet"
            )

            st.caption(
                "Completed field tests will appear here."
            )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "← Home",
            use_container_width=True,
        ):

            st.session_state.page = "home"
            st.rerun()

    with col2:

        if st.button(
            "＋ New test",
            type="primary",
            use_container_width=True,
        ):

            reset_test()
            st.rerun()


# ============================================================
# ROUTER
# ============================================================

if st.session_state.page == "home":

    home()

elif st.session_state.page == "new_test":

    new_test()

elif st.session_state.page == "camera":

    camera()

elif st.session_state.page == "result":

    result()

elif st.session_state.page == "report":

    report()

elif st.session_state.page == "records":

    records()

else:

    st.session_state.page = "home"
    st.rerun()