"""Run locally: streamlit run dashboard.py"""
from pathlib import Path
import tempfile
import time
import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO

st.set_page_config(page_title='HelmetGuard | Safety Monitor', page_icon='🛡️', layout='wide')
@st.cache_resource
def load_model(path):
    return YOLO(path)


def detect(model, frame, confidence):
    result = model(frame, conf=confidence, classes=[0, 2], verbose=False)[0]
    helmet = sum(int(b.cls.item()) == 0 for b in result.boxes)
    missing = sum(int(b.cls.item()) == 2 for b in result.boxes)
    return result.plot(), helmet, missing


def show_status(slot, helmets, missing):
    if missing:
        slot.error(f'⚠️ CHECK REQUIRED · {missing} no-helmet detection(s) in this frame')
    elif helmets:
        slot.success('✓ NO VIOLATION DETECTED · Helmet detected in this frame')
    else:
        slot.info('WAITING · No helmet or bare-head detections. Safety status is unknown.')

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">H</span>HelmetGuard</div>', unsafe_allow_html=True)
    st.caption('YOUR SAFETY, IN FOCUS')
    dark_mode = st.toggle('Dark mode', value=True, key='dark_mode', help='Switch between light and dark appearance.')
    st.divider()
    mode = st.radio('INSPECTION WORKSPACE', ['Image inspection', 'Video inspection', 'Live camera'])
    st.divider()
    with st.expander('Detection settings'):
        confidence = st.slider('Detection confidence', 0.1, 0.95, 0.5, 0.05)
        st.caption('Higher thresholds can reduce false alerts but miss more detections.')
    st.markdown('**Model** · Helmet / No helmet')
    st.caption('Prototype • Review alerts before taking action')

# Keep the selected appearance across widget reruns.
palette = {
    'bg': '#0c1017', 'surface': '#141a23', 'raised': '#1b2330',
    'text': '#edf2f7', 'muted': '#a3b0c2', 'line': '#303c4e',
    'accent': '#67e0bd', 'soft': '#18372f', 'shadow': '#00000024',
    'preview': '#101820', 'badge': '#8be4c9', 'on-accent': '#09291f',
    'danger': '#ffab98', 'warning-soft': '#38241f',
} if dark_mode else {
    'bg': '#f3f6fa', 'surface': '#ffffff', 'raised': '#f5f8fc',
    'text': '#1a2b43', 'muted': '#52647b', 'line': '#d5deea',
    'accent': '#087f70', 'soft': '#e4f5ef', 'shadow': '#253b5410',
    'preview': '#eef6f5', 'badge': '#13745c', 'on-accent': '#ffffff',
    'danger': '#a53622', 'warning-soft': '#fff0e9',
}
variables = ';'.join(f'--{name}:{value}' for name, value in palette.items())
scheme = 'dark' if dark_mode else 'light'
stylesheet = Path(__file__).with_name('dashboard.css').read_text(encoding='utf-8')
st.markdown(f'<style>:root {{{variables};color-scheme:{scheme}}}{stylesheet}</style>', unsafe_allow_html=True)

st.markdown('<div class="eyebrow">WORKSPACE &nbsp; / &nbsp; SAFETY OPERATIONS</div>', unsafe_allow_html=True)
st.markdown('<div class="page-heading"><h1>Safety, in focus<span class="heading-dot">.</span></h1><span class="ready-badge"><span class="ready-dot"></span> Local workspace</span></div>', unsafe_allow_html=True)
st.markdown('<p class="intro">Choose your footage. Spot missing helmets. Review what matters.</p>', unsafe_allow_html=True)
weights = Path(__file__).parent / 'models' / 'helmet.pt'
if not weights.exists():
    st.warning('Add your existing model at models/helmet.pt, then refresh this page.')
    st.stop()
