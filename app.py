"""
app.py - Video Automation Tool (GUI)
Chalane ka tareeqa: streamlit run app.py
"""
import streamlit as st
import os, subprocess

st.set_page_config(page_title="Video Automation Tool", page_icon="🎬", layout="wide")
st.title("🎬 Video Automation Tool")
st.caption("Topic do -> HD video banao -> YouTube / Facebook / Instagram pe upload karo")

tab1, tab2, tab3 = st.tabs(["🎥 Video Banao", "🔗 Accounts Connect", "🚀 Upload"])

with tab1:
    st.subheader("Naya Video Banayein")
    topic = st.text_input("Topic likho:", placeholder="e.g. 5 morning habits of successful people")
    size = st.selectbox("Video style:", ["landscape (YouTube)", "vertical (Reels/Shorts)"])
    if st.button("🎬 Video Banana Shuru Karo", type="primary"):
        if not topic:
            st.warning("Pehle topic likho!")
        else:
            with open("config.py") as f: cfg = f.read()
            new_size = "vertical" if size.startswith("vertical") else "landscape"
            cfg = cfg.replace('SIZE = "landscape"', f'SIZE = "{new_size}"').replace(
                            'SIZE = "vertical"', f'SIZE = "{new_size}"')
            with open("config.py", "w") as f: f.write(cfg)
            with st.spinner("Video ban raha hai... 1-2 minute lag sakte hain ⏳"):
                result = subprocess.run(
                    ["python", "video_automator.py", "--topic", topic],
                    capture_output=True, text=True)
            st.code(result.stdout[-1500:] or result.stderr[-1500:])
            outdir = "output"
            if os.path.isdir(outdir):
                vids = sorted([v for v in os.listdir(outdir) if v.endswith(".mp4")],
                              key=lambda v: os.path.getmtime(f"{outdir}/{v}"), reverse=True)
                if vids:
                    st.success("Video ready! ✅")
                    st.video(f"{outdir}/{vids[0]}")
                else:
                    st.error("Video nahi bana. Upar error check karo.")

with tab2:
    st.subheader("Apne Accounts Connect Karo")
    st.info("Ye one-time setup hai. Baad me sab automatic chalega!")
    with st.expander("▶️ YouTube connect kaise karein"):
        st.markdown("""
1. console.cloud.google.com pe jao
2. Naya project -> YouTube Data API v3 enable karo
3. OAuth consent screen set karo (External)
4. Credentials -> Create OAuth Client ID -> Desktop app -> download karo
5. File ka naam client_secret.json rakh ke app folder me rakho
6. Upload dabao -> pehli baar browser khulega -> Google login
""")
    with st.expander("📘 Facebook Page connect kaise karein"):
        st.markdown("""
1. developers.facebook.com pe app banao
2. Graph API -> apna Page select karo
3. Page Access Token generate karo (pages_manage_posts)
4. Token neeche wale form me paste karo
""")
    with st.expander("📸 Instagram connect kaise karein"):
        st.markdown("""
1. Instagram ko Business account banao
2. Facebook Page se link karo
3. Meta app me instagram_basic + instagram_content_publish scopes lo
4. Token aur IG User ID paste karo
""")

with tab3:
    st.subheader("Ek Click Me Sab Jagah Upload 🚀")
    video = st.file_uploader("Video file chuno:", type=["mp4"])
    title = st.text_input("Title:", "Mera Awesome Video")
    desc = st.text_area("Description:", "Created with Video Automation Tool")
    c1, c2, c3 = st.columns(3)
    yt = c1.checkbox("YouTube ▶️", value=True)
    fb = c2.checkbox("Facebook 📘")
    ig = c3.checkbox("Instagram 📸")
    fb_page = st.text_input("FB Page ID (sirf Facebook ke liye):")
    fb_token = st.text_input("FB Page Access Token:", type="password")
    ig_id = st.text_input("Instagram User ID:")
    ig_token = st.text_input("Instagram Access Token:", type="password")
    if st.button("🚀 UPLOAD SAB JAGAH", type="primary"):
        if video is None:
            st.warning("Pehle video chuno!")
        else:
            tmp = "upload_temp.mp4"
            with open(tmp, "wb") as f: f.write(video.read())
            if yt:
                try:
                    with st.spinner("YouTube pe upload ho raha hai..."):
                        from uploaders import youtube_upload
                        link = youtube_upload(tmp, title, desc)
                    st.success(f"YouTube ✅ {link}")
                except Exception as e:
                    st.error(f"YouTube error: {e}")
            if fb and fb_token and fb_page:
                try:
                    from uploaders import facebook_upload
                    r = facebook_upload(tmp, title, fb_page, fb_token)
                    st.success(f"Facebook ✅ {r}")
                except Exception as e:
                    st.error(f"Facebook error: {e}")
            if ig and ig_token and ig_id:
                try:
                    from uploaders import instagram_upload
                    r = instagram_upload(tmp, title, ig_id, ig_token)
                    st.success(f"Instagram ✅ {r}")
                except Exception as e:
                    st.error(f"Instagram error: {e}")
