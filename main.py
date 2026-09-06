from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import sqlite3
import datetime
import calendar 
import os
import math
import webbrowser 
import urllib.parse 
import random 

Window.size = (360, 640)
Window.clearcolor = (0.95, 0.95, 0.95, 1)

# ==========================================
# 1. PERSIAPAN DATABASE & UPDATE TABEL
# ==========================================
FOLDER_KTP = "foto_ktp"
if not os.path.exists(FOLDER_KTP): os.makedirs(FOLDER_KTP)

def siapkan_database():
    koneksi = sqlite3.connect('golocker_v6.db') 
    kursor = koneksi.cursor()
    kursor.execute('''CREATE TABLE IF NOT EXISTS pelanggan (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, no_hp TEXT, jumlah_titip INTEGER DEFAULT 0, foto_ktp TEXT, waktu_update_ktp TEXT)''')
    kursor.execute('''CREATE TABLE IF NOT EXISTS motor (id INTEGER PRIMARY KEY AUTOINCREMENT, plat_nomor TEXT, tipe TEXT, status TEXT, harga INTEGER)''')
    kursor.execute('''CREATE TABLE IF NOT EXISTS loker (id INTEGER PRIMARY KEY AUTOINCREMENT, nomor_loker TEXT, ukuran TEXT, status TEXT)''')
    kursor.execute('''CREATE TABLE IF NOT EXISTS transaksi_loker (id INTEGER PRIMARY KEY AUTOINCREMENT, id_pelanggan INTEGER, id_loker INTEGER, jenis_tarif TEXT, perkiraan_ambil TEXT, waktu_titip TEXT, sudah_dibayar INTEGER, kode_unik TEXT, nama_kasir TEXT DEFAULT 'Sistem')''')
    kursor.execute('''CREATE TABLE IF NOT EXISTS riwayat_transaksi (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_pelanggan TEXT, nomor_loker TEXT, waktu_titip TEXT, waktu_ambil TEXT, total_pendapatan INTEGER, nama_kasir TEXT DEFAULT 'Sistem')''')
    kursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
    kursor.execute('''CREATE TABLE IF NOT EXISTS pengaturan_tarif (nama_tarif TEXT PRIMARY KEY, harga INTEGER)''')

    # Insert Data Loker Awal 
    kursor.execute("SELECT COUNT(*) FROM loker")
    if kursor.fetchone()[0] == 0:
        data_loker = [(str(i), 'Besar', 'Tersedia') for i in range(1, 71)] + [(f"{i}L", 'Kecil', 'Tersedia') for i in range(1, 21)]
        kursor.executemany("INSERT INTO loker (nomor_loker, ukuran, status) VALUES (?, ?, ?)", data_loker)
        
    # Insert Akun Default 
    kursor.execute("SELECT COUNT(*) FROM users")
    if kursor.fetchone()[0] == 0:
        kursor.execute("INSERT INTO users (username, password, role) VALUES ('owner', 'owner123', 'owner')")
        kursor.execute("INSERT INTO users (username, password, role) VALUES ('kasir1', 'kasir123', 'kasir')")
        
    # Insert Tarif Default 
    kursor.execute("SELECT COUNT(*) FROM pengaturan_tarif")
    if kursor.fetchone()[0] == 0:
        tarif_default = [
            ('TARIF_DASAR', 27000),   
            ('TARIF_PER_JAM', 9000),  
            ('TARIF_TANGGUNG', 5000), 
            ('TARIF_24_JAM', 65000)   
        ]
        kursor.executemany("INSERT INTO pengaturan_tarif (nama_tarif, harga) VALUES (?, ?)", tarif_default)
        
    koneksi.commit()
    koneksi.close()

def bersihkan_ktp_kadaluarsa():
    koneksi = sqlite3.connect('golocker_v6.db')
    kursor = koneksi.cursor()
    batas_waktu = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    kursor.execute("SELECT foto_ktp FROM pelanggan WHERE waktu_update_ktp < ? AND foto_ktp IS NOT NULL", (batas_waktu,))
    for data in kursor.fetchall():
        if data[0] and os.path.exists(data[0]): os.remove(data[0])
    kursor.execute("UPDATE pelanggan SET foto_ktp = NULL, waktu_update_ktp = NULL WHERE waktu_update_ktp < ?", (batas_waktu,))
    koneksi.commit()
    koneksi.close()

def get_tarif_sekarang():
    koneksi = sqlite3.connect('golocker_v6.db')
    kursor = koneksi.cursor()
    kursor.execute("SELECT nama_tarif, harga FROM pengaturan_tarif")
    dict_tarif = {row[0]: row[1] for row in kursor.fetchall()}
    koneksi.close()
    return dict_tarif

siapkan_database()
bersihkan_ktp_kadaluarsa()

