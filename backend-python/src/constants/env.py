import os

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ENFORCE_JWT_AUTH = os.environ.get("ENFORCE_JWT_AUTH", "true").lower() == "true"
HTTP_WS_PORT = int(os.environ.get("HTTP_PORT", "8080"))

WS_TASK_TIMEOUT = int(os.environ.get("WS_TASK_TIMEOUT", "60"))

JWT_SECRET = os.environ.get("JWT_SECRET", "")

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://wcimkuektecvnbwsaocg.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndjaW1rdWVrdGVjdm5id3Nhb2NnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODA2MDg0NjQsImV4cCI6MTk5NjE4NDQ2NH0.7ViXbDbUumML_k9cU7QtnqYhs6jp0DN85NNVWg6U1F8")