model = load_model(str(weights))
if model.names.get(0) != 'Hardhat' or model.names.get(2) != 'NO-Hardhat':
    st.error('This dashboard expects the verified model with class 0 Hardhat and class 2 NO-Hardhat.')
    st.stop()

with st.container(border=True, key='source-panel'):
    st.markdown('<div class="eyebrow">INSPECTION SOURCE</div>', unsafe_allow_html=True)
    source = None
    temporary = None
    upload = None
    start = False
    if mode == 'Image inspection':
        upload_col, sample_col = st.columns([3, 1], gap='medium', vertical_alignment='center')
        with upload_col:
            upload = st.file_uploader('Upload inspection image', type=['jpg', 'jpeg', 'png'])
        with sample_col:
            st.caption('Explore with the bundled example')
            sample_path = Path(__file__).parent / 'test.jpg'
            if st.button('Try sample image', disabled=not sample_path.exists(), width='stretch', type='primary'):
                st.session_state['use_sample'] = True
    else:
        source_col, action_col = st.columns([3, 1], gap='medium', vertical_alignment='bottom')
        with source_col:
            if mode == 'Video inspection':
                upload = st.file_uploader('Upload a video', type=['mp4', 'avi', 'mov', 'mkv'])
                if upload:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(upload.name).suffix) as temp:
                        temp.write(upload.getbuffer())
                        temporary = Path(temp.name)
                    source = str(temporary)
            else:
                kind = st.radio('Camera connection', ['This computer’s webcam', 'Camera stream URL'], horizontal=True)
                if kind == 'This computer’s webcam':
                    source = int(st.number_input('Camera index', min_value=0, max_value=10, value=0))
                    st.caption('Uses the webcam on the computer running Streamlit.')
                else:
                    source = st.text_input('RTSP / HTTP camera stream URL', type='password', placeholder='rtsp://camera-address/stream')
                    st.caption('The camera stream must be reachable from this computer.')
        with action_col:
            start = st.button('Start inspection', type='primary', width='stretch', disabled=source is None or source == '')
            st.button('Stop inspection', width='stretch', help='Stops playback and releases the camera.')

with st.container(key='results-workspace'):
    left, right = st.columns([2.25, 1], gap='medium')
    with left, st.container(border=True, key='inspection-panel'):
        st.markdown('<div class="eyebrow">INSPECTION VIEWPORT</div>', unsafe_allow_html=True)
        st.subheader(mode)
        result_area = st.container()
    with right, st.container(border=True, key='summary-panel'):
        st.markdown('<div class="eyebrow">CURRENT FRAME</div>', unsafe_allow_html=True)
        st.subheader('Inspection overview')
        with st.container(key='frame-metrics'):
            helmet_col, missing_col = st.columns(2, gap='small')
            with helmet_col:
                helmet_metric = st.empty()
                helmet_metric.metric('Helmets detected', '—')
            with missing_col:
                missing_metric = st.empty()
                missing_metric.metric('Without helmet', '—')
            share_col, fps_col = st.columns(2, gap='small')
            with share_col:
                rate_metric = st.empty()
                rate_metric.metric('Helmet detection share', '—')
            with fps_col:
                speed_metric = st.empty()
                speed_metric.metric('Processing speed / FPS', '—')
        st.markdown('<div class="card-label status-label">DETECTION STATUS</div>', unsafe_allow_html=True)
        status = st.empty()
        status.info('Standby. Choose an input to start inspection.')
        st.markdown('''<div class="detection-legend"><div class="card-label">DETECTION LEGEND</div>
        <div class="legend-row"><span class="legend-dot green"></span><span>Helmet detected</span><span class="legend-tag">Hardhat</span></div>
        <div class="legend-row"><span class="legend-dot red"></span><span>Review required</span><span class="legend-tag">No helmet</span></div>
        </div>''', unsafe_allow_html=True)
        with st.expander('Inspection workflow'):
            st.markdown('''<div class="workflow-row"><span>01</span><div><strong>Connect your source</strong><p>Upload an image, video, or camera feed.</p></div></div>
            <div class="workflow-row"><span>02</span><div><strong>Review detections</strong><p>Check highlighted areas and frame counts.</p></div></div>
            <div class="workflow-row"><span>03</span><div><strong>Take informed action</strong><p>Verify flagged detections on your site.</p></div></div>''', unsafe_allow_html=True)
        st.caption('Counts are detections per frame, not unique workers. Helmet detection share is not site compliance.')