# ==========================================
# 2. DESAIN TAMPILAN (BAHASA KV)
# ==========================================
desain_antarmuka = """
ScreenManager:
    LoginScreen: 
    MenuUtama:
    LokerScreen:
    CheckInScreen:
    CheckOutScreen: 
    MonitoringScreen: 
    LaporanScreen:  
    PengaturanScreen:
    DataPelangganScreen: 

<LoginScreen>:
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: 40
        spacing: 15
        Widget:
            size_hint_y: 0.2
        Label:
            text: "GoLockers Mobile"
            font_size: '28sp'
            bold: True
            color: 0.2, 0.6, 0.9, 1
            size_hint_y: None
            height: 40
        Label:
            text: "Silakan Login"
            font_size: '16sp'
            color: 0.4, 0.4, 0.4, 1
            size_hint_y: None
            height: 30
        TextInput:
            id: input_user
            hint_text: "Username"
            multiline: False
            size_hint_y: None
            height: 50
        TextInput:
            id: input_pass
            hint_text: "Password"
            password: True
            multiline: False
            size_hint_y: None
            height: 50
        Label:
            id: lbl_error
            text: ""
            color: 0.9, 0.1, 0.1, 1
            font_size: '12sp'
            size_hint_y: None
            height: 30
        Button:
            text: "MASUK"
            background_color: 0.2, 0.6, 0.9, 1
            background_normal: ''
            bold: True
            size_hint_y: None
            height: 50
            on_release: root.proses_login()
        Widget:
            size_hint_y: 0.4

<MenuUtama>:
    name: 'menu_utama'
    on_enter: root.muat_profil()
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20
        Label:
            text: "GoLockers Mobile"
            color: 0.1, 0.1, 0.1, 1
            font_size: '28sp'
            bold: True
            size_hint_y: 0.2
        Label:
            id: lbl_sapaan
            text: "Halo, -"
            color: 0.4, 0.4, 0.4, 1
            font_size: '14sp'
            size_hint_y: 0.1
        Button:
            text: "PENITIPAN LOKER"
            font_size: '16sp'
            bold: True
            background_color: 0.85, 0.65, 0.13, 1
            background_normal: ''
            on_release: app.root.current = 'menu_loker'
        Button:
            text: "RENTAL MOTOR"
            font_size: '16sp'
            bold: True
            background_color: 0.8, 0.1, 0.1, 1
            background_normal: ''
        Widget:
            size_hint_y: 0.2
        Button:
            text: "LOGOUT"
            background_color: 0.5, 0.5, 0.5, 1
            background_normal: ''
            size_hint_y: None
            height: 40
            on_release: root.proses_logout()

<LokerScreen>:
    name: 'menu_loker'
    on_enter: root.atur_hak_akses() 
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 15
        Label:
            text: "Dashboard Loker"
            color: 0.1, 0.1, 0.1, 1
            font_size: '24sp'
            bold: True
            size_hint_y: 0.2
        Button:
            text: "TITIP BARANG (Check-In)"
            background_color: 0.85, 0.65, 0.13, 1
            background_normal: ''
            on_release: app.root.current = 'check_in'
        Button:
            text: "AMBIL BARANG (Check-Out)"
            background_color: 0.2, 0.6, 0.9, 1
            background_normal: ''
            on_release: app.root.current = 'check_out'  
        Button:
            text: "MONITORING LOKER"
            background_color: 0.9, 0.5, 0.0, 1  
            background_normal: ''
            on_release: app.root.current = 'monitoring'  
            
        BoxLayout:
            id: box_owner_1
            orientation: 'horizontal'
            spacing: 10
            Button:
                text: "LAPORAN (Owner)"  
                background_color: 0.1, 0.7, 0.1, 1  
                background_normal: ''
                on_release: app.root.current = 'laporan'
            Button:
                text: "CUSTOMER (Owner)"  
                background_color: 0.6, 0.2, 0.8, 1  
                background_normal: ''
                on_release: app.root.current = 'data_pelanggan'
                
        Button:
            id: btn_pengaturan
            text: "PENGATURAN HARGA & AKUN (Owner)"  
            background_color: 0.3, 0.3, 0.3, 1  
            background_normal: ''
            on_release: app.root.current = 'pengaturan' 
            
        Widget:
            size_hint_y: 0.05
        Button:
            text: "KEMBALI"
            size_hint_y: 0.4
            background_color: 0.5, 0.5, 0.5, 1
            background_normal: ''
            on_release: app.root.current = 'menu_utama'

<DataPelangganScreen>:
    name: 'data_pelanggan'
    on_enter: root.muat_data()
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 15
        
        Label:
            text: "Data Pelanggan (CRM)"
            color: 0.1, 0.1, 0.1, 1
            font_size: '20sp'
            bold: True
            size_hint_y: None
            height: 40
            
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 45
            spacing: 5
            TextInput:
                id: input_cari
                hint_text: "Cari Nama / No. HP"
                multiline: False
                size_hint_x: 0.7
            Button:
                text: "CARI"
                background_color: 0.2, 0.6, 0.9, 1
                background_normal: ''
                bold: True
                size_hint_x: 0.3
                on_release: root.muat_data(input_cari.text)
                
        Label:
            text: "Daftar Pelanggan (Diurutkan dari paling loyal):"
            color: 0.3, 0.3, 0.3, 1
            font_size: '12sp'
            size_hint_y: None
            height: 25
            halign: 'left'
            text_size: self.size
            
        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            BoxLayout:
                id: wadah_pelanggan
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 5
                
        Button:
            text: "KEMBALI"
            background_color: 0.5, 0.5, 0.5, 1
            background_normal: ''
            size_hint_y: None
            height: 45
            on_release: app.root.current = 'menu_loker'

<PengaturanScreen>:
    name: 'pengaturan'
    on_enter: root.muat_data()
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 10
        Label:
            text: "Pengaturan Sistem"
            color: 0.1, 0.1, 0.1, 1
            font_size: '20sp'
            bold: True
            size_hint_y: None
            height: 40
        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 20
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: 290
                    padding: 10
                    spacing: 5
                    canvas.before:
                        Color:
                            rgba: 0.9, 0.9, 0.9, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [10]
                    Label:
                        text: "PENGATURAN HARGA"
                        color: 0.1, 0.7, 0.1, 1
                        bold: True
                        size_hint_y: None
                        height: 30
                    Label:
                        text: "Tarif Dasar (3 Jam Pertama):"
                        color: 0.3, 0.3, 0.3, 1
                        font_size: '12sp'
                        size_hint_y: None
                        height: 20
                    TextInput:
                        id: in_tarif_dasar
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: 35
                    Label:
                        text: "Tarif Per Jam (Atau Menit > 39):"
                        color: 0.3, 0.3, 0.3, 1
                        font_size: '12sp'
                        size_hint_y: None
                        height: 20
                    TextInput:
                        id: in_tarif_jam
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: 35
                    Label:
                        text: "Tarif Tanggung (Menit 11 - 39):"
                        color: 0.3, 0.3, 0.3, 1
                        font_size: '12sp'
                        size_hint_y: None
                        height: 20
                    TextInput:
                        id: in_tarif_tanggung
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: 35
                    Label:
                        text: "Tarif 24 Jam (Flat):"
                        color: 0.3, 0.3, 0.3, 1
                        font_size: '12sp'
                        size_hint_y: None
                        height: 20
                    TextInput:
                        id: in_tarif_24
                        input_filter: 'int'
                        multiline: False
                        size_hint_y: None
                        height: 35
                    Button:
                        text: "SIMPAN TARIF"
                        background_color: 0.2, 0.6, 0.9, 1
                        background_normal: ''
                        bold: True
                        size_hint_y: None
                        height: 40
                        on_release: root.simpan_tarif()
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: 10
                    spacing: 5
                    canvas.before:
                        Color:
                            rgba: 0.9, 0.9, 0.9, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [10]
                    Label:
                        text: "TAMBAH AKUN KASIR"
                        color: 0.9, 0.5, 0.0, 1
                        bold: True
                        size_hint_y: None
                        height: 30
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: 40
                        spacing: 5
                        TextInput:
                            id: in_user_kasir
                            hint_text: "Username Baru"
                            multiline: False
                        TextInput:
                            id: in_pass_kasir
                            hint_text: "Password Baru"
                            multiline: False
                    Button:
                        text: "TAMBAH AKUN"
                        background_color: 0.9, 0.5, 0.0, 1
                        background_normal: ''
                        bold: True
                        size_hint_y: None
                        height: 40
                        on_release: root.tambah_akun()
                    Label:
                        text: "Daftar Kasir Terdaftar:"
                        color: 0.3, 0.3, 0.3, 1
                        font_size: '12sp'
                        size_hint_y: None
                        height: 30
                    BoxLayout:
                        id: wadah_daftar_akun
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: 5
        Button:
            text: "KEMBALI"
            background_color: 0.5, 0.5, 0.5, 1
            background_normal: ''
            size_hint_y: None
            height: 45
            on_release: app.root.current = 'menu_loker'

<CheckInScreen>:
    name: 'check_in'
    ScrollView:
        do_scroll_x: False
        do_scroll_y: True
        BoxLayout:
            orientation: 'vertical'
            padding: 20
            spacing: 15
            size_hint_y: None
            height: self.minimum_height
            Label:
                text: "Form Penitipan"
                color: 0.1, 0.1, 0.1, 1
                font_size: '20sp'
                bold: True
                size_hint_y: None
                height: 40
            TextInput:
                id: input_hp
                hint_text: "No. HP Pelanggan"
                multiline: False
                size_hint_y: None
                height: 40
                on_text: root.munculkan_saran_hp(self.text)
            BoxLayout:
                id: wadah_saran_hp
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 2
            TextInput:
                id: input_nama
                hint_text: "Nama Pelanggan"
                multiline: False
                size_hint_y: None
                height: 40
            Button:
                id: btn_kamera
                text: "AMBIL FOTO KTP (SIMULASI)"
                bold: True
                background_color: 0.2, 0.6, 0.9, 1
                background_normal: ''
                size_hint_y: None
                height: 45
                on_release: root.proses_kamera()
            Label:
                id: info_ktp
                text: "Status KTP: Belum Diambil"
                color: 0.4, 0.4, 0.4, 1
                font_size: '12sp'
                size_hint_y: None
                height: 20
            TextInput:
                id: input_loker
                hint_text: "Nomor Loker (Cth: 1, 23, 1L)"
                multiline: False
                size_hint_y: None
                height: 40
                on_text: root.cek_ketersediaan_loker(self.text)
            Label:
                id: info_loker
                text: ""
                font_size: '13sp'
                bold: True
                size_hint_y: None
                height: 20
            Spinner:
                id: input_tarif
                text: "Pilih Tarif"
                values: ["Per Jam", "Per 24 Jam (Flat)"]
                size_hint_y: None
                height: 40
                background_color: 0.4, 0.4, 0.4, 1
                on_text: root.cek_tarif(self.text)
            TextInput:
                id: input_hari
                hint_text: "Jml Hari (Pilih Tarif 24 Jam Dulu)"
                multiline: False
                size_hint_y: None
                height: 40
                disabled: True
            TextInput:
                id: input_perkiraan
                hint_text: "Perkiraan Diambil (Cth: 18.00)"
                multiline: False
                size_hint_y: None
                height: 40
            Button:
                text: "SIMPAN & KIRIM TIKET PIN"
                bold: True
                background_color: 0.2, 0.6, 0.9, 1  
                background_normal: ''
                size_hint_y: None
                height: 50
                on_release: root.simpan_transaksi()
            Button:
                text: "BATAL"
                background_color: 0.5, 0.5, 0.5, 1
                background_normal: ''
                size_hint_y: None
                height: 40
                on_release: app.root.current = 'menu_loker'

<CheckOutScreen>:
    name: 'check_out'
    ScrollView:
        do_scroll_x: False
        do_scroll_y: True
        BoxLayout:
            orientation: 'vertical'
            padding: 20
            spacing: 15
            size_hint_y: None
            height: self.minimum_height
            Label:
                text: "Ambil Barang (Check-Out)"
                color: 0.1, 0.1, 0.1, 1
                font_size: '20sp'
                bold: True
                size_hint_y: None
                height: 40
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 45
                spacing: 5
                TextInput:
                    id: input_cari
                    hint_text: "No. Loker / PIN"
                    multiline: False
                    size_hint_x: 0.5
                Button:
                    text: "CARI LOKER"
                    bold: True
                    font_size: '12sp'
                    background_color: 0.2, 0.6, 0.9, 1
                    background_normal: ''
                    size_hint_x: 0.25
                    on_release: root.cari_data('loker')
                Button:
                    text: "CARI PIN"
                    bold: True
                    font_size: '12sp'
                    background_color: 0.9, 0.5, 0.0, 1 
                    background_normal: ''
                    size_hint_x: 0.25
                    on_release: root.cari_data('kode')
            BoxLayout:
                id: area_struk
                orientation: 'vertical'
                size_hint_y: None
                height: 260
                padding: 15
                spacing: 5
                canvas.before:
                    Color:
                        rgba: 0.9, 0.9, 0.9, 1  
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [10]
                Label:
                    id: lbl_detail
                    text: "Silakan masukkan nomor loker atau Kode PIN 4-digit pelanggan."
                    color: 0.1, 0.1, 0.1, 1
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size
            Label:
                id: lbl_total_bayar
                text: "TOTAL TAGIHAN: Rp 0"
                color: 0.9, 0.5, 0.0, 1 
                font_size: '18sp'
                bold: True
                size_hint_y: None
                height: 40
            Button:
                id: btn_lunasi
                text: "LUNASI & AMBIL (KIRIM WA)"
                bold: True
                background_color: 0.2, 0.6, 0.9, 1 
                background_normal: ''
                size_hint_y: None
                height: 50
                disabled: True 
                on_release: root.lunasi_transaksi()
            Button:
                text: "KEMBALI"
                background_color: 0.5, 0.5, 0.5, 1
                background_normal: ''
                size_hint_y: None
                height: 40
                on_release: root.kembali_ke_menu()

<MonitoringScreen>:
    name: 'monitoring'
    on_enter: root.muat_data_loker() 
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 10
        Label:
            text: "Peta Loker Real-Time"
            color: 0.1, 0.1, 0.1, 1
            font_size: '20sp'
            bold: True
            size_hint_y: None
            height: 40
        Label:
            id: lbl_statistik
            text: "Total: 90 | Terisi: 0 | Kosong: 90"
            color: 0.3, 0.3, 0.3, 1
            bold: True
            size_hint_y: None
            height: 30
        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            GridLayout:
                id: grid_loker
                cols: 4  
                spacing: 10
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: 140  
            padding: 10
            canvas.before:
                Color:
                    rgba: 0.9, 0.9, 0.9, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            Label:
                id: lbl_info_detail
                text: "Klik salah satu kotak loker di atas untuk melihat detail."
                color: 0.1, 0.1, 0.1, 1
                halign: 'left'
                valign: 'top'
                text_size: self.size
        Button:
            text: "KEMBALI"
            background_color: 0.5, 0.5, 0.5, 1
            background_normal: ''
            size_hint_y: None
            height: 45
            on_release: app.root.current = 'menu_loker'

<LaporanScreen>:
    name: 'laporan'
    on_enter: root.muat_awal()
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 15
        Label:
            text: "Laporan Pendapatan"
            color: 0.1, 0.1, 0.1, 1
            font_size: '20sp'
            bold: True
            size_hint_y: None
            height: 40
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 40
            spacing: 10
            Label:
                text: "Rentang:"
                color: 0.3, 0.3, 0.3, 1
                bold: True
                size_hint_x: 0.3
            Spinner:
                id: spinner_rentang
                text: "Hari Ini"
                values: [] 
                size_hint_x: 0.7
                background_color: 0.2, 0.6, 0.9, 1
                on_text: root.filter_laporan(self.text)
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: 80
            canvas.before:
                Color:
                    rgba: 0.1, 0.7, 0.1, 1 
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            Label:
                text: "TOTAL OMZET (DARI RENTANG TERPILIH)"
                font_size: '12sp'
                bold: True
            Label:
                id: lbl_omzet_total
                text: "Rp 0"
                font_size: '22sp'
                bold: True
        Label:
            text: "Riwayat Transaksi:"
            color: 0.3, 0.3, 0.3, 1
            font_size: '14sp'
            bold: True
            size_hint_y: None
            height: 25
            halign: 'left'
            text_size: self.size
        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            BoxLayout:
                id: wadah_riwayat
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 5
        Button:
            text: "KEMBALI"
            background_color: 0.5, 0.5, 0.5, 1
            background_normal: ''
            size_hint_y: None
            height: 45
            on_release: app.root.current = 'menu_loker'
"""

