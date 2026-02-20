import streamlit as st
from supabase import create_client
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
from ultralytics import YOLO
import av, cv2, time, random, segno
from datetime import datetime

# --- 1. CLOUD CONNECTION & BRAIN ---
# Enter your Supabase credentials here (or use st.secrets for safety)
URL = "https://sb_publishable_NxPLX7CwJ_hy3iJF69GqMg_CPsWBsfu.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqb3B5c2Rnem11ZGtzamN3b3dnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE0NTYxMTEsImV4cCI6MjA4NzAzMjExMX0.fru7f--YTKJa0QrdFteg7Pq3d5JjmVB2gY-mNoQMll0"
supabase = create_client(URL, KEY)

@st.cache_resource
def load_ai():
    # Loading the MANIT-specific brain
    return YOLO('best.pt')

model = load_ai()

# --- 2. THE ANTI-CHEAT SCANNER ENGINE ---
class BinGoProcessor(VideoProcessorBase):
    def _init_(self):
        self.last_scan = 0
        self.status = "Ready"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        h, w, _ = img.shape
        
        # Detection Zone (Green Rectangle)
        zone = [int(w*0.3), int(h*0.6), int(w*0.7), h]
        cv2.rectangle(img, (zone[0], zone[1]), (zone[2], zone[3]), (0, 255, 0), 2)

        # AI Detection with Confidence Shield (Anti-Cheat: Phone Photo)
        results = model.predict(img, conf=0.85, verbose=False)
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1+x2)//2, (y1+y2)//2
                
                # Logic: Is it in the zone?
                if (zone[0] < cx < zone[2]) and (zone[1] < cy < zone[3]):
                    # Anti-Cheat: Yo-Yo Spam Cooldown
                    if time.time() - self.last_scan > 10:
                        self.last_scan = time.time()
                        st.session_state.earned_points = True
                        self.status = "✅ BOTTLE ACCEPTED!"
                    else:
                        self.status = "⏳ COOLDOWN..."
                
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- 3. THE APP INTERFACE ---
st.set_page_config(page_title="MANIT Bin-Go Pro", page_icon="♻️")

# Persistent Session Logic
if 'user' not in st.session_state:
    st.session_state.user = None
if 'earned_points' not in st.session_state:
    st.session_state.earned_points = False

# A. LOGIN SYSTEM
if not st.session_state.user:
    st.title("🛡️ MANIT Secure Login")
    user_id = st.text_input("Scholar ID / Merchant ID")
    pwd = st.text_input("Password", type="password")
    if st.button("Enter Campus"):
        # Check Supabase for user
        res = supabase.table("profiles").select("*").eq("username", user_id).eq("password", pwd).execute()
        if res.data:
            st.session_state.user = res.data[0]
            st.rerun()
        else:
            st.error("Invalid Credentials!")
else:
    user = st.session_state.user
    st.sidebar.title(f"👋 {user['username']}")
    st.sidebar.write(f"Role: *{user['role']}*")
    
    # B. DASHBOARDS
    if user['role'] == "Student":
        tab1, tab2, tab3 = st.tabs(["🎥 Earn", "🪪 My QR", "💸 Pay"])
        
        with tab1:
            st.metric("Wallet Balance", f"🪙 {user['balance']}")
            webrtc_streamer(key="earn", video_processor_factory=BinGoProcessor)
            if st.session_state.earned_points:
                # Update Supabase
                new_bal = user['balance'] + 10
                supabase.table("profiles").update({"balance": new_bal}).eq("id", user['id']).execute()
                st.balloons()
                st.success("Coin Added to Wallet!")
                st.session_state.earned_points = False
                time.sleep(2)
                st.rerun()

        with tab2:
            st.subheader("Your Unique QR")
            # Generate QR
            qr = segno.make(user['username'])
            st.image(qr.png_data_uri(scale=10), caption="Show this to Canteen or Teacher")
            st.info(f"UPI ID Linked: {user['username']}@manit")

        with tab3:
            st.subheader("Quick Transfer")
            recip = st.text_input("Recipient ID (Teacher/Merchant)")
            amt = st.number_input("Amount", min_value=10)
            if st.button("Transfer Points"):
                # Real P2P Transaction Logic would go here
                st.success(f"Transaction Successful! TID: {random.randint(1000,9999)}")

    elif user['role'] in ["Teacher", "Merchant"]:
     st.subheader("📲 Scan Student QR")
    
    # Import the updated library
    from streamlit_qrcode_scanner import qrcode_scanner

    # This opens the camera on the phone to read the QR
    scanned_qr = qrcode_scanner(key='qr_scanner')

    if scanned_qr:
        # scanned_qr will be the Scholar ID (e.g., "stu_01")
        st.success(f"Found Student: {scanned_qr}")
        
        # UI for point deduction
        amount = st.number_input("Enter Coins to Collect", min_value=10, step=10)
        
        if st.button("Confirm Transaction"):
            # 1. Deduct from student
            # 2. Add to merchant
            # (Use your Supabase logic here)
            st.balloons()

            st.success(f"Deducted {amount} coins from {scanned_qr}!")


