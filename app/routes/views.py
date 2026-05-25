from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from app.utils.least_square import hitung_prediksi_least_square
from flask import request
import pandas as pd
import sqlite3
from app.models.database import get_semua_stok, get_stok_by_obat, tambah_stok, update_stok, hapus_stok
from flask import render_template, request, redirect, url_for, flash
import json

views = Blueprint('views', __name__)

DB_PATH = 'instance/database.db'

# --- FUNGSI KEAMANAN ---
# Decorator untuk mengecek apakah user sudah login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('views.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTE LOGIN & LOGOUT ---
@views.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, langsung lempar ke dashboard
    if 'logged_in' in session:
        return redirect(url_for('views.index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Cek kecocokan (Kamu bisa ganti username/password ini)
        if username == 'apotek' and password == '12345':
            session['logged_in'] = True
            return redirect(url_for('views.index'))
        else:
            error = 'Username atau password salah!'

    return render_template('login.html', error=error)

@views.route('/import-csv-obat', methods=['POST'])
@login_required
def import_csv_obat():
    file = request.files.get('file_csv')
    nama_obat = request.form.get('nama_obat')

    if not file or file.filename == '':
        flash('Gagal: Tidak ada file CSV yang dipilih!', 'error')
        return redirect(url_for('views.data_obat'))

    try:
        df = pd.read_csv(file, sep=';', encoding='utf-8-sig')
        df.columns = df.columns.str.lower().str.strip()

        # Validasi kolom wajib
        kolom_wajib = ['bulan', 'tahun', 'stok']
        for kolom in kolom_wajib:
            if kolom not in df.columns:
                flash(f'Gagal: Kolom "{kolom}" tidak ditemukan di file CSV!', 'error')
                return redirect(url_for('views.data_obat'))

        # =======================================================
        # KAMUS PENERJEMAH BULAN OTOMATIS (Mencegat Ulah Excel)
        # =======================================================
        kamus_bulan = {
            'jan': 'Januari', 'feb': 'Februari', 'mar': 'Maret', 'apr': 'April',
            'may': 'Mei', 'jun': 'Juni', 'jul': 'Juli', 'aug': 'Agustus',
            'sep': 'September', 'oct': 'Oktober', 'nov': 'November', 'dec': 'Desember',
            'januari': 'Januari', 'februari': 'Februari', 'maret': 'Maret', 'april': 'April',
            'mei': 'Mei', 'juni': 'Juni', 'juli': 'Juli', 'agustus': 'Agustus',
            'september': 'September', 'oktober': 'Oktober', 'november': 'November', 'desember': 'Desember'
        }

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        berhasil_masuk = 0
        
        for index, row in df.iterrows():
            # 1. Ambil data bulan dari CSV, ubah ke huruf kecil semua, hapus spasi ujung
            bulan_mentah = str(row['bulan']).strip().lower()
            
            # 2. Terjemahkan otomatis menggunakan kamus di atas. 
            # Jika tidak terdaftar di kamus, gunakan kata aslinya dengan huruf kapital di awal.
            bulan = kamus_bulan.get(bulan_mentah, bulan_mentah.capitalize())
            
            tahun = int(row['tahun'])
            jumlah_stok = int(row['stok']) 

            # 3. Masukkan data yang sudah rapi berbahasa Indonesia ke database
            cursor.execute(
                'INSERT INTO historis_stok (nama_obat, bulan, tahun, jumlah_stok) VALUES (?, ?, ?, ?)',
                (nama_obat, bulan, tahun, jumlah_stok)
            )
            berhasil_masuk += 1

        conn.commit()
        conn.close()

        flash(f'Berhasil mengimpor {berhasil_masuk} baris data CSV ke dalam sistem.', 'success')

    except Exception as e:
        flash(f'Terjadi kesalahan saat memproses CSV: {str(e)}', 'error')

    return redirect(url_for('views.data_obat'))

@views.route('/logout')
def logout():
    # Hapus data login dari session
    session.pop('logged_in', None)
    return redirect(url_for('views.login'))

# --- ROUTE HALAMAN UTAMA (Diberi pelindung @login_required) ---
@views.route('/')
@login_required
def index():
    # 1. Ambil data mentah dari database
    data_raw = get_semua_stok()
    data_stok = [dict(baris) for baris in data_raw]

    # ==========================================
    # HITUNG KARTU RINGKASAN & ERROR PREDIKSI
    # ==========================================
    total_data = len(data_stok)
    total_stok = sum(baris['jumlah_stok'] for baris in data_stok)

    data_obh = [d for d in data_stok if d['nama_obat'] == 'obh_combi']
    data_paratusin = [d for d in data_stok if d['nama_obat'] == 'paratusin']
    data_demacolin = [d for d in data_stok if d['nama_obat'] == 'demacolin']
    
    total_prediksi = 0
    
    # Variabel keranjang penampung error rata-rata total seluruh obat
    total_mad = 0
    total_mse = 0
    total_mape = 0
    obat_dihitung = 0
    periode_prediksi = "-"

    # REVISI: Tambahan struktur penampung untuk kebutuhan Javascript Dropdown & Rekomendasi
    data_semua_obat = {}
    ringkasan_mape = []

    # Map array data ke nama string kunci obatnya
    pemetaan_obat = [
        ('obh_combi', data_obh),
        ('paratusin', data_paratusin),
        ('demacolin', data_demacolin)
    ]

    # Jalankan algoritma Least Square untuk masing-masing obat
    for nama_raw, d_obat in pemetaan_obat:
        hasil, err = hitung_prediksi_least_square(d_obat, 1)
        if hasil:
            prediksi_terdekat = {'periode': '-', 'nilai': 0}
            if len(hasil['prediksi_mendatang']) > 0:
                prediksi_terdekat = hasil['prediksi_mendatang'][0]
                total_prediksi += prediksi_terdekat['nilai']
                # Ambil nama periode dari hasil kalkulasi (contoh: "Januari 2025")
                periode_prediksi = prediksi_terdekat['periode']
            
            # Ambil nilai evaluasi error-nya
            mape_nilai = hasil['evaluasi']['MAPE']
            mse_nilai = hasil['evaluasi']['MSE']
            mad_nilai = hasil['evaluasi']['MAD']

            # Tambahkan ke kalkulasi rata-rata total
            total_mad += mad_nilai
            total_mse += mse_nilai
            total_mape += mape_nilai
            obat_dihitung += 1

            # REVISI: Masukkan data individu obat ke dictionary untuk dibaca Live oleh JavaScript
            data_semua_obat[nama_raw] = {
                'MAD': float(mad_nilai),
                'MSE': float(mse_nilai),
                'MAPE': float(mape_nilai),
                'periode_depan': prediksi_terdekat['periode'],
                'nilai_depan': float(prediksi_terdekat['nilai'])
            }

            # REVISI: Catat ke list pembanding untuk mencari obat paling akurat (MAPE terkecil)
            ringkasan_mape.append({
                'nama_raw': nama_raw,
                'mape': float(mape_nilai),
                'prediksi': prediksi_terdekat
            })

    # Hitung rata-rata error dari ke-3 obat (Sebagai fallback default tampilan)
    rata_mad = round(total_mad / obat_dihitung, 2) if obat_dihitung > 0 else 0
    rata_mse = round(total_mse / obat_dihitung, 2) if obat_dihitung > 0 else 0
    rata_mape = round(total_mape / obat_dihitung, 2) if obat_dihitung > 0 else 0

    # REVISI: Cari obat mana yang memiliki performa akurasi terbaik (MAPE paling rendah)
    obat_terakurat = None
    if ringkasan_mape:
        ringkasan_mape.sort(key=lambda x: x['mape'])
        obat_terakurat = ringkasan_mape[0]
        
        # Set agar nilai default ringkasan yang pertama kali muncul mengikuti data obat terakurat
        obat_default = obat_terakurat['nama_raw']
        rata_mad = round(data_semua_obat[obat_default]['MAD'], 1)
        rata_mse = round(data_semua_obat[obat_default]['MSE'], 1)
        rata_mape = round(data_semua_obat[obat_default]['MAPE'], 1)
    # ==========================================

    # ==========================================
    # PERSIAPAN DATA GRAFIK CHART.JS
    # ==========================================
    labels_waktu = []
    data_grafik = {'obh_combi': [], 'paratusin': [], 'demacolin': []}
    keranjang_periode = {}

    for baris in data_stok:
        periode = f"{baris['bulan'].capitalize()} {baris['tahun']}"
        if periode not in keranjang_periode:
            keranjang_periode[periode] = {'obh_combi': 0, 'paratusin': 0, 'demacolin': 0}
            labels_waktu.append(periode)
            
        nama_obat = baris['nama_obat']
        if nama_obat in keranjang_periode[periode]:
            keranjang_periode[periode][nama_obat] = baris['jumlah_stok']

    for label in labels_waktu:
        data_grafik['obh_combi'].append(keranjang_periode[label]['obh_combi'])
        data_grafik['paratusin'].append(keranjang_periode[label]['paratusin'])
        data_grafik['demacolin'].append(keranjang_periode[label]['demacolin'])

    paket_chart = {'labels': labels_waktu, 'datasets': data_grafik}
    paket_chart_json = json.dumps(paket_chart)

    # REVISI: Kirim tambahan variabel data_semua_obat dan obat_terakurat ke index.html
    return render_template('index.html', 
                           chart_data=paket_chart_json,
                           total_data=total_data,
                           total_stok=total_stok,
                           total_prediksi=round(total_prediksi, 1),
                           rata_mad=rata_mad,
                           rata_mse=rata_mse,
                           rata_mape=rata_mape,
                           periode_prediksi=periode_prediksi,
                           data_semua_obat=data_semua_obat,
                           obat_terakurat=obat_terakurat)   

@views.route('/data-obat')
@login_required
def data_obat():
    # 1. Ambil data dari database
    data_stok_dari_db = get_semua_stok()
    
    # 2. Kirim data tersebut ke template HTML dengan variabel 'data_stok'
    return render_template('data_obat.html', active_page='data_obat', data_stok=data_stok_dari_db)

@views.route('/hapus-semua-obat', methods=['POST'])
@login_required
def hapus_semua_obat():
    # Menangkap nama obat dari form (misal: 'paratusin')
    nama_obat = request.form.get('nama_obat')

    if not nama_obat:
        flash('Gagal: Nama obat harus dipilih!', 'error')
        return redirect(url_for('views.data_obat'))

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Cek dulu ada berapa jumlah data obat tersebut sebelum dihapus (agar bisa ditampilkan di notifikasi)
        cursor.execute('SELECT COUNT(*) FROM historis_stok WHERE nama_obat = ?', (nama_obat,))
        jumlah_data = cursor.fetchone()[0]
        
        if jumlah_data == 0:
            flash(f'Tidak ada data {nama_obat} yang bisa dihapus. Tabel sudah kosong.', 'error')
        else:
            # Ini adalah perintah SQL untuk menghapus semua data berdasarkan nama obat
            cursor.execute('DELETE FROM historis_stok WHERE nama_obat = ?', (nama_obat,))
            conn.commit()
            flash(f'BERHASIL! {jumlah_data} data {nama_obat} telah dihapus permanen dari sistem.', 'success')
            
        conn.close()

    except Exception as e:
        flash(f'Terjadi kesalahan saat menghapus data: {str(e)}', 'error')

    return redirect(url_for('views.data_obat'))

@views.route('/prediksi', methods=['GET', 'POST'])
@login_required
def prediksi():
    hasil = None
    error_msg = None
    jenis_obat_terpilih = None
    bulan_kedepan = 1

    if request.method == 'POST':
        # Ambil data inputan dari Form UI
        jenis_obat_terpilih = request.form.get('jenis_obat')
        bulan_kedepan = int(request.form.get('bulan_kedepan', 1))
        
        # 1. Ambil data dari database berdasarkan jenis obat
        data_rows = get_stok_by_obat(jenis_obat_terpilih)
        
        # 2. Ubah format data SQLite Row menjadi List of Dictionary agar bisa dibaca Pandas
        data_list = [dict(row) for row in data_rows]
        
        # 3. Jalankan kalkulasi rumus Least Square
        hasil, error_msg = hitung_prediksi_least_square(data_list, bulan_kedepan)

    return render_template(
        'prediksi.html', 
        active_page='prediksi', 
        hasil=hasil, 
        error_msg=error_msg,
        obat_terpilih=jenis_obat_terpilih,
        bulan_kedepan=bulan_kedepan
    )

    # Rute untuk menangani form Tambah Data
@views.route('/tambah-obat', methods=['POST'])
@login_required
def tambah_obat():
    nama_obat = request.form.get('nama_obat')
    bulan = request.form.get('bulan')
    tahun = request.form.get('tahun')
    jumlah_stok = request.form.get('jumlah_stok')
    
    tambah_stok(nama_obat, bulan, tahun, jumlah_stok)
    flash('Data stok obat berhasil ditambahkan!', 'success')
    return redirect(url_for('views.data_obat'))

# Rute untuk menangani form Edit Data
@views.route('/edit-obat/<int:id>', methods=['POST'])
@login_required
def edit_obat(id):
    nama_obat = request.form.get('nama_obat')
    bulan = request.form.get('bulan')
    tahun = request.form.get('tahun')
    jumlah_stok = request.form.get('jumlah_stok')
    
    update_stok(id, nama_obat, bulan, tahun, jumlah_stok)
    flash('Data stok obat berhasil diperbarui!', 'success')
    return redirect(url_for('views.data_obat'))

# Rute untuk menangani tombol Hapus Data
@views.route('/hapus-obat/<int:id>', methods=['POST'])
@login_required
def hapus_obat(id):
    hapus_stok(id)
    flash('Data stok obat berhasil dihapus!', 'success')
    return redirect(url_for('views.data_obat'))

@views.route('/tentang')
@login_required
def tentang():
    return render_template('tentang.html', active_page='tentang')