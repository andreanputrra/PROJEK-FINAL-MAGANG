import pandas as pd
import streamlit as st
import os
import sqlite3
from datetime import datetime
# Impor yang tidak lagi digunakan untuk solusi HTML cetak (PDF, Word, components)
# from docx import Document
# from fpdf import FPDF
# from streamlit import components as stc

# Konfigurasi database
DB_FILE = "pengeluaran_kas.db"

# --- Fungsi-fungsi Database ---

def get_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kas (
            id TEXT,
            tanggal TEXT,
            deskripsi_pekerjaan TEXT,
            deskripsi_pengeluaran TEXT,
            jumlah_barang INTEGER,
            unit TEXT,
            harga_per_satuan INTEGER,
            total_harga INTEGER,
            keterangan TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM kas", conn)
    # Pastikan kolom 'tanggal' diubah ke datetime, errors='coerce' akan mengubah yang gagal jadi NaT
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    conn.close()
    return df

def save_data(row):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kas (id, tanggal, deskripsi_pekerjaan, deskripsi_pengeluaran,
                         jumlah_barang, unit, harga_per_satuan, total_harga, keterangan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
    conn.commit()
    conn.close()

def delete_data_by_index(index):
    df = load_data()
    if index < len(df):
        id_to_delete = df.iloc[index]['id']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kas WHERE id = ?", (id_to_delete,))
        conn.commit()
        conn.close()

def update_data_by_id(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE kas SET
            tanggal = ?,
            deskripsi_pekerjaan = ?,
            deskripsi_pengeluaran = ?,
            jumlah_barang = ?,
            unit = ?,
            harga_per_satuan = ?,
            total_harga = ?,
            keterangan = ?
        WHERE id = ?
    """, data)
    conn.commit()
    conn.close()

# --- Fungsi-fungsi Bantuan/Utilities ---

def generate_id_transaksi(kode_pelanggan, tanggal, df):
    prefix = kode_pelanggan.upper() if kode_pelanggan else "X1"
    bulan_tahun = tanggal.strftime("%m%y")
    filter_prefix = prefix + bulan_tahun
    df_filtered = df[df['id'].notna() & df['id'].astype(str).str.startswith(filter_prefix)]
    nomor_urut = len(df_filtered) + 1
    nomor_urut_str = f"{nomor_urut:03d}"
    return f"{filter_prefix}{nomor_urut_str}"

def format_rupiah(x):
    try:
        if isinstance(x, (int, float)):
            return f"Rp {x:,.0f}".replace(",", ".")
        return x
    except:
        return x

# --- Fungsi Cetak Data ke HTML Lokal ---

# Fungsi untuk menulis DataFrame ke file HTML dan membukanya
def print_data(df_to_print): # Menggunakan nama df_to_print agar jelas bahwa ini adalah data yang akan dicetak
    # Tambahkan judul laporan dan styling yang lebih baik untuk cetak
    html_content = df_to_print.to_html(index=False) # Convert DataFrame to HTML table

    full_html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Pengeluaran Kas</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ text-align: center; margin-bottom: 20px; color: #333; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
                vertical-align: top;
                word-wrap: break-word; /* Memastikan teks panjang pecah baris */
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
                color: #555;
            }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f1f1; }}

            /* Styling khusus untuk cetak */
            @media print {{
                body {{ margin: 0; }} /* Hapus margin di mode cetak */
                table {{ border-collapse: collapse; }}
                th, td {{ border: 1px solid #000; padding: 6px; }} /* Border hitam untuk cetak */
                h1 {{ page-break-after: avoid; }} /* Hindari judul terpotong antar halaman */
                table {{ page-break-inside: auto; }} /* Tabel pecah halaman otomatis */
                tr {{ page-break-inside: avoid; page-break-after: auto; }} /* Baris tidak terpotong */
                thead {{ display: table-header-group; }} /* Header tabel muncul di setiap halaman */
            }}
        </style>
    </head>
    <body>
        <h1>Data Pengeluaran Kas</h1>
        {html_content}
    </body>
    </html>
    """
    
    html_path = "pengeluaran_kas_print.html" # Nama file HTML yang akan disimpan
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html_page)
        
        # Buka file HTML secara otomatis di browser default
        # Menggunakan webbrowser lebih robust daripada os.startfile
        import webbrowser
        webbrowser.open_new_tab(f"file://{os.path.abspath(html_path)}")
        
        st.success(f"Laporan berhasil dibuat dan dibuka di browser: {html_path}")
    except Exception as e:
        st.error(f"Gagal membuat atau membuka file HTML: {e}")


# --- Setup Awal ---
setup_database()

# --- Konfigurasi Streamlit ---
st.set_page_config(page_title="Pengeluaran Kas", layout="wide")
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Halaman", ["Dashboard", "Input Data", "Data & Pencarian", "Kelola Data"])

# --- Halaman-halaman Streamlit ---

# ====================== DASHBOARD ==========================
if menu == "Dashboard":
    st.title("📊 Dashboard Pengeluaran")
    df = load_data()

    if not df.empty:
        total_harga = df['total_harga'].sum()
        avg_harga = df['total_harga'].mean()
        count = len(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pengeluaran", format_rupiah(total_harga))
        col2.metric("Rata-rata Pengeluaran", format_rupiah(avg_harga))
        col3.metric("Jumlah Transaksi", count)

        df['Bulan'] = df['tanggal'].dt.to_period('M').astype(str)
        monthly_summary = df.groupby('Bulan')['total_harga'].sum()
        st.line_chart(monthly_summary)
    else:
        st.warning("Belum ada data untuk ditampilkan.")

# ===================== INPUT DATA ==========================
elif menu == "Input Data":
    st.title("📝 Input Pengeluaran Baru")
    df = load_data() # Muat ulang data untuk ID
    kode_pelanggan = st.text_input("Kode Pelanggan", max_chars=10)
    tanggal = st.date_input("Tanggal", value=datetime.today())
    deskripsi_pekerjaan = st.text_area("Deskripsi Pekerjaan")
    deskripsi_pengeluaran = st.text_area("Deskripsi Pengeluaran")
    jumlah_barang = st.number_input("Jumlah Barang", min_value=1)
    unit = st.selectbox("Unit", ["pcs", "ea", "meter", "galon", "liter", "lot", "set", "assy", "kaleng", "pail", "unit", "lembar"])
    harga_per_satuan = st.number_input("Harga per Satuan", min_value=0)
    keterangan = st.text_input("Keterangan")
    total_harga = jumlah_barang * harga_per_satuan

    if st.button("Simpan Data"):
        if not kode_pelanggan:
            st.error("Kode Pelanggan harus diisi.")
        else:
            id_transaksi = generate_id_transaksi(kode_pelanggan, tanggal, df)
            row = (id_transaksi, tanggal.strftime("%Y-%m-%d"), deskripsi_pekerjaan, deskripsi_pengeluaran,
                   jumlah_barang, unit, harga_per_satuan, total_harga, keterangan)
            save_data(row)
            st.success(f"Data ID {id_transaksi} berhasil disimpan!")
            st.experimental_rerun() # Refresh data setelah disimpan

# =================== DATA & PENCARIAN ======================
elif menu == "Data & Pencarian":
    st.title("🔍 Data & Pencarian")
    df = load_data()

    # --- Kolom Pencarian Baru ---
    search_col1, search_col2, search_col3 = st.columns(3)
    with search_col1:
        search_pekerjaan = st.text_input("Cari Deskripsi Pekerjaan", key="search_pekerjaan")
    with search_col2:
        search_id = st.text_input("Cari ID Transaksi", key="search_id")
    with search_col3:
        search_tanggal = st.date_input("Cari Tanggal (Opsional)", value=None, key="search_tanggal")
    
    df_filtered = df.copy()

    # Logika Filter
    if search_pekerjaan:
        df_filtered = df_filtered[df_filtered['deskripsi_pekerjaan'].astype(str).str.contains(search_pekerjaan, case=False, na=False)]
    
    if search_id:
        df_filtered = df_filtered[df_filtered['id'].astype(str).str.contains(search_id, case=False, na=False)]
    
    if search_tanggal:
        # Konversi tanggal DataFrame ke format string YYYY-MM-DD untuk perbandingan
        df_filtered_by_date = df_filtered[df_filtered['tanggal'].dt.strftime('%Y-%m-%d') == search_tanggal.strftime('%Y-%m-%d')]
        if not df_filtered_by_date.empty:
            df_filtered = df_filtered_by_date
        else:
            st.warning("Tidak ada data ditemukan untuk tanggal tersebut.")
            df_filtered = df.iloc[0:0] # Tampilkan DataFrame kosong jika tidak ada yang cocok

    # Menampilkan hasil pencarian
    if search_pekerjaan or search_id or search_tanggal:
        st.write(f"Menampilkan hasil pencarian:")
        if search_pekerjaan: st.write(f"- Deskripsi Pekerjaan: **{search_pekerjaan}**")
        if search_id: st.write(f"- ID Transaksi: **{search_id}**")
        if search_tanggal: st.write(f"- Tanggal: **{search_tanggal.strftime('%Y-%m-%d')}**")
    else:
        st.write("Menampilkan semua data.")


    # Tampilkan dataframe interaktif (ini adalah tabel yang Anda lihat di Streamlit)
    df_tampil = df_filtered.copy() # Pastikan df_tampil adalah hasil filter
    df_tampil["harga_per_satuan"] = df_tampil["harga_per_satuan"].apply(format_rupiah)
    df_tampil["total_harga"] = df_tampil["total_harga"].apply(format_rupiah)
    df_tampil["tanggal"] = df_tampil["tanggal"].dt.strftime("%Y-%m-%d") # Format untuk tampilan
    st.dataframe(df_tampil)

    # --- Tombol Download dan Cetak ---
    col_download1, col_print_button = st.columns([1, 1])

    # Tombol unduh CSV
    with col_download1:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Unduh CSV", csv, "hasil_pengeluaran.csv", "text/csv", key='download_csv')

    # Tombol Cetak (HTML) - Sekarang menggunakan fungsi print_data
    with col_print_button:
        if not df_filtered.empty: # Pastikan DataFrame tidak kosong sebelum dicetak
            if st.button("🖨️ Cetak Data", key='print_html_data'):
                print_data(df_filtered) # Panggil fungsi print_data dengan df_filtered
        else:
            st.info("Tidak ada data untuk dicetak.")

# ====================== KELOLA DATA ========================
elif menu == "Kelola Data":
    st.title("✏️ Kelola Data")
    df = load_data()

    if not df.empty:
        df_tampil = df.copy()
        df_tampil["harga_per_satuan"] = df_tampil["harga_per_satuan"].apply(format_rupiah)
        df_tampil["total_harga"] = df_tampil["total_harga"].apply(format_rupiah)
        df_tampil["tanggal"] = df_tampil["tanggal"].dt.strftime("%Y-%m-%d")

        st.dataframe(df_tampil)

        selected_index = st.number_input("Pilih Index untuk Edit/Hapus", min_value=0, max_value=len(df)-1, step=1)
        selected_row = df.iloc[selected_index]

        with st.expander("Edit Data Ini"):
            tanggal_value = selected_row['tanggal']
            if pd.isna(tanggal_value):
                tanggal_value = datetime.today()
            tanggal = st.date_input("Tanggal", value=pd.to_datetime(tanggal_value))

            deskripsi_pekerjaan = st.text_input("Deskripsi Pekerjaan", value=selected_row['deskripsi_pekerjaan'])
            deskripsi_pengeluaran = st.text_input("Deskripsi Pengeluaran", value=selected_row['deskripsi_pengeluaran'])
            jumlah_barang = st.number_input("Jumlah Barang", min_value=1, value=int(selected_row['jumlah_barang']))
            
            unit_options = ["pcs", "ea", "meter", "galon", "liter", "lot", "set", "assy", "kaleng", "pail", "unit", "lembar"]
            try:
                selected_unit_index = unit_options.index(selected_row['unit'])
            except ValueError:
                selected_unit_index = 0 

            unit = st.selectbox("Unit", unit_options, index=selected_unit_index)
            harga_per_satuan = st.number_input("Harga per Satuan", min_value=0, value=int(selected_row['harga_per_satuan']))
            keterangan = st.text_input("Keterangan", value=selected_row['keterangan'])
            total_harga = jumlah_barang * harga_per_satuan

            if st.button("Simpan Perubahan"):
                data = (
                    tanggal.strftime("%Y-%m-%d"), deskripsi_pekerjaan, deskripsi_pengeluaran,
                    jumlah_barang, unit, harga_per_satuan, total_harga, keterangan, selected_row['id']
                )
                update_data_by_id(data)
                st.success("Perubahan berhasil disimpan. Silakan refresh halaman.")
                st.experimental_rerun()

        if st.button("Hapus Data Ini"):
            delete_data_by_index(selected_index)
            st.success("Data berhasil dihapus. Silakan refresh halaman.")
            st.experimental_rerun()
    else:
        st.warning("Belum ada data.")