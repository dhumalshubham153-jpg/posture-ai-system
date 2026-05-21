from supabase import create_client, Client

SUPABASE_URL         = "https://xepdxusghwuzepyekbxk.supabase.co"
SUPABASE_KEY         = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlcGR4dXNnaHd1emVweWVrYnhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3MjQ2OTgsImV4cCI6MjA5MzMwMDY5OH0.zhtZLs9P2BWnbrIjighJTJoZPAxgyV_pLEz2aKAL_dU"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlcGR4dXNnaHd1emVweWVrYnhrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzcyNDY5OCwiZXhwIjoyMDkzMzAwNjk4fQ.mf91sNqdJHLnW6Vw3NkzyhnKNQXYqCwxfb_js44vLXU"

supabase       : Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin : Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_client()       -> Client: return supabase
def get_admin_client() -> Client: return supabase_admin