# ==========================================
# 3. LOGIKA PROGRAM (PYTHON)
# ==========================================

class DataPelangganScreen(Screen):
    def muat_data(self, kata_kunci=""):
        wadah = self.ids.wadah_pelanggan
        wadah.clear_widgets()
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        if kata_kunci: kursor.execute('''SELECT nama, no_hp, jumlah_titip, waktu_update_ktp FROM pelanggan WHERE nama LIKE ? OR no_hp LIKE ? ORDER BY jumlah_titip DESC''', ('%'+kata_kunci+'%', '%'+kata_kunci+'%'))
        else: kursor.execute('''SELECT nama, no_hp, jumlah_titip, waktu_update_ktp FROM pelanggan ORDER BY jumlah_titip DESC LIMIT 50''') 
        hasil = kursor.fetchall()
        koneksi.close()
        
        if not hasil:
            lbl = Label(text="Data tidak ditemukan.", color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=40)
            wadah.add_widget(lbl)
            return
            
        for data in hasil:
            nama, hp, jml, tgl_ktp = data
            ktp_status = "Ada KTP" if tgl_ktp else "Tanpa KTP"
            teks = f" {nama} ({hp})\n Total Titip: {jml} kali  |  Status: {ktp_status}"
            btn = Button(text=teks, color=(0.1, 0.1, 0.1, 1), background_color=(0.9, 0.9, 0.9, 1), background_normal='', size_hint_y=None, height=65, halign='left', valign='middle')
            btn.bind(size=btn.setter('text_size'))
            wadah.add_widget(btn)

