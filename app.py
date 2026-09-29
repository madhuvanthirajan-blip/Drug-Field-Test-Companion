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
# OPTIONAL GPS
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
    layout="centered",
    initial_sidebar_state="collapsed"
)

init_db()


# ============================================================
# SIMPLE THEME
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #f5f8fa;
    }

    /* Keep content centered */
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Hide Streamlit decoration */
    [data-testid="stHeader"] {
        background: #f5f8fa;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 600;
    }

    /* Mobile */
    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
            padding-top: 1.5rem;
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

    st.title("🛡️ Field Test Companion")

    st.caption(
        "Digital companion for field drug testing"
    )

    st.divider()


# ============================================================
# STEP BAR
# NO HTML USED HERE
# ============================================================

def steps(active):

    labels = [
        "Officer",
        "Test details",
        "Take photo",
        "Result",
        "Report"
    ]

    columns = st.columns(5)

    for index, label in enumerate(labels, start=1):

        with columns[index - 1]:

            if index == active:

                st.success(
                    f"**{index}**\n\n**{label}**"
                )

            else:

                st.info(
                    f"**{index}**\n\n{label}"
                )

    st.write("")


# ============================================================
# RESET
# ============================================================

def reset():

    keys_to_remove = []

    for key in list(st.session_state.keys()):

        if key.startswith("test_"):
            keys_to_remove.append(key)

        if key in [
            "officer_id",
            "page"
        ]:
            keys_to_remove.append(key)

    for key in keys_to_remove:

        if key in st.session_state:
            del st.session_state[key]


# ============================================================
# HOME
# ============================================================

def home():

    header()

    steps(1)

    st.header("Officer workspace")

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

        if not officer.strip():

            st.error(
                "Please enter an Officer ID."
            )

        else:

            st.session_state.officer_id = (
                officer.strip()
            )

            st.session_state.page = "new_test"

            st.rerun()

    st.warning(
        "Prototype: Field-test output is presumptive "
        "and requires laboratory confirmation."
    )


# ============================================================
# NEW TEST
# ============================================================

def new_test():

    header()

    steps(2)

    st.header("Start a new test")

    st.caption(
        f"Field Officer · "
        f"{st.session_state.get('officer_id', '')}"
    )

    drug_options = [
        "Choose a drug"
    ] + list(DRUGS)

    drug = st.selectbox(
        "Suspected drug",
        drug_options
    )

    batch = st.text_input(
        "Kit batch / lot number (optional)",
        placeholder="As printed on the kit"
    )

    if drug != "Choose a drug":

        st.info(
            "The selected drug determines the prototype "
            "colour interpretation. This prototype cannot "
            "identify an unknown substance by itself."
        )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "← Back",
            use_container_width=True
        ):

            st.session_state.page = "home"
            st.rerun()

    with col2:

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
# CAMERA
# ============================================================