def render(frame):
    tick = time.perf_counter()
    annotated, helmets, missing = detect(model, frame, confidence)
    elapsed = time.perf_counter() - tick
    show_status(status, helmets, missing)
    helmet_metric.metric('Helmets detected', helmets)
    missing_metric.metric('Without helmet', missing)
    total = helmets + missing
    rate_metric.metric('Helmet detection share', f'{helmets / total:.0%}' if total else '—')
    speed_metric.metric('Processing speed / FPS', f'{1 / max(elapsed, 0.001):.1f}')
    return annotated


with result_area:
    if mode == 'Image inspection':
        use_sample = st.session_state.get('use_sample', False)
        if upload or use_sample:
            image_bytes = upload.getvalue() if upload else sample_path.read_bytes()
            frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                st.error('Cannot read this image. Try another JPG or PNG.')
            else:
                annotated = render(frame)
                detection_tab, original_tab = st.tabs(['Detection result', 'Original image'])
                detection_tab.image(annotated, channels='BGR', width='stretch')
                original_tab.image(frame, channels='BGR', width='stretch')
                ok, encoded = cv2.imencode('.jpg', annotated)
                if ok:
                    st.download_button('Download annotated image', encoded.tobytes(), 'helmetguard-result.jpg', 'image/jpeg')
        else:
            st.markdown('''<div class="empty-state"><div class="preview-label"><span class="preview-dot"></span> INSPECTION VIEWPORT <span class="preview-state">AWAITING INPUT</span></div><div class="viewfinder"><span></span></div><h3>Ready when you are</h3><p>Add an image above to begin your safety inspection.<br>Your annotated results will appear here.</p><div class="preview-formats">JPG &nbsp; / &nbsp; PNG &nbsp; / &nbsp; JPEG</div></div>''', unsafe_allow_html=True)
    else:
        viewer = st.empty()
        if not start:
            viewer.markdown('<div class="empty-state"><div class="viewfinder"><span></span></div><h3>Your feed will appear here</h3><p>Choose a source above and select Start inspection.</p></div>', unsafe_allow_html=True)
        if start:
            cap = cv2.VideoCapture(source)
            try:
                if not cap.isOpened():
                    status.error('CONNECTION FAILED · Check the file, camera permissions, or stream URL.')
                else:
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    delay = 1 / fps if mode == 'Video inspection' and 0 < fps < 200 else 0
                    while cap.isOpened():
                        tick = time.perf_counter()
                        success, frame = cap.read()
                        if not success:
                            if mode == 'Video inspection':
                                st.info('Video finished. Status and counts refer to the last processed frame.')
                            else:
                                status.warning('DISCONNECTED · Camera frames are unavailable.')
                            break
                        viewer.image(render(frame), channels='BGR', width='stretch')
                        time.sleep(max(0, delay - (time.perf_counter() - tick)))
            except Exception:
                status.error('Inspection failed. Check the video format or camera connection and try again.')
            finally:
                cap.release()
                if temporary:
                    temporary.unlink(missing_ok=True)
        elif temporary:
            temporary.unlink(missing_ok=True)
        st.caption('Video is processed frame by frame without audio. CPU processing may be slower than the original video.')

st.markdown('<div class="section-note">HelmetGuard &nbsp; / &nbsp; Visual safety monitoring &nbsp; · &nbsp; Review detections before taking action.</div>', unsafe_allow_html=True)
