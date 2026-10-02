import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseClient:
    """
    Cliente Supabase robusto y multiplataforma basado en la API REST (PostgREST + Storage).
    Funciona sin dependencias binarias de Rust, garantizando compatibilidad total
    tanto en Windows (sin bloqueos de DLL) como en Linux (Render.com).
    """
    def __init__(self, url=None, key=None):
        self.url = (url or SUPABASE_URL or "").rstrip("/")
        self.key = key or SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def table(self, table_name: str):
        return TableQuery(self, table_name)

    def upload_file(self, bucket: str, path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        """Sube un archivo al bucket de Supabase Storage y retorna su URL pública."""
        endpoint = f"{self.url}/storage/v1/object/{bucket}/{path}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": content_type,
            "x-upsert": "true"
        }
        res = requests.post(endpoint, headers=headers, data=file_bytes, timeout=30)
        res.raise_for_status()
        return self.get_public_url(bucket, path)

    def get_public_url(self, bucket: str, path: str) -> str:
        """Retorna la URL pública de un archivo en Supabase Storage."""
        return f"{self.url}/storage/v1/object/public/{bucket}/{path}"


class TableQuery:
    def __init__(self, client: SupabaseClient, table_name: str):
        self.client = client
        self.endpoint = f"{client.url}/rest/v1/{table_name}"
        self.params = {}

    def select(self, columns: str = "*"):
        self.params["select"] = columns
        return self

    def eq(self, column: str, value: str):
        self.params[column] = f"eq.{value}"
        return self

    def order(self, column: str, ascending: bool = False):
        direction = "asc" if ascending else "desc"
        self.params["order"] = f"{column}.{direction}"
        return self

    def limit(self, count: int):
        self.params["limit"] = count
        return self

    def execute(self):
        resp = requests.get(self.endpoint, headers=self.client.headers, params=self.params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def insert(self, data):
        resp = requests.post(self.endpoint, headers=self.client.headers, json=data, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def update(self, data):
        resp = requests.patch(self.endpoint, headers=self.client.headers, params=self.params, json=data, timeout=15)
        resp.raise_for_status()
        return resp.json()


# Instancia por defecto
db = SupabaseClient()