def camera():

    header()

    steps(3)

    st.header("Take a test photo")

    st.caption(
        f"{st.session_state.test_drug} · "
        f"Batch {st.session_state.test_batch}"
    )

    st.info(
        "Position the reference colour card on the LEFT "
        "and the test strip/reaction area on the RIGHT. "
        "Keep both visible, flat and well lit."
    )

    # --------------------------------------------------------
    # GUIDE IMAGE
    # --------------------------------------------------------

    try:

        st.image(
            "assets/reference_card_guide.png",
            use_container_width=True
        )

    except Exception:

        st.warning(
            "Reference guide image could not be loaded."
        )

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    captured = st.camera_input(
        "Take test photo"
    )

    uploaded = st.file_uploader(
        "Or upload a saved test photo",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    image = captured or uploaded

    if image is None:
        return

    # --------------------------------------------------------
    # SHOW IMAGE
    # --------------------------------------------------------

    st.image(
        image,
        caption="Captured test image",
        use_container_width=True
    )

    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    st.subheader("Location")

    lat = None
    lon = None

    if get_geolocation is not None:

        try:

            location = get_geolocation(
                component_key="field_test_gps"
            )

            if isinstance(location, dict):

                latitude = None
                longitude = None

                if "coords" in location:

                    coords = location.get(
                        "coords",
                        {}
                    )

                    latitude = coords.get(
                        "latitude"
                    )

                    longitude = coords.get(
                        "longitude"
                    )

                else:

                    latitude = location.get(
                        "latitude"
                    )

                    longitude = location.get(
                        "longitude"
                    )

                if (
                    latitude is not None
                    and longitude is not None
                ):

                    lat, lon = normalize_location(
                        latitude,
                        longitude
                    )

                    st.success(
                        f"GPS captured automatically\n\n"
                        f"Latitude: {lat:.6f}\n\n"
                        f"Longitude: {lon:.6f}"
                    )

                else:

                    st.info(
                        "Waiting for browser GPS permission..."
                    )

        except Exception:

            st.info(
                "Automatic GPS is unavailable. "
                "You can enter the coordinates manually."
            )

    else:

        st.info(
            "Automatic GPS component is unavailable. "
            "You can enter the coordinates manually."
        )

    # --------------------------------------------------------
    # MANUAL GPS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        lat_input = st.text_input(
            "Latitude (optional)",
            value=(
                ""
                if lat is None
                else str(lat)
            )
        )

    with col2:

        lon_input = st.text_input(
            "Longitude (optional)",
            value=(
                ""
                if lon is None
                else str(lon)
            )
        )

    if (
        lat is None
        and lat_input.strip()
        and lon_input.strip()
    ):

        try:

            lat, lon = normalize_location(
                lat_input,
                lon_input
            )

        except Exception:

            st.warning(
                "Please enter valid coordinates."
            )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    if st.button(
        "PROCESS PHOTO →",
        type="primary",
        use_container_width=True
    ):

        try:

            raw = image.getvalue()

            decoded = decode_image(
                raw
            )

            cv = analyze_image(
                decoded
            )

            # Store image
            st.session_state.test_image = raw

            # Store CV output
            st.session_state.test_cv = cv

            # Time
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
                + uuid.uuid4()
                .hex[:10]
                .upper()
            )

            # Image hash
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

    st.header("Review result")

    cv = st.session_state.test_cv

    result_value = str(
        cv.get(
            "result",
            "INCONCLUSIVE"
        )
    )

    confidence = float(
        cv.get(
            "confidence",
            0
        )
    )

    # --------------------------------------------------------
    # RESULT DISPLAY
    # --------------------------------------------------------

    if result_value.upper() == "POSITIVE":

        st.error(
            f"## {result_value}"
        )

    elif result_value.upper() == "NEGATIVE":

        st.success(
            f"## {result_value}"
        )

    else:

        st.warning(
            f"## {result_value}"
        )

    st.metric(
        "Prototype confidence",
        f"{confidence:.1f}%"
    )

    # --------------------------------------------------------
    # PROCESSED IMAGE
    # --------------------------------------------------------

    if "annotated" in cv:

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

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    if "explanation" in cv:

        st.write(
            cv["explanation"]
        )

    # --------------------------------------------------------
    # COLOUR DATA
    # --------------------------------------------------------

    st.subheader("Image analysis")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Sample R",
            f'{cv["sample_rgb"]["r"]:.0f}'
        )

        st.metric(
            "Sample G",
            f'{cv["sample_rgb"]["g"]:.0f}'
        )

    with col2:

        st.metric(
            "Sample B",
            f'{cv["sample_rgb"]["b"]:.0f}'
        )

        st.metric(
            "Hue",
            f'{cv["sample_hsv"]["h"]:.0f}'
        )

    with col3:

        st.metric(
            "Saturation",
            f'{cv["sample_hsv"]["s"]:.0f}'
        )

        st.metric(
            "Lighting factor",
            f'{cv["lighting_factor"]:.2f}'
        )

    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    lat = st.session_state.get(
        "test_lat"
    )

    lon = st.session_state.get(
        "test_lon"
    )

    if (
        lat is not None
        and lon is not None
    ):

        gps = (
            f"{lat:.6f}, {lon:.6f}"
        )

    else:

        gps = "Not recorded"

    # --------------------------------------------------------
    # TEST DETAILS
    # --------------------------------------------------------

    st.subheader("Test details")

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

    details_df = pd.DataFrame(
        details.items(),
        columns=[
            "Field",
            "Value"
        ]
    )

    st.dataframe(
        details_df,
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

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

        # Generate tamper-evident hash
        rh = record_hash(
            base
        )

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

        # Store hash
        st.session_state.test_record_hash = rh

        # Generate PDF
        st.session_state.test_pdf = build_pdf(
            test,
            st.session_state.test_image
        )

        # Report
        st.session_state.page = "report"

        st.rerun()


# ============================================================
# REPORT
# ============================================================

def report():

    header()

    steps(5)

    st.header(
        "Digital record created"
    )

    st.success(
        "Test saved locally and a tamper-evident "
        "record was generated."
    )

    st.subheader(
        "Record hash"
    )

    st.code(
        st.session_state.test_record_hash,
        language="text"
    )

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    st.download_button(
        label="⬇ DOWNLOAD PDF REPORT",
        data=st.session_state.test_pdf,
        file_name=(
            f"{st.session_state.test_record_id}.pdf"
        ),
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

    # --------------------------------------------------------
    # RECORDS
    # --------------------------------------------------------

    rows = list_tests()

    if rows:

        df = pd.DataFrame(
            rows
        )

        columns = [
            "record_id",
            "officer_id",
            "drug",
            "result",
            "confidence",
            "timestamp",
            "latitude",
            "longitude"
        ]

        available = [
            column
            for column in columns
            if column in df.columns
        ]

        st.subheader(
            "Recent test records"
        )

        st.dataframe(
            df[available],
            hide_index=True,
            use_container_width=True
        )

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "START NEW TEST",
            use_container_width=True
        ):

            reset()

            st.session_state.page = "new_test"

            st.rerun()

    with col2:

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

    st.header(
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

        available = [
            column
            for column in columns
            if column in df.columns
        ]

        st.dataframe(
            df[available],
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
# APP ROUTING
# ============================================================

if "page" not in st.session_state:

    st.session_state.page = "home"


page = st.session_state.page


if page == "home":

    home()

elif page == "new_test":

    new_test()

elif page == "camera":

    camera()

elif page == "result":

    result()

elif page == "report":

    report()

elif page == "records":

    records()

else:

    home()