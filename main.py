import json
import os
import threading
import speech_recognition as sr
import flet as ft

def normalize_arabic(text: str) -> str:
    """إزالة التشكيل وتوحيد الحروف للمطابقة الإملائية الدقيقة"""
    noise = ['َ', 'ً', 'ُ', 'ٌ', 'ِ', 'ٍ', 'ْ', 'ّ', 'ـ']
    for char in noise:
        text = text.replace(char, '')
    
    text = (text.replace('أ', 'ا')
                .replace('إ', 'ا')
                .replace('آ', 'ا')
                .replace('ة', 'ه')
                .replace('ى', 'ي'))
    return text.strip()


def main(page: ft.Page):
    # --- إعدادات الصفحة الرئيسية ---
    page.title = "تطبيق القرآن الكريم والتسميع"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- تحميل ملف البيانات JSON ---
    json_path = os.path.join(os.path.dirname(__file__), 'assets', 'quran.json')
    if not os.path.exists(json_path):
        json_path = 'assets/quran.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        surahs = json.load(f)

    # --- المتغيرات الحالية لربط الحالة ---
    current_surah_idx = 0
    current_verse_idx = 0
    memorized_verses = set()
    is_listening = False
    is_hidden = False

    # --- عناصر الواجهة (UI Controls) ---
    surah_title = ft.Text(size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
    verse_text = ft.Text(size=26, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER)
    verse_number = ft.Text(size=16, weight=ft.FontWeight.BOLD)

    status_icon = ft.Icon(ft.Icons.MIC, color=ft.Colors.RED_500, visible=False)
    status_text = ft.Text(size=14, weight=ft.FontWeight.W_500)
    
    status_card = ft.Container(
        content=ft.Row([status_icon, status_text], alignment=ft.MainAxisAlignment.CENTER),
        padding=10,
        border_radius=10,
        visible=False,
        width=360
    )

    # --- دالة تحديث حالة الصفحة بأمان ---
    def update_ui():
        nonlocal is_hidden
        try:
            surah = surahs[current_surah_idx]
            verse = surah['verses'][current_verse_idx]
            v_id = verse['id']

            surah_title.value = f"سورة {surah['name_ar']}"
            verse_number.value = f"﴿ آية {v_id} ﴾"

            if is_hidden:
                verse_text.value = "• • • • • • • • • • • • • • •"
                hide_button.text = "إظهار"
                hide_button.icon = ft.Icons.VISIBILITY
            else:
                verse_text.value = verse['text']
                hide_button.text = "إخفاء"
                hide_button.icon = ft.Icons.VISIBILITY_OFF

            if v_id in memorized_verses:
                verse_text.color = ft.Colors.GREEN_600
                save_button.text = "محفوظة"
                save_button.icon = ft.Icons.CHECK_CIRCLE
                save_button.style = ft.ButtonStyle(color=ft.Colors.GREEN_700)
            else:
                verse_text.color = None
                save_button.text = "حفظ"
                save_button.icon = ft.Icons.CHECK_CIRCLE_OUTLINE
                save_button.style = ft.ButtonStyle(color=ft.Colors.BLUE_700)

            page.update()
        except Exception:
            pass

    # --- دالات التفاعل بالأزرار ---
    def toggle_hide(e):
        nonlocal is_hidden
        is_hidden = not is_hidden
        update_ui()

    def toggle_memorized(e):
        v_id = surahs[current_surah_idx]['verses'][current_verse_idx]['id']
        if v_id in memorized_verses:
            memorized_verses.remove(v_id)
        else:
            memorized_verses.add(v_id)
        update_ui()

    # --- معالجة التسميع الصوتي بخلفية مستقلة (Thread) ---
    def listen_worker(target_text, v_id):
        nonlocal is_listening, is_hidden
        recognizer = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

            status_text.value = "جاري المطابقة..."
            page.update()

            spoken_text = recognizer.recognize_google(audio, language="ar-SA")

            clean_target = normalize_arabic(target_text)
            clean_spoken = normalize_arabic(spoken_text)

            if clean_target in clean_spoken or clean_spoken in clean_target:
                memorized_verses.add(v_id)
                is_hidden = False
                status_card.bgcolor = ft.Colors.GREEN_100
                status_icon.name = ft.Icons.CHECK_CIRCLE
                status_icon.color = ft.Colors.GREEN_700
                status_text.value = f"التسميع صحيح! تم حفظ الآية {v_id}"
                status_text.color = ft.Colors.GREEN_900
            else:
                status_card.bgcolor = ft.Colors.ORANGE_100
                status_icon.name = ft.Icons.WARNING
                status_icon.color = ft.Colors.ORANGE_800
                status_text.value = f"غير مطابق: {spoken_text}"
                status_text.color = ft.Colors.ORANGE_900

        except sr.WaitTimeoutError:
            status_card.bgcolor = ft.Colors.GREY_200
            status_icon.name = ft.Icons.MIC_OFF
            status_icon.color = ft.Colors.GREY_700
            status_text.value = "لم يتم التقاط صوت"
            status_text.color = ft.Colors.BLACK
        except Exception:
            status_card.bgcolor = ft.Colors.RED_100
            status_icon.name = ft.Icons.ERROR
            status_icon.color = ft.Colors.RED_700
            status_text.value = "حدث خطأ في الميكروفون"
            status_text.color = ft.Colors.RED_900

        is_listening = False
        mic_button.text = "تسميع"
        mic_button.style = ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700)
        update_ui()

    def start_listening(e):
        nonlocal is_listening
        if is_listening:
            return

        is_listening = True
        v_id = surahs[current_surah_idx]['verses'][current_verse_idx]['id']
        target_text = surahs[current_surah_idx]['verses'][current_verse_idx]['text']

        status_card.visible = True
        status_card.bgcolor = ft.Colors.RED_50
        status_icon.visible = True
        status_icon.name = ft.Icons.MIC
        status_icon.color = ft.Colors.RED_600
        status_text.value = "جاري الاستماع... اتلُ الآن"
        status_text.color = ft.Colors.RED_700

        mic_button.text = "جاري الاستماع..."
        mic_button.style = ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_600)
        page.update()

        threading.Thread(target=listen_worker, args=(target_text, v_id), daemon=True).start()

    # --- دالات التنقل بين السور والآيات ---
    def prev_verse(e=None):
        nonlocal current_verse_idx, is_hidden
        if current_verse_idx > 0:
            current_verse_idx -= 1
            is_hidden = False
            status_card.visible = False
            update_ui()

    def next_verse(e=None):
        nonlocal current_verse_idx, is_hidden
        if current_verse_idx < len(surahs[current_surah_idx]['verses']) - 1:
            current_verse_idx += 1
            is_hidden = False
            status_card.visible = False
            update_ui()

    def prev_surah(e=None):
        nonlocal current_surah_idx, current_verse_idx, is_hidden
        if current_surah_idx > 0:
            current_surah_idx -= 1
            current_verse_idx = 0
            is_hidden = False
            status_card.visible = False
            update_ui()

    def next_surah(e=None):
        nonlocal current_surah_idx, current_verse_idx, is_hidden
        if current_surah_idx < len(surahs) - 1:
            current_surah_idx += 1
            current_verse_idx = 0
            is_hidden = False
            status_card.visible = False
            update_ui()

    # --- إنشاء عناصر التفاعل والتخطيط ---
    hide_button = ft.OutlinedButton("إخفاء", icon=ft.Icons.VISIBILITY_OFF, on_click=toggle_hide)
    save_button = ft.ElevatedButton("حفظ", icon=ft.Icons.CHECK_CIRCLE_OUTLINE, on_click=toggle_memorized)
    mic_button = ft.ElevatedButton(
        "تسميع",
        icon=ft.Icons.MIC,
        on_click=start_listening,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700)
    )

    verse_container = ft.Container(
        content=ft.Column([
            verse_text,
            ft.Container(height=10),
            verse_number
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=15,
        width=360,
        bgcolor=ft.Colors.WHITE,
    )

    surah_navigation = ft.Row([
        ft.TextButton("السورة السابقة", on_click=prev_surah),
        ft.TextButton("السورة التالية", on_click=next_surah),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=360)

    verse_navigation = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_FORWARD_IOS, on_click=prev_verse, tooltip="الآية السابقة"),
        ft.Row([hide_button, save_button, mic_button], spacing=4),
        ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS, on_click=next_verse, tooltip="الآية التالية"),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=360)

    # إدراج المكونات داخل الواجهة
    page.add(
        surah_navigation,
        ft.Container(height=5),
        surah_title,
        ft.Container(height=10),
        verse_container,
        ft.Container(height=10),
        status_card,
        ft.Container(height=10),
        verse_navigation
    )

    update_ui()

if __name__ == "__main__":
    ft.app(target=main)