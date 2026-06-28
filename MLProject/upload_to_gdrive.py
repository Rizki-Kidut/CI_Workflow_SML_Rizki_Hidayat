import os
import shutil
import mlflow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ── 1. Bangun credentials dari Refresh Token
credentials = Credentials(
    token=None,
    refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GDRIVE_CLIENT_ID"],
    client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/drive"]
)

# Refresh token untuk dapat access token baru
credentials.refresh(Request())
print("✅ Autentikasi OAuth berhasil")

# ── 2. Build Google Drive API client
service = build('drive', 'v3', credentials=credentials)

# ── 3. Konfigurasi
FOLDER_ID  = os.environ["GDRIVE_FOLDER_ID"]
RUN_ID     = os.environ.get("RUN_ID")

if not RUN_ID:
    raise ValueError("❌ RUN_ID tidak ditemukan. Pastikan step GitHub Actions sebelumnya telah mengekspor RUN_ID.")

# ── 4. Cari lokasi Folder Artifact menggunakan MLflow & Zip Folder tersebut
print(f"🔍 Mencari lokasi artifact untuk RUN_ID: {RUN_ID}")
client = mlflow.tracking.MlflowClient()
run = client.get_run(RUN_ID)

# Hapus prefix 'file://' jika ada agar menjadi local path yang valid
local_artifact_path = run.info.artifact_uri.replace("file://", "")

if not os.path.exists(local_artifact_path):
    raise FileNotFoundError(f"❌ Folder artifact tidak ditemukan di: {local_artifact_path}")

print(f"📦 Mengompresi folder artifacts dari: {local_artifact_path}")
zip_base_name = "mlflow_artifacts_temp"
shutil.make_archive(zip_base_name, 'zip', local_artifact_path)

LOCAL_FILE = f"{zip_base_name}.zip"
FILE_NAME  = f"model_artifacts_{RUN_ID}.zip" # Nama file saat di Google Drive


# ── 5. Fungsi Upload
def cari_file_existing(folder_id, file_name):
    """Cari file dengan nama tertentu di folder Google Drive."""
    query = (
        f"name = '{file_name}' "
        f"and '{folder_id}' in parents "
        f"and trashed = false"
    )
    response = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = response.get("files", [])
    return files[0] if files else None


def upload_file(local_path, file_name, folder_id):
    """Upload ke Google Drive. Overwrite jika file sudah ada."""
    file_size = os.path.getsize(local_path) / (1024 * 1024)
    print(f"🚀 Bersiap mengunggah File  : {file_name}")
    print(f"📏 Size  : {file_size:.1f} MB")
    print(f"📂 Ke Folder GDrive: {folder_id}")

    media    = MediaFileUpload(local_path, resumable=True)
    existing = cari_file_existing(folder_id, file_name)

    if existing:
        # File sudah ada → UPDATE (overwrite)
        print(f"🔄 File sudah ada (ID: {existing['id']}) → Overwrite...")
        updated = service.files().update(
            fileId=existing["id"],
            media_body=media,
            fields="id, name"
        ).execute()
        print(f"✅ Berhasil diupdate: {updated['name']} (ID: {updated['id']})")
    else:
        # File belum ada → CREATE baru
        print("🆕 File belum ada → Upload baru...")
        file_meta = {
            "name"   : file_name,
            "parents": [folder_id]
        }
        created = service.files().create(
            body=file_meta,
            media_body=media,
            fields="id, name"
        ).execute()
        print(f"✅ Berhasil diupload: {created['name']} (ID: {created['id']})")

if __name__ == "__main__":
    print("=" * 50)
    print("☁️  Upload MLflow Artifacts ke Google Drive (OAuth)")
    print("=" * 50)
    upload_file(LOCAL_FILE, FILE_NAME, FOLDER_ID)
    print("=" * 50)
    print("🎉 Upload selesai!")
    print("=" * 50)
