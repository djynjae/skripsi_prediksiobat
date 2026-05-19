import pandas as pd
import sqlite3
import os

# Mengatur jalur (path) menuju file database dan folder CSV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'database.db')
CSV_DIR = os.path.join(BASE_DIR, 'data_csv')

def import_csv_ke_db():
    """Fungsi untuk membaca 3 file CSV dan memindahkannya ke tabel historis_stok"""
    
    file_mapping = {
        'obh_combi.csv': 'obh_combi',
        'paratusin.csv': 'paratusin',
        'pimtrakol.csv': 'pimtrakol'
    }

    conn = sqlite3.connect(DB_PATH)

    for nama_file, nama_obat in file_mapping.items():
        file_path = os.path.join(CSV_DIR, nama_file)

        if os.path.exists(file_path):
            try:
                # 1. Baca CSV dengan pemisah titik koma (sep=';')
                df = pd.read_csv(file_path, sep=';')

                # 2. Tambahkan kolom 'nama_obat' agar sesuai dengan tabel SQLite
                df['nama_obat'] = nama_obat

                # 3. Ubah nama kolom sesuai dengan nama di tabel database
                # Sisi kiri: nama di CSV kamu | Sisi kanan: nama di database
                df = df.rename(columns={
                    'Bulan': 'bulan',
                    'Tahun': 'tahun',
                    'Stok': 'jumlah_stok'
                })

                # 4. Filter hanya kolom yang dibutuhkan (Kolom 'No' otomatis ditinggalkan/diabaikan)
                df_to_insert = df[['nama_obat', 'bulan', 'tahun', 'jumlah_stok']]

                # 5. Suntikkan ke database
                df_to_insert.to_sql('historis_stok', conn, if_exists='append', index=False)
                
                print(f"✅ Berhasil menyedot data {nama_file} ke database.")
            except Exception as e:
                print(f"❌ Gagal memproses {nama_file}: {e}")
        else:
            print(f"⚠️ File {nama_file} tidak ditemukan di folder {CSV_DIR}.")

    conn.close()
    print("🚀 Proses pemindahan data CSV selesai!")