import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import base64
import requests
import time
import threading
import random

# ==============================================================================
# 1. INISIALISASI CLIENT AI 
# ==============================================================================
from groq import Groq

try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("⚠️ API Key Groq tidak ditemukan! Tambahkan GROQ_API_KEY di Streamlit Secrets.")
    st.stop()

# ==============================================================================
# 2. PENGATURAN HALAMAN
# ==============================================================================
st.set_page_config(page_title="AI Study Planner Pretty Pink Edition", layout="wide", page_icon="💖")

# ==============================================================================
# 3. INJECT CSS & VISUAL PINK 
# ==============================================================================
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

img_base64 = get_base64_image("wallpaper.jpeg")

if img_base64:
    bg_style = f"""
    html, body, [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(255, 230, 240, 0.82), rgba(255, 204, 221, 0.82)), url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """
else:
    bg_style = 'html, body, [data-testid="stAppViewContainer"] { background-color: #FFE6F0 !important; }'

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    {bg_style}
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        font-family: 'Inter', sans-serif !important;
        color: #2D1F24 !important;
    }}
    
    [data-testid="stVerticalBlock"] p, [data-testid="stVerticalBlock"] label, .stWidgetLabel p {{
        color: #2D1F24 !important;
        font-weight: 600 !important;
    }}
    
    .stTextInput input, 
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatInput"] textarea {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}
    
    [data-testid="stChatInput"] textarea {{
        background-color: #FFFFFF !important;
    }}
    
    [data-testid="stChatInput"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid #FF69B4 !important;
        border-radius: 16px !important;
        padding: 4px !important;
        box-shadow: 0 4px 10px rgba(255, 105, 180, 0.15) !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #FFF0F5 !important;
        border-right: 2px solid #FFB6C1;
    }}
    
    .custom-card {{
        background-color: rgba(255, 255, 255, 0.9);
        border-left: 6px solid #FF1493;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(255, 20, 147, 0.15);
    }}
    
    .custom-card h4 {{
        color: #FF1493 !important;
        margin-top: 0;
        font-weight: 700;
    }}
    
    div.stButton > button:first-child {{
        background-color: #FF69B4 !important;
        color: white !important;
        border-radius: 12px !important;
        border: 2px solid #FF1493 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 10px rgba(255, 105, 180, 0.4);
    }}
    
    div.stButton > button:first-child:hover {{
        background-color: #FF1493 !important;
        box-shadow: 0 0 15px rgba(255, 20, 147, 0.7);
        transform: scale(1.02);
    }}
    
    div[data-testid="stForm"], div.stExpander {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid #FF69B4 !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 15px rgba(255, 105, 180, 0.1);
    }}
    
    button[data-baseweb="tab"] {{
        color: #5C3A47 !important;
        font-weight: 700 !important;
    }}
    
    button[aria-selected="true"] {{
        color: #FF1493 !important;
        border-bottom-color: #FF1493 !important;
    }}
    
    h1 {{
        color: #FF1493 !important;
        font-weight: 800 !important;
    }}
    </style>
    
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 999; overflow: hidden; display: flex; justify-content: space-around;">
        <marquee behavior="scroll" direction="down" scrollamount="4" style="height: 100%; font-size: 26px; opacity: 0.55;">💕</marquee>
        <marquee behavior="scroll" direction="down" scrollamount="6" style="height: 100%; font-size: 20px; opacity: 0.45;">💖</marquee>
        <marquee behavior="scroll" direction="down" scrollamount="3" style="height: 100%; font-size: 28px; opacity: 0.55;">💗</marquee>
        <marquee behavior="scroll" direction="down" scrollamount="5" style="height: 100%; font-size: 22px; opacity: 0.5;">🌸</marquee>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. INISIALISASI DATA
# ==============================================================================
HARI = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
TK_LABEL = {1: 'Mudah', 2: 'Sedang', 3: 'Sulit'}
TK_BOBOT = {1: 1.0, 2: 1.5, 3: 2.5}

