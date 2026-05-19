# app/utils/least_square.py
import pandas as pd

def hitung_prediksi_least_square(data_historis, bulan_kedepan=1):
    if not data_historis or len(data_historis) < 2:
        return None, "Data historis tidak cukup untuk melakukan prediksi."

    df = pd.DataFrame(data_historis)
    
    peta_bulan_ke_angka = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
        'january': 1, 'february': 2, 'march': 3, 'may': 5, 
        'june': 6, 'july': 7, 'august': 8, 'october': 10, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mei': 5, 'jun': 6, 
        'jul': 7, 'agu': 8, 'aug': 8, 'sep': 9, 'okt': 10, 'oct': 10, 
        'nov': 11, 'des': 12, 'dec': 12
    }

    peta_angka_ke_nama = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }

    bulan_bersih = df['bulan'].astype(str).str.strip().str.lower()
    df['bulan_angka'] = bulan_bersih.map(peta_bulan_ke_angka)
    df['bulan_angka'] = df['bulan_angka'].fillna(pd.to_numeric(df['bulan'], errors='coerce'))

    df['tahun'] = pd.to_numeric(df['tahun'], errors='coerce')
    df['jumlah_stok'] = pd.to_numeric(df['jumlah_stok'], errors='coerce')

    df = df.dropna(subset=['tahun', 'bulan_angka', 'jumlah_stok'])
    df = df.sort_values(by=['tahun', 'bulan_angka']).reset_index(drop=True)
    
    df['bulan'] = df['bulan_angka'].astype(int).map(peta_angka_ke_nama)
    df['tahun'] = df['tahun'].astype(int)

    n = len(df)
    
    df['X'] = range(1, n + 1)
    df['Y'] = df['jumlah_stok']
    df['XY'] = df['X'] * df['Y']
    df['X2'] = df['X'] ** 2

    sum_X = df['X'].sum()
    sum_Y = df['Y'].sum()
    sum_XY = df['XY'].sum()
    sum_X2 = df['X2'].sum()

    pembagi_b = (n * sum_X2) - (sum_X ** 2)
    if pembagi_b == 0:
        return None, "Perhitungan gagal karena variansi waktu nol."
        
    b = ((n * sum_XY) - (sum_X * sum_Y)) / pembagi_b
    a = (sum_Y - (b * sum_X)) / n

    df['forecast'] = a + (b * df['X'])
    df['error'] = df['Y'] - df['forecast']
    df['abs_error'] = df['error'].abs()
    df['squared_error'] = df['error'] ** 2
    df['ape'] = (df['abs_error'] / df['Y'].replace(0, 0.0001)) * 100

    MSE = df['squared_error'].mean()
    MAD = df['abs_error'].mean()
    MAPE = df['ape'].mean()

    # ---> BAGIAN PENYEMBUH TABEL KOSONG <---
    prediksi_mendatang = []
    
    tahun_terakhir = df['tahun'].iloc[-1]
    bulan_terakhir = df['bulan_angka'].iloc[-1] 
    
    tahun_prediksi = tahun_terakhir
    bulan_prediksi = bulan_terakhir

    for i in range(1, bulan_kedepan + 1):
        x_baru = n + i
        y_prediksi = a + (b * x_baru)
        hasil_bulat = max(0, round(y_prediksi))
        
        bulan_prediksi += 1
        if bulan_prediksi > 12:
            bulan_prediksi = 1
            tahun_prediksi += 1
            
        nama_bulan_prediksi = peta_angka_ke_nama[bulan_prediksi]
        
        # Format ini yang dibutuhkan oleh tabel HTML agar tidak kosong
        prediksi_mendatang.append({
            'periode': f"{nama_bulan_prediksi} {tahun_prediksi}",
            'nilai': hasil_bulat
        })

    hasil_akhir = {
        'persamaan': {'a': a, 'b': b},
        'evaluasi': {
            'MSE': round(MSE, 3),
            'MAD': round(MAD, 3),
            'MAPE': round(MAPE, 3)
        },
        'prediksi_mendatang': prediksi_mendatang, 
        'data_tabel': df.to_dict('records') 
    }

    return hasil_akhir, None