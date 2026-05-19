import sqlite3
import os

# Menentukan lokasi file database secara otomatis di folder 'instance/'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'database.db')

def get_db_connection():
    """Fungsi untuk membuka koneksi ke SQLite"""
    conn = sqlite3.connect(DB_PATH)
    # Row_factory agar hasil query bisa diakses layaknya dictionary (key-value)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Fungsi untuk membuat kerangka tabel jika belum ada"""
    # Pastikan folder instance ada, jika belum buat foldernya
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Eksekusi perintah SQL untuk membuat tabel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historis_stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_obat TEXT NOT NULL,
            bulan INTEGER NOT NULL,
            tahun INTEGER NOT NULL,
            jumlah_stok INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Berhasil: Tabel 'historis_stok' siap digunakan!")

def get_semua_stok():
    """Mengambil seluruh data historis dari database, diurutkan secara kronologis (Bulan & Tahun)"""
    conn = get_db_connection()
    
    # Query SQL dengan "Penerjemah" agar SQLite tahu urutan bulan kalender yang benar
    query = '''
        SELECT * FROM historis_stok 
        ORDER BY 
            tahun ASC,
            CASE LOWER(TRIM(bulan))
                WHEN 'januari' THEN 1 WHEN 'jan' THEN 1
                WHEN 'februari' THEN 2 WHEN 'feb' THEN 2
                WHEN 'maret' THEN 3 WHEN 'mar' THEN 3
                WHEN 'april' THEN 4 WHEN 'apr' THEN 4
                WHEN 'mei' THEN 5
                WHEN 'juni' THEN 6 WHEN 'jun' THEN 6
                WHEN 'juli' THEN 7 WHEN 'jul' THEN 7
                WHEN 'agustus' THEN 8 WHEN 'agu' THEN 8
                WHEN 'september' THEN 9 WHEN 'sep' THEN 9
                WHEN 'oktober' THEN 10 WHEN 'okt' THEN 10
                WHEN 'november' THEN 11 WHEN 'nov' THEN 11
                WHEN 'desember' THEN 12 WHEN 'des' THEN 12
                ELSE 99
            END ASC,
            nama_obat ASC
    '''
    data = conn.execute(query).fetchall()
    conn.close()
    return data

def get_stok_by_obat(nama_obat):
    """Mengambil data historis untuk obat tertentu diurutkan dari tertua ke terbaru"""
    conn = get_db_connection()
    data = conn.execute(
        'SELECT * FROM historis_stok WHERE nama_obat = ? ORDER BY tahun ASC, bulan ASC',
        (nama_obat,)
    ).fetchall()
    conn.close()
    return data

def tambah_stok(nama_obat, bulan, tahun, jumlah_stok):
    """Menambahkan data historis baru ke database"""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO historis_stok (nama_obat, bulan, tahun, jumlah_stok) VALUES (?, ?, ?, ?)',
        (nama_obat, bulan, tahun, jumlah_stok)
    )
    conn.commit()
    conn.close()

def update_stok(id_stok, nama_obat, bulan, tahun, jumlah_stok):
    """Memperbarui data historis yang sudah ada"""
    conn = get_db_connection()
    conn.execute(
        'UPDATE historis_stok SET nama_obat = ?, bulan = ?, tahun = ?, jumlah_stok = ? WHERE id = ?',
        (nama_obat, bulan, tahun, jumlah_stok, id_stok)
    )
    conn.commit()
    conn.close()

def hapus_stok(id_stok):
    """Menghapus data historis berdasarkan ID"""
    conn = get_db_connection()
    conn.execute('DELETE FROM historis_stok WHERE id = ?', (id_stok,))
    conn.commit()
    conn.close()