DAFTAR_TIPS = [
    "Coba teknik Pomodoro: 25 menit fokus penuh, 5 menit istirahat. Auto lebih produktif daripada belajar maraton 6 jam! ⏱️",
    "Sebelum mulai belajar, minum air putih dulu. Otak yang dehidrasi itu susah fokus, lho! 💧",
    "Jangan cuma baca ulang catatan — coba teknik active recall: tutup buku, terus coba inget poin pentingnya sendiri. 🧠",
    "Pindah-pindah tempat belajar tiap beberapa hari bisa bantu otak nyimpen informasi lebih kuat. 🌿",
    "Tidur cukup itu bukan males, itu investasi. Otak ngolah & nyimpen ingatan justru pas kamu tidur. 😴",
    "Pecah materi besar jadi chunk-chunk kecil. Belajar 1 bab penuh sekaligus itu bikin capek duluan. 🍰",
    "Coba teknik Feynman: jelasin materi ke diri sendiri pakai bahasa paling sederhana, kayak ngejelasin ke anak kecil. 🗣️",
    "Matiin notifikasi HP pas sesi belajar. Kepotong notif 10 menit itu ngerusak fokus lebih dari yang kamu kira. 📵",
    "Spaced repetition lebih ngena daripada SKS (Sistem Kebut Semalam). Ulang materi tiap beberapa hari, bukan cuma sekali. 🔁",
    "Belajar bareng temen boleh banget, asal saling jelasin materi, bukan cuma ngobrol doang ya! 👯",
    "Kalau ngerasa stuck di satu soal lebih dari 10 menit, skip dulu, lanjut yang lain, balik lagi nanti. ⏭️",
    "Reward diri sendiri abis nyelesain target belajar, sekecil apapun itu. Kamu pantas dapet itu! 🎁",
    "Musik tanpa lirik (lo-fi, instrumental) bisa bantu fokus buat sebagian orang — coba aja dulu! 🎧",
    "Catat progress harian, sekecil apapun. Liat progress itu sendiri udah jadi motivasi. ✅",
    "Belajar pagi hari pas otak masih fresh itu beda banget efeknya sama belajar pas udah capek malam-malam. 🌅",
    "Kalau ngerasa overwhelmed, coba breakdown tugas jadi 3 langkah kecil aja dulu. Mulai dari yang paling gampang. 🪜",
    "Jangan multitasking pas belajar. Otak manusia itu bukan didesain buat fokus ke 2 hal sekaligus. 🚫",
    "Olahraga ringan 10-15 menit sebelum belajar bisa ningkatin fokus karena aliran darah ke otak jadi lebih lancar. 🏃‍♀️",
    "Self-talk yang positif itu beneran ngaruh. Ganti 'aku gabisa' jadi 'aku lagi belajar buat bisa'. 💖",
    "Kalau capek banget, istirahat itu bukan kalah. Otak yang lelah gabakal nyerep informasi dengan baik. 🌸",
]

MOOD_OPTIONS = {
    "😄 Semangat Banget": 5,
    "🙂 Lumayan Oke": 4,
    "😐 Biasa Aja": 3,
    "😩 Capek Banget": 2,
    "😢 Down / Stres": 1,
}

if 'mata_kuliah' not in st.session_state:
    st.session_state.mata_kuliah = []

if 'jam_tersedia' not in st.session_state:
    st.session_state.jam_tersedia = {0: 2, 1: 3, 2: 2, 3: 4, 4: 3, 5: 5, 6: 4}

if 'jadwal_hasil' not in st.session_state:
    st.session_state.jadwal_hasil = {}

if 'bot_token' not in st.session_state:
    st.session_state.bot_token = ""

if 'chat_id' not in st.session_state:
    st.session_state.chat_id = ""

if 'mood_log' not in st.session_state:
    st.session_state.mood_log = []

if 'tip_sekarang' not in st.session_state:
    st.session_state.tip_sekarang = random.choice(DAFTAR_TIPS)

# ==============================================================================
# 5. BACKGROUND ENGINE TELEGRAM OTOMATIS
# ==============================================================================
def kirim_pengingat_tele(token, cid, daftar_mk):
    pesan = "✨ *Pagi Maya! Kring Kring.. Saatnya Belajar!* ✨\n\nIni list tugas/ujian kamu yang harus dicicil hari ini:\n"
    ada_tugas = False
    for mk in daftar_mk:
        if not mk['selesai']:
            ada_tugas = True
            sisa = (mk['deadline'] - datetime.date.today()).days
            if sisa <= 3:
                pesan += f"🚨 🔥 *PERINGATAN MEPET:* *{mk['nama']}* tinggal *{sisa} hari lagi!* Buruan dicicil ya Maya! (Deadline: {mk['deadline'].strftime('%d/%m/%Y')})\n"
            else:
                pesan += f"📌 *{mk['nama']}* — Sisa {sisa} hari lagi. (Deadline: {mk['deadline'].strftime('%d/%m/%Y')})\n"
    pesan += "\nJangan ditunda-tunda ya Maya, semangat belajarnya! Mwa 💕🌸"
    if ada_tugas:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": cid, "text": pesan, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