class PengaturanScreen(Screen):
    def muat_data(self):
        tarif_db = get_tarif_sekarang()
        self.ids.in_tarif_dasar.text = str(tarif_db.get('TARIF_DASAR', 27000))
        self.ids.in_tarif_jam.text = str(tarif_db.get('TARIF_PER_JAM', 9000))
        self.ids.in_tarif_tanggung.text = str(tarif_db.get('TARIF_TANGGUNG', 5000))
        self.ids.in_tarif_24.text = str(tarif_db.get('TARIF_24_JAM', 65000))
        self.muat_daftar_kasir()
        
    def simpan_tarif(self):
        try:
            t_dasar = int(self.ids.in_tarif_dasar.text)
            t_jam = int(self.ids.in_tarif_jam.text)
            t_tanggung = int(self.ids.in_tarif_tanggung.text)
            t_24 = int(self.ids.in_tarif_24.text)
        except ValueError: return 
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        data_update = [(t_dasar, 'TARIF_DASAR'), (t_jam, 'TARIF_PER_JAM'), (t_tanggung, 'TARIF_TANGGUNG'), (t_24, 'TARIF_24_JAM')]
        kursor.executemany("UPDATE pengaturan_tarif SET harga = ? WHERE nama_tarif = ?", data_update)
        koneksi.commit()
        koneksi.close()

    def muat_daftar_kasir(self):
        wadah = self.ids.wadah_daftar_akun
        wadah.clear_widgets()
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("SELECT id, username, password FROM users WHERE role = 'kasir'")
        for id_user, usr, pwd in kursor.fetchall():
            baris = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            lbl = Label(text=f" User: {usr} | Pass: {pwd}", color=(0.1, 0.1, 0.1, 1), halign='left')
            lbl.bind(size=lbl.setter('text_size'))
            btn_hapus = Button(text="HAPUS", size_hint_x=0.3, background_color=(0.9, 0.1, 0.1, 1), background_normal='')
            btn_hapus.bind(on_release=lambda b, i=id_user: self.hapus_akun(i))
            baris.add_widget(lbl)
            baris.add_widget(btn_hapus)
            wadah.add_widget(baris)
        koneksi.close()
        
    def tambah_akun(self):
        usr = self.ids.in_user_kasir.text
        pwd = self.ids.in_pass_kasir.text
        if not usr or not pwd: return
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'kasir')", (usr, pwd))
        koneksi.commit()
        koneksi.close()
        self.ids.in_user_kasir.text = ""
        self.ids.in_pass_kasir.text = ""
        self.muat_daftar_kasir()
        
    def hapus_akun(self, id_user):
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("DELETE FROM users WHERE id = ?", (id_user,))
        koneksi.commit()
        koneksi.close()
        self.muat_daftar_kasir()

