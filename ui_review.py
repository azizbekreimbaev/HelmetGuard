"""Browser regression review. Run with the app listening on port 8501."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).parent
ARTIFACTS = ROOT / 'ui-review'
ARTIFACTS.mkdir(exist_ok=True)

def settle(page):
    expect(page.get_by_role('heading', name='Safety, in focus.')).to_be_visible(timeout=60000)
    expect(page.get_by_test_id('stException')).to_have_count(0)

def capture(page, name):
    page.wait_for_timeout(1000)
    page.get_by_test_id('stMain').evaluate('(e)=>e.scrollTo(0,0)')
    page.screenshot(path=str(ARTIFACTS / f'{name}.png'), full_page=True)
    overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert not overflow, f'Horizontal overflow: {name}'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440, 'height':1100}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://localhost:8501/')
    settle(page)
    nudge = page.get_by_role('button', name="Don't show again")
    if nudge.is_visible():
        nudge.click()
    toggle = page.get_by_role('switch', name='Dark mode')
    expect(toggle).to_be_checked()
    page.get_by_text('Detection settings', exact=True).click()
    expect(page.get_by_role('slider')).to_be_visible()
    page.get_by_role('slider').press('ArrowRight')
    settle(page)
    for theme in ['dark', 'light']:
        if theme == 'light':
            toggle.focus()
            toggle.press('Space')
            expect(toggle).not_to_be_checked()
        page.wait_for_timeout(700)
        capture(page, f'{theme}-desktop')
        for width in [1024, 768, 390]:
            page.set_viewport_size({'width':width,'height':1000})
            page.wait_for_timeout(300)
            capture(page, f'{theme}-{width}')
        page.set_viewport_size({'width':1440,'height':1100})
        sidebar = page.get_by_test_id('stSidebar')
        if sidebar.get_attribute('aria-expanded') == 'false':
            page.get_by_test_id('stExpandSidebarButton').click()
        page.get_by_role('button', name='Try sample image', exact=True).click()
        expect(page.get_by_role('tab', name='Detection result')).to_be_visible(timeout=60000)
        expect(page.get_by_test_id('stMetricValue').first).not_to_have_text('—')
        page.get_by_role('tab', name='Original image').click()
        with page.expect_download() as download:
            page.get_by_role('button', name='Download annotated image').click()
        assert download.value.suggested_filename == 'helmetguard-result.jpg'
        page.get_by_role('tab', name='Detection result', exact=True).click()
        viewport = page.locator('.st-key-inspection-panel').bounding_box()
        summary = page.locator('.st-key-summary-panel').bounding_box()
        assert viewport and summary
        assert summary['x'] >= viewport['x'] + viewport['width'], 'Summary must sit beside the result on desktop'
        assert abs(summary['y'] - viewport['y']) < 4, 'Result and summary must align at the top'
        expect(page.locator('.st-key-summary-panel').get_by_test_id('stMetric')).to_have_count(4)
        capture(page, f'{theme}-results')
        page.get_by_test_id('stRadioOption').filter(has_text='Video inspection').click()
        expect(page.get_by_role('button', name='Start inspection')).to_be_disabled()
        capture(page, f'{theme}-video')
        # A short real video exercises playback and end-of-file handling.
        import cv2
        clip = ARTIFACTS / 'short-test.avi'
        frame = cv2.imread(str(ROOT / 'test.jpg'))
        height, width = frame.shape[:2]
        writer = cv2.VideoWriter(str(clip), cv2.VideoWriter_fourcc(*'MJPG'), 5, (width, height))
        for _ in range(3):
            writer.write(frame)
        writer.release()
        page.locator('input[type=file]').set_input_files(str(clip))
        expect(page.get_by_role('button', name='Start inspection')).to_be_enabled()
        page.get_by_role('button', name='Start inspection').click()
        expect(page.get_by_text('Video finished.', exact=False)).to_be_visible(timeout=60000)
        page.get_by_role('button', name='Stop inspection').click()
        page.get_by_test_id('stRadioOption').filter(has_text='Live camera').click()
        expect(page.get_by_role('spinbutton', name='Camera index')).to_be_visible()
        page.get_by_test_id('stRadioOption').filter(has_text='Camera stream URL').click()
        expect(page.get_by_role('button', name='Start inspection')).to_be_disabled()
        page.get_by_label('RTSP / HTTP camera stream URL').fill('http://127.0.0.1:1/invalid')
        page.get_by_label('RTSP / HTTP camera stream URL').press('Enter')
        expect(page.get_by_role('button', name='Start inspection')).to_be_enabled()
        capture(page, f'{theme}-camera')
        page.get_by_role('button', name='Start inspection').click()
        expect(page.get_by_text('CONNECTION FAILED', exact=False)).to_be_visible(timeout=30000)
        page.get_by_test_id('stRadioOption').filter(has_text='Image inspection').click()
        settle(page)
        page.locator('input[type=file]').set_input_files(str(ROOT / 'test2.jpg'))
        expect(page.get_by_role('tab', name='Detection result')).to_be_visible(timeout=60000)
    assert not errors, errors
    (ARTIFACTS / 'result.json').write_text(json.dumps({'result':'passed','themes':2,'widths':[1440,1024,768,390],'browser_errors':errors}, indent=2))
    browser.close()
    print('PASS: themes, responsive layouts, settings, sample detection, tabs, download, video and camera controls.')