def loop_jadwal_otomatis(token, cid):
    hari_terakhir_kirim = None
    while True:
        sekarang = datetime.datetime.now()
        hari_ini = sekarang.date()
        if hari_terakhir_kirim != hari_ini:
            kirim_pengingat_tele(token, cid, st.session_state.mata_kuliah)
            hari_terakhir_kirim = hari_ini
        time.sleep(3600)

# ==============================================================================
# 6. LAYOUT UTAMA APLIKASI
# ==============================================================================
st.title("💖 AI STUDY PLANNER")
st.caption("Asisten Bot Pribadi Nyala Otomatis Tiap Jam 7 Pagi")
st.write("---")

kolom_kiri, kolom_kanan = st.columns([1, 2])

with kolom_kiri:
    st.markdown("### 🤖 Kredensial Asisten Telegram")
    bot_token = st.text_input("Bot Token (Dari @BotFather):", type="password")
    chat_id = st.text_input("ID Chat Telegram Kamu:")

    if bot_token:
        st.session_state.bot_token = bot_token
    if chat_id:
        st.session_state.chat_id = chat_id
    
    if st.button("🔔 AKTIFKAN BOT OTOMATIS HARIAN", use_container_width=True):
        if bot_token and chat_id:
            t = threading.Thread(target=loop_jadwal_otomatis, args=(bot_token, chat_id), daemon=True)
            t.start()
            st.success("🧸 Asisten Telegram Aktif! Pesan dikirim otomatis jam 7 pagi.")
            kirim_pengingat_tele(bot_token, chat_id, st.session_state.mata_kuliah)
        else:
            st.error("Isi Token dan ID dulu ya, Maya!")

    st.markdown("### 📅 Atur Jam Belajar Harian")
    with st.expander("🌸 Buka Slot Waktu", expanded=False):
        for idx, hari_nama in enumerate(HARI):
            st.session_state.jam_tersedia[idx] = st.number_input(
                f"Jam Hari {hari_nama}:", min_value=0, max_value=16, 
                value=st.session_state.jam_tersedia.get(idx, 0), key=f"jam_{idx}"
            )
            
    st.markdown("### ➕ Tambah Mata Kuliah")
    with st.form("form_mk", clear_on_submit=True):
        nama_mk = st.text_input("Nama Mata Kuliah:")
        kesulitan_mk = st.radio("Tingkat Kesulitan:", [1, 2, 3], format_func=lambda x: TK_LABEL[x], horizontal=True)
        deadline_mk = st.date_input("Deadline Tugas/Ujian:", min_value=datetime.date.today())
        total_jam_mk = st.number_input("Total Jam Kebutuhan Belajar:", min_value=1, value=2)
        btn_tambah = st.form_submit_button("🎀 Tambahkan MK")
        
        if btn_tambah and nama_mk:
            st.session_state.mata_kuliah.append({
                'nama': nama_mk, 'kesulitan': kesulitan_mk, 
                'deadline': deadline_mk, 'jam': total_jam_mk, 'selesai': False
            })
            st.success(f"🧸 Berhasil menambahkan '{nama_mk}'!")

    st.write("---")
    
    if st.button("🚀 GENERATE JADWAL BELAJAR UTAMA", use_container_width=True):
        pending = []
        for mk in st.session_state.mata_kuliah:
            if mk['selesai']: continue
            sisa_hari = max((mk['deadline'] - datetime.date.today()).days, 1)
            pending.append({**mk, 'prioritas': TK_BOBOT[mk['kesulitan']] * (100 / sisa_hari), 'sisa_jam': mk['jam']})
        pending.sort(key=lambda x: x['prioritas'], reverse=True)

        hasil_generate = {}
        hari_ini = datetime.date.today()
        
        for d in range(21):
            tgl = hari_ini + datetime.timedelta(days=d)
            dow = tgl.weekday()
            avail = st.session_state.jam_tersedia.get(dow, 0)
            if not avail: continue

            sisa_hari_jam = avail
            sesi = []
            for mk in pending:
                if sisa_hari_jam <= 0: break
                if mk['sisa_jam'] <= 0: continue
                if tgl > mk['deadline']: continue
                
                assign = min(sisa_hari_jam, mk['sisa_jam'], 2)
                if assign:
                    sesi.append({'nama': mk['nama'], 'jam': assign, 'kesulitan': mk['kesulitan']})
                    mk['sisa_jam'] -= assign
                    sisa_hari_jam -= assign

            if sesi:
                hasil_generate[tgl] = {'sesi': sesi, 'total_jam': avail - sisa_hari_jam}
                
        st.session_state.jadwal_hasil = hasil_generate
        st.toast("Jadwal Belajar Berhasil Diperbarui! 💕", icon="🌸")

