from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from app.utils.least_square import hitung_prediksi_least_square
from flask import request
from app.models.database import get_semua_stok, get_stok_by_obat, tambah_stok, update_stok, hapus_stok
from flask import render_template, request, redirect, url_for, flash
import json

views = Blueprint('views', __name__)

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
    data_pimtrakol = [d for d in data_stok if d['nama_obat'] == 'pimtrakol']
    
    total_prediksi = 0
    
    # Variabel keranjang penampung error rata-rata
    total_mad = 0
    total_mse = 0
    total_mape = 0
    obat_dihitung = 0
    periode_prediksi = "-"

    # Jalankan algoritma Least Square untuk masing-masing obat
    for d_obat in [data_obh, data_paratusin, data_pimtrakol]:
        hasil, err = hitung_prediksi_least_square(d_obat, 1)
        if hasil:
            if len(hasil['prediksi_mendatang']) > 0:
                total_prediksi += hasil['prediksi_mendatang'][0]['nilai']
                # Ambil nama periode dari hasil kalkulasi (contoh: "Januari 2025")
                periode_prediksi = hasil['prediksi_mendatang'][0]['periode']
            
            # Tambahkan nilai evaluasi error-nya
            total_mad += hasil['evaluasi']['MAD']
            total_mse += hasil['evaluasi']['MSE']
            total_mape += hasil['evaluasi']['MAPE']
            obat_dihitung += 1

    # Hitung rata-rata error dari ke-3 obat
    rata_mad = round(total_mad / obat_dihitung, 2) if obat_dihitung > 0 else 0
    rata_mse = round(total_mse / obat_dihitung, 2) if obat_dihitung > 0 else 0
    rata_mape = round(total_mape / obat_dihitung, 2) if obat_dihitung > 0 else 0
    # ==========================================

    # ==========================================
    # PERSIAPAN DATA GRAFIK CHART.JS
    # ==========================================
    labels_waktu = []
    data_grafik = {'obh_combi': [], 'paratusin': [], 'pimtrakol': []}
    keranjang_periode = {}

    for baris in data_stok:
        periode = f"{baris['bulan'].capitalize()} {baris['tahun']}"
        if periode not in keranjang_periode:
            keranjang_periode[periode] = {'obh_combi': 0, 'paratusin': 0, 'pimtrakol': 0}
            labels_waktu.append(periode)
            
        nama_obat = baris['nama_obat']
        if nama_obat in keranjang_periode[periode]:
            keranjang_periode[periode][nama_obat] = baris['jumlah_stok']

    for label in labels_waktu:
        data_grafik['obh_combi'].append(keranjang_periode[label]['obh_combi'])
        data_grafik['paratusin'].append(keranjang_periode[label]['paratusin'])
        data_grafik['pimtrakol'].append(keranjang_periode[label]['pimtrakol'])

    paket_chart = {'labels': labels_waktu, 'datasets': data_grafik}
    paket_chart_json = json.dumps(paket_chart)

    # Kirim semua data termasuk error rate ke index.html
    return render_template('index.html', 
                           chart_data=paket_chart_json,
                           total_data=total_data,
                           total_stok=total_stok,
                           total_prediksi=total_prediksi,
                           rata_mad=rata_mad,
                           rata_mse=rata_mse,
                           rata_mape=rata_mape,
                           periode_prediksi=periode_prediksi)   

@views.route('/data-obat')
@login_required
def data_obat():
    # 1. Ambil data dari database
    data_stok_dari_db = get_semua_stok()
    
    # 2. Kirim data tersebut ke template HTML dengan variabel 'data_stok'
    return render_template('data_obat.html', active_page='data_obat', data_stok=data_stok_dari_db)

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