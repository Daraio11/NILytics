"""Run the experience bonus pass standalone."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from scoring.run_scoring import apply_experience_bonuses, get_supabase

sb = get_supabase()
apply_experience_bonuses(sb)
print("Done.")