with kolom_kanan:
    tabs = st.tabs([
        "📅 Jadwal Otomasi",
        "⏰ Reminder Progress",
        "📊 Grafik Interaktif",
        "🤖 Konsultasi AI",
        "🎲 Tips Belajar",
        "📈 Mood Tracker",
    ])
    
    with tabs[0]:
        st.subheader("🌸 Susunan Jadwal Belajar Optimal")
        if not st.session_state.jadwal_hasil:
            st.info("Jadwal kosong. Klik tombol '🚀 GENERATE JADWAL BELAJAR UTAMA' di sebelah kiri.")
        else:
            for tgl, info in sorted(st.session_state.jadwal_hasil.items()):
                hari_nama = HARI[tgl.weekday()]
                tgl_fmt = tgl.strftime('%d %B %Y')
                sesi_html = "".join([f"<li>✨ <b>{s['nama']}</b> — {s['jam']} Jam [{TK_LABEL[s['kesulitan']]}]</li>" for s in info['sesi']])
                card_template = f"""
                <div class="custom-card">
                    <h4>💕 {hari_nama}, {tgl_fmt} — Total: {info['total_jam']} Jam</h4>
                    <ul>{sesi_html}</ul>
                </div>
                """
                st.markdown(card_template, unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("⏰ Status Pengingat Progress Tugas")
        total_mk = len(st.session_state.mata_kuliah)
        if total_mk > 0:
            selesai_mk = sum(1 for m in st.session_state.mata_kuliah if m['selesai'])
            persen = selesai_mk / total_mk
            st.progress(persen, text=f"Progress Belajar: {int(persen*100)}%")
        
        st.write("---")
        for idx, mk in enumerate(st.session_state.mata_kuliah):
            sisa = (mk['deadline'] - datetime.date.today()).days
            status_tag = "🔵 SELESAI" if mk['selesai'] else ("🔴 MENDESAK" if sisa <= 3 else "🟢 AMAN")
            is_done = st.checkbox(f"**{mk['nama']}** | Deadline: {mk['deadline'].strftime('%d/%m/%Y')} ({sisa} hari lagi) — [{status_tag}]", value=mk['selesai'], key=f"mk_check_{idx}")
            st.session_state.mata_kuliah[idx]['selesai'] = is_done

    with tabs[2]:
        st.subheader("📊 Analisis Data Grafik Aktivitas")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            jam_list = [st.session_state.jam_tersedia.get(i, 0) for i in range(7)]
            fig_bar = go.Figure(data=[go.Bar(x=HARI, y=jam_list, marker_color='#FF1493')])
            fig_bar.update_layout(title='Jam Belajar Tersedia', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_g2:
            counts = {1: 0, 2: 0, 3: 0}
            for mk in st.session_state.mata_kuliah: counts[mk['kesulitan']] += 1
            sizes = [counts[k] for k in [1, 2, 3] if counts[k]]
            labels = [TK_LABEL[k] for k in [1, 2, 3] if counts[k]]
            if sizes:
                fig_pie = go.Figure(data=[go.Pie(labels=labels, values=sizes, hole=.5, marker=dict(colors=['#FFB6B1', '#FF69B4', '#FF1493']))])
                fig_pie.update_layout(title='Proporsi Beban Materi', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)

    with tabs[3]:
        st.subheader("🤖 AI Academic Consultant Co-Pilot (Powered by Groq ⚡)")
        
        def konsultasi_ai(pertanyaan):
            try:
                response = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "Kamu adalah asisten akademik yang ramah, suportif, dan ngerti bahasa gaul Indonesia. "
                                       "Jawab langsung sesuai isi curhatan/pertanyaan mahasiswa, jangan kasih jawaban template generik. "
                                       "Beri saran praktis dan singkat."
                        },
                        {
                            "role": "user",
                            "content": pertanyaan
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300,
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Waduh, ada error nih: {e}. Coba lagi sebentar ya!"

        user_ask = st.chat_input("Konsultasikan hambatan belajarmu langsung dengan AI:")
        if user_ask:
            st.chat_message("user").write(user_ask)
            with st.spinner("Groq sedang memproses jawaban kilat... ⚡"):
                jawaban_ai = konsultasi_ai(user_ask)
                st.chat_message("assistant").write(jawaban_ai)

    with tabs[4]:
        st.subheader("🎲 Bank Tips Belajar Random")
        st.write("Lagi butuh suntikan semangat atau trik belajar baru? Klik tombol di bawah, Maya! ✨")

        st.markdown(f"""
        <div class="custom-card">
            <h4>💡 Tips Buat Kamu</h4>
            <p style="font-size:17px;">{st.session_state.tip_sekarang}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Kasih Tips Lain Dong!", use_container_width=True):
            tip_baru = random.choice(DAFTAR_TIPS)
            percobaan = 0
            while tip_baru == st.session_state.tip_sekarang and percobaan < 10:
                tip_baru = random.choice(DAFTAR_TIPS)
                percobaan += 1
            st.session_state.tip_sekarang = tip_baru
            st.rerun()

    with tabs[5]:
        st.subheader("📈 Mood Tracker Harian")
        st.write("Catat mood belajar kamu biar bisa lihat polanya seiring waktu, Maya 🌷")

        col_mood1, col_mood2 = st.columns([2, 1])
        with col_mood1:
            mood_pilihan = st.radio(
                "Gimana mood belajar kamu sekarang?",
                list(MOOD_OPTIONS.keys()),
                horizontal=True
            )
        with col_mood2:
            st.write("")
            st.write("")
            if st.button("💾 Catat Mood", use_container_width=True):
                st.session_state.mood_log.append({
                    'waktu': datetime.datetime.now(),
                    'mood_label': mood_pilihan,
                    'mood_score': MOOD_OPTIONS[mood_pilihan]
                })
                st.toast(f"Mood '{mood_pilihan}' berhasil dicatat! 🌸", icon="💖")

        st.write("---")

        if st.session_state.mood_log:
            df_mood = pd.DataFrame(st.session_state.mood_log)

            fig_mood = go.Figure()
            fig_mood.add_trace(go.Scatter(
                x=df_mood['waktu'],
                y=df_mood['mood_score'],
                mode='lines+markers',
                line=dict(color='#FF1493', width=3),
                marker=dict(size=10, color='#FF69B4'),
                hovertext=df_mood['mood_label'],
                hoverinfo='text+x'
            ))
            fig_mood.update_layout(
                title='Tren Mood Belajar Kamu',
                yaxis=dict(
                    range=[0, 6],
                    tickvals=[1, 2, 3, 4, 5],
                    ticktext=['😢', '😩', '😐', '🙂', '😄']
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_mood, use_container_width=True)

            rata_rata = df_mood['mood_score'].mean()
            if rata_rata >= 4:
                st.success(f"Rata-rata mood kamu lagi bagus nih ({rata_rata:.1f}/5)! Pertahankan ya 🌸")
            elif rata_rata >= 2.5:
                st.warning(f"Mood kamu lumayan naik-turun ({rata_rata:.1f}/5). Jangan lupa istirahat cukup ya 💕")
            else:
                st.error(f"Mood kamu akhir-akhir ini cenderung lelah ({rata_rata:.1f}/5). Yuk kurangi beban belajar dulu & istirahat 🌷")

            with st.expander("📜 Riwayat Mood Lengkap"):
                for entry in reversed(st.session_state.mood_log[-15:]):
                    st.write(f"🕐 {entry['waktu'].strftime('%d/%m %H:%M')} — {entry['mood_label']}")
        else:
            st.info("Belum ada data mood. Yuk catat mood pertama kamu di atas! 🌸")