class LoginScreen(Screen):
    def proses_login(self):
        usr = self.ids.input_user.text
        pwd = self.ids.input_pass.text
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (usr, pwd))
        hasil = kursor.fetchone()
        koneksi.close()
        if hasil:
            app = App.get_running_app()
            app.session_username = hasil[0]
            app.session_role = hasil[1]
            self.ids.input_user.text = ""
            self.ids.input_pass.text = ""
            self.ids.lbl_error.text = ""
            self.manager.current = 'menu_utama'
        else:
            self.ids.lbl_error.text = "Username atau Password salah!"

class MenuUtama(Screen): 
    def muat_profil(self):
        app = App.get_running_app()
        role_label = "OWNER" if app.session_role == 'owner' else "KASIR"
        self.ids.lbl_sapaan.text = f"Login sebagai: {app.session_username} ({role_label})"
    def proses_logout(self):
        app = App.get_running_app()
        app.session_username = ""
        app.session_role = ""
        self.manager.current = 'login'

class LokerScreen(Screen): 
    def atur_hak_akses(self):
        app = App.get_running_app()
        if app.session_role == 'kasir':
            self.ids.box_owner_1.opacity = 0
            self.ids.box_owner_1.disabled = True
            self.ids.btn_pengaturan.opacity = 0
            self.ids.btn_pengaturan.disabled = True
        else:
            self.ids.box_owner_1.opacity = 1
            self.ids.box_owner_1.disabled = False
            self.ids.btn_pengaturan.opacity = 1
            self.ids.btn_pengaturan.disabled = False

