import os
import shutil
from datetime import datetime

def auto_backup():
    os.makedirs("backups", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = f"backups/backup_{timestamp}.db"

    if os.path.exists("fleet.db"):
        shutil.copy("fleet.db", backup_path)
