"""
uploaders.py - YouTube / Facebook / Instagram auto-upload
"""
import os, requests

# ================= YOUTUBE =================
def youtube_upload(video_path, title, description, tags=None, client_secret="client_secret.json"):
    """First run me browser khulega -> Google login -> token.json save.
    Phir har upload automatically hoga."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    if os.path.exists("token.json"):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": title, "description": description,
                        "tags": tags or [], "categoryId": "22"},
            "status": {"privacyStatus": "public"}}
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    return f"https://youtube.com/watch?v={resp['id']}"

# ================= FACEBOOK PAGE =================
def facebook_upload(video_path, title, page_id, page_access_token):
    """Page access token chahiye (Meta for Developers se).
    Scope: pages_manage_posts"""
    url = f"https://graph.facebook.com/v21.0/{page_id}/videos"
    with open(video_path, "rb") as f:
        r = requests.post(url,
                          files={"source": f},
                          data={"access_token": page_access_token,
                                "description": title}, timeout=300)
    return r.json()

# ================= INSTAGRAM (Reels) =================
def instagram_upload(video_path, caption, ig_user_id, access_token):
    """IG Business account + linked FB Page chahiye.
    Scope: instagram_basic, instagram_content_publish"""
    with open(video_path, "rb") as f:
        r1 = requests.post(
            f"https://graph.facebook.com/v21.0/{ig_user_id}/media",
            data={"caption": caption,
                  "access_token": access_token,
                  "media_type": "REELS"},
            files={"video_file": f}, timeout=300)
    container = r1.json().get("id")
    if not container:
        return r1.json()
    r2 = requests.post(
        f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish",
        data={"creation_id": container, "access_token": access_token}, timeout=120)
    return r2.json()