class CheckInScreen(Screen):
    path_foto_tersimpan = ""
    def munculkan_saran_hp(self, ketikan):
        wadah = self.ids.wadah_saran_hp
        wadah.clear_widgets() 
        if len(ketikan) < 2: return
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("SELECT no_hp, nama FROM pelanggan WHERE no_hp LIKE ?", ('%'+ketikan+'%',))
        for hp, nama in kursor.fetchall():
            btn = Button(text=f"{hp} - {nama}", size_hint_y=None, height=35, background_color=(0.8, 0.8, 0.8, 1), background_normal='', color=(0.1, 0.1, 0.1, 1))
            btn.bind(on_release=lambda b, h=hp, n=nama: self.pilih_saran(h, n))
            wadah.add_widget(btn)
        koneksi.close()
    def pilih_saran(self, hp_pilihan, nama_pilihan):
        self.ids.input_hp.text = hp_pilihan
        self.ids.input_nama.text = nama_pilihan
        self.ids.wadah_saran_hp.clear_widgets() 
    def cek_tarif(self, pilihan):
        self.ids.input_hari.disabled = "24 Jam" not in pilihan
        self.ids.input_hari.text = "1" if "24 Jam" in pilihan else ""
        self.ids.input_hari.hint_text = "Jumlah Hari" if "24 Jam" in pilihan else "Jml Hari (Pilih Tarif 24 Jam Dulu)"
    def proses_kamera(self):
        nama_file = f"{FOLDER_KTP}/KTP_{self.ids.input_hp.text or 'Anonim'}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        open(nama_file, 'w').write("Simulasi foto KTP berhasil diambil.")
        self.path_foto_tersimpan = nama_file
        self.ids.btn_kamera.text = "FOTO KTP TERSIMPAN (KLIK UTK UBAH)"
        self.ids.btn_kamera.background_color = (0.2, 0.8, 0.2, 1) 
        self.ids.info_ktp.text = f"Sukses: {nama_file}"
        self.ids.info_ktp.color = (0.2, 0.6, 0.9, 1)
    def cek_ketersediaan_loker(self, ketikan):
        if not ketikan: 
            self.ids.info_loker.text = ""
            return
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("SELECT status FROM loker WHERE nomor_loker = ?", (ketikan.upper(),))
        hasil = kursor.fetchone()
        koneksi.close()
        if hasil:
            if hasil[0] == 'Terisi': self.ids.info_loker.text, self.ids.info_loker.color = f"⚠️ LOKER {ketikan.upper()} SUDAH TERISI!", (0.9, 0.5, 0.0, 1) 
            else: self.ids.info_loker.text, self.ids.info_loker.color = f"✅ Loker {ketikan.upper()} Tersedia", (0.2, 0.6, 0.9, 1) 
        else:
            self.ids.info_loker.text, self.ids.info_loker.color = "❌ Loker tidak ditemukan", (0.5, 0.5, 0.5, 1)
            
    def simpan_transaksi(self):
        hp, nama, loker_ketik, tarif, hari, perkiraan = self.ids.input_hp.text, self.ids.input_nama.text, self.ids.input_loker.text.upper(), self.ids.input_tarif.text, self.ids.input_hari.text, self.ids.input_perkiraan.text
        if not hp or not nama or not loker_ketik or tarif == "Pilih Tarif": return
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute("SELECT id FROM loker WHERE nomor_loker = ? AND status = 'Tersedia'", (loker_ketik,))
        hasil_loker = kursor.fetchone()
        if not hasil_loker: 
            koneksi.close()
            return
        waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tarif_db = get_tarif_sekarang()
        harga_24 = tarif_db.get('TARIF_24_JAM', 65000)
        uang_muka = int(hari) * harga_24 if "24 Jam" in tarif and hari.isdigit() else 0
        kursor.execute("SELECT id, jumlah_titip FROM pelanggan WHERE no_hp = ?", (hp,))
        hasil_pel = kursor.fetchone()
        if hasil_pel: 
            id_pelanggan, jumlah_baru = hasil_pel[0], (hasil_pel[1] or 0) + 1
            kursor.execute("UPDATE pelanggan SET jumlah_titip = ?, foto_ktp = COALESCE(?, foto_ktp), waktu_update_ktp = COALESCE(?, waktu_update_ktp) WHERE id = ?", (jumlah_baru, self.path_foto_tersimpan or None, waktu if self.path_foto_tersimpan else None, id_pelanggan))
        else:
            kursor.execute("INSERT INTO pelanggan (nama, no_hp, jumlah_titip, foto_ktp, waktu_update_ktp) VALUES (?, ?, 1, ?, ?)", (nama, hp, self.path_foto_tersimpan or None, waktu if self.path_foto_tersimpan else None))
            id_pelanggan = kursor.lastrowid 
        kode_pin = str(random.randint(1000, 9999))
        while kursor.execute("SELECT id FROM transaksi_loker WHERE kode_unik = ?", (kode_pin,)).fetchone(): kode_pin = str(random.randint(1000, 9999))
        kasir_aktif = App.get_running_app().session_username
        kursor.execute('''INSERT INTO transaksi_loker (id_pelanggan, id_loker, jenis_tarif, perkiraan_ambil, waktu_titip, sudah_dibayar, kode_unik, nama_kasir) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (id_pelanggan, hasil_loker[0], tarif, perkiraan, waktu, uang_muka, kode_pin, kasir_aktif))
        kursor.execute("UPDATE loker SET status = 'Terisi' WHERE id = ?", (hasil_loker[0],))
        koneksi.commit()
        koneksi.close()
        no_tujuan = '62' + hp[1:] if hp.startswith('0') else hp
        teks_masuk = f"Halo {nama},\nTerima kasih telah menggunakan GoLockers.\n\nDetail Penitipan:\nLoker: {loker_ketik}\nWaktu Titip: {waktu}\n\n*KODE PENGAMBILAN: {kode_pin}*\nSimpan pesan ini dan tunjukkan kode 4-digit di atas ke Kasir saat pengambilan barang."
        try: webbrowser.open(f"https://wa.me/{no_tujuan}?text={urllib.parse.quote(teks_masuk)}")
        except: pass
        self.ids.input_hp.text = self.ids.input_nama.text = self.ids.input_loker.text = self.ids.input_hari.text = self.ids.input_perkiraan.text = self.ids.info_loker.text = ""
        self.ids.input_tarif.text = "Pilih Tarif"
        self.ids.wadah_saran_hp.clear_widgets() 
        self.ids.input_hari.disabled = True
        self.path_foto_tersimpan = ""
        self.ids.info_ktp.text, self.ids.info_ktp.color = "Status KTP: Belum Diambil", (0.4, 0.4, 0.4, 1)
        self.ids.btn_kamera.text, self.ids.btn_kamera.background_color = "AMBIL FOTO KTP (SIMULASI)", (0.2, 0.6, 0.9, 1)
        self.manager.current = 'menu_loker'

class CheckOutScreen(Screen):
    id_transaksi_aktif, id_loker_aktif, no_hp_aktif, nama_aktif, nomor_loker_aktif, waktu_titip_aktif, biaya_keseluruhan, teks_struk_wa = None, None, "", "", "", "", 0, ""
    def cari_data(self, mode):
        kata_kunci = self.ids.input_cari.text.upper()
        if not kata_kunci: return
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        
        # 🌟 QUERY DIPERBARUI: Mengambil p.jumlah_titip dari tabel pelanggan
        query = f'''SELECT t.id, t.waktu_titip, t.jenis_tarif, t.sudah_dibayar, p.nama, p.no_hp, l.id, l.nomor_loker, t.kode_unik, p.jumlah_titip 
                    FROM transaksi_loker t JOIN pelanggan p ON t.id_pelanggan = p.id JOIN loker l ON t.id_loker = l.id 
                    WHERE {'l.nomor_loker' if mode == 'loker' else 't.kode_unik'} = ? AND l.status = 'Terisi' '''
        kursor.execute(query, (kata_kunci,))
        hasil = kursor.fetchone()
        koneksi.close()
        
        if hasil:
            self.id_transaksi_aktif, self.waktu_titip_aktif, tarif, uang_muka, self.nama_aktif, self.no_hp_aktif, self.id_loker_aktif, self.nomor_loker_aktif, kode_unik, jumlah_titip = hasil
            waktu_titip = datetime.datetime.strptime(self.waktu_titip_aktif, "%Y-%m-%d %H:%M:%S")
            waktu_sekarang = datetime.datetime.now()
            menit_total = math.ceil((waktu_sekarang - waktu_titip).total_seconds() / 60)
            teks_durasi = f"{menit_total // 60} Jam {menit_total % 60} Menit"
            
            tarif_db = get_tarif_sekarang()
            t_dasar = tarif_db.get('TARIF_DASAR', 27000)
            t_jam = tarif_db.get('TARIF_PER_JAM', 9000)
            t_tanggung = tarif_db.get('TARIF_TANGGUNG', 5000)
            t_24 = tarif_db.get('TARIF_24_JAM', 65000)
            
            biaya = 0
            if "24 Jam" in tarif:
                waktu_jatah_menit = (uang_muka // t_24 if uang_muka > 0 else 1) * 1440
                if menit_total <= waktu_jatah_menit + 10: biaya = uang_muka
                else:
                    kelebihan_menit = menit_total - waktu_jatah_menit
                    hari_ekstra = kelebihan_menit // 1440
                    sisa_mnt = kelebihan_menit % 1440
                    jam_over = sisa_mnt // 60
                    mnt_over = sisa_mnt % 60
                    if mnt_over <= 10: tambahan_mnt = 0
                    elif mnt_over <= 39: tambahan_mnt = t_tanggung
                    else: tambahan_mnt = t_jam
                    biaya_overtime = (jam_over * t_jam) + tambahan_mnt
                    if biaya_overtime > t_24 or sisa_mnt > 430: biaya_overtime = t_24
                    biaya = uang_muka + (hari_ekstra * t_24) + biaya_overtime
            else:
                if menit_total <= 190: 
                    biaya = t_dasar  
                else:
                    jam_total = menit_total // 60
                    mnt_total = menit_total % 60
                    if mnt_total <= 10: tambahan_mnt = 0
                    elif mnt_total <= 39: tambahan_mnt = t_tanggung
                    else: tambahan_mnt = t_jam
                    biaya = (jam_total * t_jam) + tambahan_mnt
                    
            total_tagihan_akhir = max(0, biaya - uang_muka)
            self.biaya_keseluruhan = biaya 
            
            # 🌟 MENAMPILKAN TOTAL TITIP DI TEKS DETAIL
            self.ids.lbl_detail.text = f"Nama: {self.nama_aktif} (Loyalitas: {jumlah_titip}x Titip)\nNo. HP: {self.no_hp_aktif}\nLoker: {self.nomor_loker_aktif} (PIN: {kode_unik})\nTarif: {tarif}\n\nWaktu Titip : {waktu_titip.strftime('%H:%M - %d/%m/%Y')}\nWaktu Ambil : {waktu_sekarang.strftime('%H:%M - %d/%m/%Y')}\nDurasi Total : {teks_durasi}\n\nBiaya Total : Rp {biaya:,}\nUang Muka   : Rp {uang_muka:,}"
            self.ids.lbl_detail.color = (0.1, 0.1, 0.1, 1) 
            self.ids.lbl_total_bayar.text = f"SISA TAGIHAN: Rp {total_tagihan_akhir:,}"
            self.ids.btn_lunasi.disabled = False 
            self.teks_struk_wa = urllib.parse.quote(f"Halo {self.nama_aktif},\nTerima kasih telah menggunakan GoLockers.\n\nDetail:\nLoker: {self.nomor_loker_aktif}\nDurasi: {teks_durasi}\nTotal Tagihan: Rp {total_tagihan_akhir:,}\n\nStatus: LUNAS\nBarang telah diambil.")
        else:
            self.ids.lbl_detail.text, self.ids.lbl_detail.color = f"Data '{kata_kunci}' tidak ditemukan.", (0.9, 0.1, 0.1, 1)
            self.ids.lbl_total_bayar.text, self.ids.btn_lunasi.disabled = "SISA TAGIHAN: Rp 0", True

    def lunasi_transaksi(self):
        if not self.id_transaksi_aktif: return
        waktu_sekarang_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        kasir_aktif = App.get_running_app().session_username 
        
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute('''INSERT INTO riwayat_transaksi (nama_pelanggan, nomor_loker, waktu_titip, waktu_ambil, total_pendapatan, nama_kasir) VALUES (?, ?, ?, ?, ?, ?)''', (self.nama_aktif, self.nomor_loker_aktif, self.waktu_titip_aktif, waktu_sekarang_str, self.biaya_keseluruhan, kasir_aktif))
        kursor.execute("UPDATE loker SET status = 'Tersedia' WHERE id = ?", (self.id_loker_aktif,))
        kursor.execute("DELETE FROM transaksi_loker WHERE id = ?", (self.id_transaksi_aktif,))
        koneksi.commit()
        koneksi.close()
        
        no_tujuan = '62' + self.no_hp_aktif[1:] if self.no_hp_aktif.startswith('0') else self.no_hp_aktif
        try: webbrowser.open(f"https://wa.me/{no_tujuan}?text={self.teks_struk_wa}")
        except: pass
        self.kembali_ke_menu()
        
    def kembali_ke_menu(self):
        self.ids.input_cari.text = ""
        self.ids.lbl_detail.text, self.ids.lbl_detail.color = "Silakan masukkan nomor loker atau Kode PIN 4-digit pelanggan.", (0.1, 0.1, 0.1, 1)
        self.ids.lbl_total_bayar.text, self.ids.btn_lunasi.disabled = "TOTAL TAGIHAN: Rp 0", True
        self.id_transaksi_aktif = None
        self.manager.current = 'menu_loker'

class MonitoringScreen(Screen):
    def muat_data_loker(self):
        grid = self.ids.grid_loker
        grid.clear_widgets() 
        self.ids.lbl_info_detail.text = "Klik salah satu kotak loker di atas untuk melihat detail."
        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        kursor.execute('''SELECT l.id, l.nomor_loker, l.ukuran, l.status, t.waktu_titip, t.jenis_tarif FROM loker l LEFT JOIN transaksi_loker t ON l.id = t.id_loker AND l.status = 'Terisi' ''')
        semua_loker = kursor.fetchall()
        koneksi.close()
        
        loker_terisi = sorted([l for l in semua_loker if l[3] == 'Terisi'], key=lambda x: x[0])
        loker_kosong = sorted([l for l in semua_loker if l[3] == 'Tersedia'], key=lambda x: x[0])
        
        for loker in (loker_terisi + loker_kosong):
            loker_id, nomor, ukuran, status, waktu_titip, tarif = loker
            if status == 'Terisi':
                warna = (0.9, 0.5, 0.0, 1) 
                if tarif == "Per Jam" and waktu_titip:
                    wt_obj = datetime.datetime.strptime(waktu_titip, "%Y-%m-%d %H:%M:%S")
                    if (datetime.datetime.now() - wt_obj).total_seconds() / 60 > 390: warna = (0.9, 0.1, 0.1, 1) 
            else: warna = (0.2, 0.6, 0.9, 1) 
            btn = Button(text=f"{nomor}\n({ukuran[0]})", size_hint_y=None, height=60, background_color=warna, background_normal='', bold=True, halign='center')
            btn.bind(on_release=lambda b, n=nomor, s=status: self.tampilkan_detail(n, s))
            grid.add_widget(btn)
        self.ids.lbl_statistik.text = f"Total: {len(semua_loker)} | Terisi: {len(loker_terisi)} | Kosong: {len(loker_kosong)}"
        
    def tampilkan_detail(self, nomor, status):
        if status == 'Tersedia': self.ids.lbl_info_detail.text = f"LOKER {nomor}\nStatus: KOSONG\nSiap digunakan."
        else:
            koneksi = sqlite3.connect('golocker_v6.db')
            kursor = koneksi.cursor()
            kursor.execute('''SELECT p.nama, p.no_hp, t.waktu_titip, t.jenis_tarif, t.sudah_dibayar, t.nama_kasir FROM transaksi_loker t JOIN pelanggan p ON t.id_pelanggan = p.id JOIN loker l ON t.id_loker = l.id WHERE l.nomor_loker = ? AND l.status = 'Terisi' ''', (nomor,))
            hasil = kursor.fetchone()
            koneksi.close()
            
            if hasil:
                nama, hp, waktu_titip_str, tarif, uang_muka, n_kasir = hasil
                waktu_titip_obj = datetime.datetime.strptime(waktu_titip_str, "%Y-%m-%d %H:%M:%S")
                waktu_sekarang = datetime.datetime.now()
                menit_total = math.ceil((waktu_sekarang - waktu_titip_obj).total_seconds() / 60)
                
                tarif_db = get_tarif_sekarang()
                t_dasar = tarif_db.get('TARIF_DASAR', 27000)
                t_jam = tarif_db.get('TARIF_PER_JAM', 9000)
                t_tanggung = tarif_db.get('TARIF_TANGGUNG', 5000)
                t_24 = tarif_db.get('TARIF_24_JAM', 65000)
                
                biaya = 0
                if "24 Jam" in tarif:
                    waktu_jatah_menit = (uang_muka // t_24 if uang_muka > 0 else 1) * 1440
                    if menit_total <= waktu_jatah_menit + 10: biaya = uang_muka
                    else:
                        kelebihan_menit = menit_total - waktu_jatah_menit
                        hari_ekstra = kelebihan_menit // 1440
                        sisa_mnt = kelebihan_menit % 1440
                        jam_over = sisa_mnt // 60
                        mnt_over = sisa_mnt % 60
                        if mnt_over <= 10: tambahan_mnt = 0
                        elif mnt_over <= 39: tambahan_mnt = t_tanggung
                        else: tambahan_mnt = t_jam
                        biaya_overtime = (jam_over * t_jam) + tambahan_mnt
                        if biaya_overtime > t_24 or sisa_mnt > 430: biaya_overtime = t_24
                        biaya = uang_muka + (hari_ekstra * t_24) + biaya_overtime
                else:
                    if menit_total <= 190: 
                        biaya = t_dasar  
                    else:
                        jam_total = menit_total // 60
                        mnt_total = menit_total % 60
                        if mnt_total <= 10: tambahan_mnt = 0
                        elif mnt_total <= 39: tambahan_mnt = t_tanggung
                        else: tambahan_mnt = t_jam
                        biaya = (jam_total * t_jam) + tambahan_mnt
                        
                total_tagihan_akhir = max(0, biaya - uang_muka)
                teks = f"LOKER {nomor} (Oleh: {n_kasir})\nPenyewa: {nama} ({hp})\nMasuk: {waktu_titip_obj.strftime('%d/%m/%y - %H:%M')}  |  Durasi: {menit_total // 60} Jam {menit_total % 60} Mnt\nPaket: {tarif}\nEstimasi Sisa Tagihan : Rp {total_tagihan_akhir:,}"
                self.ids.lbl_info_detail.text = teks

class LaporanScreen(Screen):
    bulan_indo = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    def muat_awal(self):
        sekarang = datetime.datetime.now()
        pilihan = ["Hari Ini", "7 Hari Terakhir"]
        for i in range(12):
            b = sekarang.month - i
            t = sekarang.year
            if b <= 0: 
                b += 12
                t -= 1
            pilihan.append(f"{self.bulan_indo[b]} {t}")
        self.ids.spinner_rentang.values = pilihan
        if self.ids.spinner_rentang.text not in pilihan: self.ids.spinner_rentang.text = "Hari Ini"
        self.filter_laporan(self.ids.spinner_rentang.text)

    def filter_laporan(self, rentang_dipilih):
        if not rentang_dipilih: return
        sekarang = datetime.datetime.now()
        awal = akhir = ""
        
        if rentang_dipilih == "Hari Ini":
            awal = sekarang.strftime("%Y-%m-%d 00:00:00")
            akhir = sekarang.strftime("%Y-%m-%d 23:59:59")
        elif rentang_dipilih == "7 Hari Terakhir":
            awal = (sekarang - datetime.timedelta(days=6)).strftime("%Y-%m-%d 00:00:00")
            akhir = sekarang.strftime("%Y-%m-%d 23:59:59")
        else:
            try:
                parts = rentang_dipilih.split()
                nama_b, tahun = parts[0], int(parts[1])
                angka_b = self.bulan_indo.index(nama_b)
                hari_terakhir = calendar.monthrange(tahun, angka_b)[1]
                awal = f"{tahun}-{angka_b:02d}-01 00:00:00"
                akhir = f"{tahun}-{angka_b:02d}-{hari_terakhir:02d} 23:59:59"
            except:
                awal = sekarang.strftime("%Y-%m-%d 00:00:00")
                akhir = sekarang.strftime("%Y-%m-%d 23:59:59")

        koneksi = sqlite3.connect('golocker_v6.db')
        kursor = koneksi.cursor()
        try:
            kursor.execute('''SELECT nama_pelanggan, nomor_loker, waktu_titip, waktu_ambil, total_pendapatan, nama_kasir FROM riwayat_transaksi WHERE waktu_ambil >= ? AND waktu_ambil <= ? ORDER BY waktu_ambil DESC''', (awal, akhir))
        except:
            kursor.execute('''SELECT nama_pelanggan, nomor_loker, waktu_titip, waktu_ambil, total_pendapatan, 'Sistem' as nama_kasir FROM riwayat_transaksi WHERE waktu_ambil >= ? AND waktu_ambil <= ? ORDER BY waktu_ambil DESC''', (awal, akhir))
            
        riwayat_semua = kursor.fetchall()
        koneksi.close()
        
        wadah = self.ids.wadah_riwayat
        wadah.clear_widgets()
        total_omzet = 0
        
        for data in riwayat_semua:
            nama, loker, w_titip, w_ambil, pendapatan, n_kasir = data
            total_omzet += pendapatan
            w_titip_pendek = datetime.datetime.strptime(w_titip, "%Y-%m-%d %H:%M:%S").strftime("%d/%m %H:%M")
            w_ambil_pendek = datetime.datetime.strptime(w_ambil, "%Y-%m-%d %H:%M:%S").strftime("%d/%m %H:%M")
            teks_riwayat = f" {nama}  (Loker {loker})\n Masuk: {w_titip_pendek}  |  Keluar: {w_ambil_pendek}\n Transaksi: Rp {pendapatan:,} (Oleh: {n_kasir})"
            btn_frame = Button(text=teks_riwayat, color=(0.1, 0.1, 0.1, 1), background_color=(0.9, 0.9, 0.9, 1), background_normal='', size_hint_y=None, height=75, halign='left', valign='middle')
            btn_frame.bind(size=btn_frame.setter('text_size'))
            wadah.add_widget(btn_frame)
            
        self.ids.lbl_omzet_total.text = f"Rp {total_omzet:,}"

class GoLockerApp(App):
    session_username = "" 
    session_role = ""
    def build(self): return Builder.load_string(desain_antarmuka)

if __name__ == '__main__': GoLockerApp().run()