import streamlit as st
import os

# Set environment variable for headless OpenCV (must be before cv2 import)
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'

try:
    import cv2
except ImportError as e:
    st.error(f"OpenCV import failed: {e}")
    st.error("Please install opencv-python-headless instead of opencv-python")
    st.stop()

try:
    from insightface.app import FaceAnalysis
except ImportError as e:
    st.error(f"InsightFace import failed: {e}")
    st.error("Please install insightface: pip install insightface")
    st.stop()

import numpy as np
from collections import defaultdict, deque
import time
from PIL import Image
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Real-time Age Detection",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    .status-stable {
        color: #28a745;
        font-weight: bold;
    }
    .status-learning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model' not in st.session_state:
    st.session_state.model = None
if 'face_history' not in st.session_state:
    st.session_state.face_history = defaultdict(lambda: {
        'ages': deque(maxlen=20),
        'genders': deque(maxlen=20),
        'last_seen': 0,
        'stable_age': None,
        'stable_gender': None,
        'confidence_threshold': 15
    })
if 'recorded_ages' not in st.session_state:
    st.session_state.recorded_ages = {}
if 'age_history' not in st.session_state:
    st.session_state.age_history = []
if 'frame_count' not in st.session_state:
    st.session_state.frame_count = 0
if 'camera_active' not in st.session_state:
    st.session_state.camera_active = False

# Constants
SMOOTHING_WINDOW = 20
FACE_DISTANCE_THRESHOLD = 100
AGE_CHANGE_THRESHOLD = 3
PROCESS_EVERY_N_FRAMES = 3

def is_deployed_environment():
    """Detect if running in a deployed environment"""
    deployment_indicators = [
        # Streamlit Cloud / Hugging Face Spaces
        os.environ.get('STREAMLIT_RUNTIME_ENV') == 'cloud',
        'streamlit' in os.environ.get('HOME', '').lower(),
        'app' in os.environ.get('HOME', '').lower(),
        'SPACE_ID' in os.environ,  # Hugging Face Spaces
        
        # Heroku
        'DYNO' in os.environ,
        
        # Railway, Render, etc.
        'RAILWAY_ENVIRONMENT' in os.environ,
        'RENDER' in os.environ,
        
        # General cloud environment indicators
        '/tmp' in os.environ.get('HOME', ''),
        '/app' in os.environ.get('HOME', ''),
        
        # Check if localhost is not accessible (common in containers)
        not os.path.exists('/dev/video0') if os.name != 'nt' else False,
    ]
    
    return any(deployment_indicators)

def load_model():
    """Load the InsightFace model"""
    with st.spinner("Loading face analysis model..."):
        try:
            # Try to initialize the model
            model = FaceAnalysis(name="buffalo_l")
            
            # Check if CUDA is available, otherwise use CPU
            try:
                model.prepare(ctx_id=0)  # Try GPU first
                st.session_state.model = model
                st.success("Model loaded successfully with GPU acceleration!")
                return True
            except Exception as gpu_error:
                st.warning(f"GPU not available ({gpu_error}), falling back to CPU...")
                try:
                    model.prepare(ctx_id=-1)  # Use CPU
                    st.session_state.model = model
                    st.success("Model loaded successfully with CPU!")
                    return True
                except Exception as cpu_error:
                    st.error(f"Failed to load model on CPU: {cpu_error}")
                    return False
                    
        except Exception as e:
            st.error(f"Failed to initialize model: {str(e)}")
            st.error("Make sure insightface is properly installed: pip install insightface")
            return False

def find_closest_face(new_face, existing_faces, frame_count):
    """Find the closest existing face to match with history"""
    if not existing_faces:
        return None
    
    new_center = ((new_face.bbox[0] + new_face.bbox[2]) / 2, 
                  (new_face.bbox[1] + new_face.bbox[3]) / 2)
    
    min_distance = float('inf')
    closest_face_id = None
    
    for face_id, face_data in existing_faces.items():
        if frame_count - face_data['last_seen'] > 30:
            continue
            
        distance = np.sqrt((new_center[0] - face_data.get('center_x', 0))**2 + 
                          (new_center[1] - face_data.get('center_y', 0))**2)
        
        if distance < min_distance and distance < FACE_DISTANCE_THRESHOLD:
            min_distance = distance
            closest_face_id = face_id
    
    return closest_face_id

def record_stable_age(face_id, stable_age):
    """Record a stable age for a face and update statistics"""
    if face_id not in st.session_state.recorded_ages or abs(st.session_state.recorded_ages[face_id] - stable_age) > 2:
        if face_id in st.session_state.recorded_ages:
            old_age = st.session_state.recorded_ages[face_id]
            if old_age in st.session_state.age_history:
                st.session_state.age_history.remove(old_age)
        
        st.session_state.recorded_ages[face_id] = stable_age
        st.session_state.age_history.append(stable_age)

def get_smoothed_predictions(face_data, face_id):
    """Calculate smoothed age and gender from history with stability locking"""
    if not face_data['ages']:
        return None, None
    
    ages = list(face_data['ages'])
    genders = list(face_data['genders'])
    sample_count = len(ages)
    
    current_median_age = int(np.median(ages))
    gender_counts = {}
    for gender in genders:
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
    current_gender = max(gender_counts.items(), key=lambda x: x[1])[0]
    
    if sample_count >= face_data['confidence_threshold']:
        if face_data['stable_age'] is None:
            face_data['stable_age'] = current_median_age
            face_data['stable_gender'] = current_gender
            record_stable_age(face_id, current_median_age)
            return face_data['stable_age'], face_data['stable_gender']
        else:
            age_diff = abs(current_median_age - face_data['stable_age'])
            
            if age_diff > AGE_CHANGE_THRESHOLD:
                recent_ages = ages[-10:] if len(ages) >= 10 else ages
                recent_median = int(np.median(recent_ages))
                
                if abs(recent_median - face_data['stable_age']) > AGE_CHANGE_THRESHOLD:
                    old_stable_age = face_data['stable_age']
                    if recent_median > face_data['stable_age']:
                        face_data['stable_age'] = min(face_data['stable_age'] + 1, recent_median)
                    else:
                        face_data['stable_age'] = max(face_data['stable_age'] - 1, recent_median)
                    
                    if abs(face_data['stable_age'] - old_stable_age) >= 1:
                        record_stable_age(face_id, face_data['stable_age'])
            
            if current_gender != face_data['stable_gender']:
                recent_genders = genders[-10:] if len(genders) >= 10 else genders
                recent_gender_counts = {}
                for gender in recent_genders:
                    recent_gender_counts[gender] = recent_gender_counts.get(gender, 0) + 1
                recent_dominant_gender = max(recent_gender_counts.items(), key=lambda x: x[1])[0]
                
                if recent_dominant_gender != face_data['stable_gender'] and recent_gender_counts[recent_dominant_gender] >= 7:
                    face_data['stable_gender'] = recent_dominant_gender
            
            return face_data['stable_age'], face_data['stable_gender']
    else:
        return current_median_age, current_gender

def process_frame(frame):
    """Process a single frame for face detection and analysis"""
    if st.session_state.model is None:
        return frame, []
    
    st.session_state.frame_count += 1
    
    # Only run face analysis every N frames
    if st.session_state.frame_count % PROCESS_EVERY_N_FRAMES == 0:
        faces = st.session_state.model.get(frame)
        
        # Clean up old face histories
        faces_to_remove = []
        for face_id, face_data in st.session_state.face_history.items():
            if st.session_state.frame_count - face_data['last_seen'] > 30:
                faces_to_remove.append(face_id)
        for face_id in faces_to_remove:
            del st.session_state.face_history[face_id]

        processed_faces = []
        for face in faces:
            box = face.bbox.astype(int)
            age = int(face.age) - 4  # Subtract 4 from detected age
            gender = 'Male' if face.gender == 1 else 'Female'
            
            center_x = (box[0] + box[2]) / 2
            center_y = (box[1] + box[3]) / 2
            
            closest_face_id = find_closest_face(face, st.session_state.face_history, st.session_state.frame_count)
            
            if closest_face_id is None:
                face_id = f"face_{st.session_state.frame_count}_{len(st.session_state.face_history)}"
                st.session_state.face_history[face_id] = {
                    'ages': deque(maxlen=SMOOTHING_WINDOW),
                    'genders': deque(maxlen=SMOOTHING_WINDOW),
                    'last_seen': st.session_state.frame_count,
                    'center_x': center_x,
                    'center_y': center_y,
                    'stable_age': None,
                    'stable_gender': None,
                    'confidence_threshold': 15
                }
            else:
                face_id = closest_face_id
            
            st.session_state.face_history[face_id]['ages'].append(age)
            st.session_state.face_history[face_id]['genders'].append(gender)
            st.session_state.face_history[face_id]['last_seen'] = st.session_state.frame_count
            st.session_state.face_history[face_id]['center_x'] = center_x
            st.session_state.face_history[face_id]['center_y'] = center_y
            
            smoothed_age, smoothed_gender = get_smoothed_predictions(st.session_state.face_history[face_id], face_id)
            
            if smoothed_age is not None:
                processed_faces.append({
                    'box': box,
                    'age': smoothed_age,
                    'gender': smoothed_gender,
                    'sample_count': len(st.session_state.face_history[face_id]['ages']),
                    'is_stable': st.session_state.face_history[face_id]['stable_age'] is not None,
                    'face_id': face_id
                })
        
        return frame, processed_faces
    
    return frame, []

def draw_annotations(frame, faces_data):
    """Draw face annotations on the frame"""
    annotated_frame = frame.copy()
    
    for face_data in faces_data:
        box = face_data['box']
        age = face_data['age']
        gender = face_data['gender']
        sample_count = face_data['sample_count']
        is_stable = face_data['is_stable']
        
        # Draw rectangle around face
        cv2.rectangle(annotated_frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        
        # Add age text
        cv2.putText(annotated_frame, f"Age: {age}", (box[0], box[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Add gender text
        cv2.putText(annotated_frame, gender, (box[0], box[3] + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Add status indicator
        status = f"{'STABLE' if is_stable else 'LEARNING'} ({sample_count}/15)"
        color = (0, 255, 0) if is_stable else (255, 165, 0)
        cv2.putText(annotated_frame, status, (box[0], box[3] + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    return annotated_frame

# Main app
def main():
    st.title("👥 Real-time Age Detection App")
    
    # Check deployment status and show appropriate message
    is_deployed = is_deployed_environment()
    if is_deployed:
        st.markdown("📷 **Upload an image to analyze faces and estimate ages**")
        st.info("🌐 You're using the deployed version. For webcam functionality, run this app locally.")
    else:
        st.markdown("Upload an image or use your webcam for real-time face analysis")
    
    # Sidebar
    st.sidebar.title("Controls")
    
    # Model loading
    if st.session_state.model is None:
        if st.sidebar.button("Load Model"):
            load_model()
    else:
        st.sidebar.success("✅ Model loaded")
    
    # Mode selection
    is_deployed = is_deployed_environment()
    
    if is_deployed:
        mode = st.sidebar.selectbox("Select Mode", ["Image Upload"])
        st.sidebar.info("ℹ️ Webcam mode is only available when running locally")
    else:
        mode = st.sidebar.selectbox("Select Mode", ["Image Upload", "Webcam (Real-time)"])
    
    # Reset button
    if st.sidebar.button("Reset Statistics"):
        st.session_state.face_history.clear()
        st.session_state.recorded_ages.clear()
        st.session_state.age_history.clear()
        st.session_state.frame_count = 0
        st.success("Statistics reset!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if mode == "Image Upload":
            st.subheader("📷 Image Analysis")
            uploaded_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png'])
            
            if uploaded_file is not None and st.session_state.model is not None:
                # Convert uploaded file to opencv format
                image = Image.open(uploaded_file)
                frame = np.array(image)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Process the frame
                processed_frame, faces_data = process_frame(frame)
                
                # Draw annotations
                if faces_data:
                    annotated_frame = draw_annotations(processed_frame, faces_data)
                    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                else:
                    annotated_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                st.image(annotated_frame_rgb, caption="Processed Image", use_column_width=True)
                
                # Display face details
                if faces_data:
                    st.subheader("Detected Faces")
                    for i, face_data in enumerate(faces_data):
                        with st.expander(f"Face {i+1} - {face_data['gender']}, Age: {face_data['age']}"):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Age", f"{face_data['age']} years")
                            with col_b:
                                st.metric("Gender", face_data['gender'])
                            with col_c:
                                status = "STABLE" if face_data['is_stable'] else "LEARNING"
                                st.metric("Status", f"{status} ({face_data['sample_count']}/15)")
        
        elif mode == "Webcam (Real-time)":
            st.subheader("📹 Real-time Webcam Analysis")
            
            if st.session_state.model is None:
                st.warning("Please load the model first using the sidebar.")
            else:
                # Webcam controls
                start_button = st.button("Start Webcam")
                stop_button = st.button("Stop Webcam")
                
                if start_button:
                    st.session_state.camera_active = True
                
                if stop_button:
                    st.session_state.camera_active = False
                
                # Webcam feed placeholder
                frame_placeholder = st.empty()
                
                if st.session_state.camera_active:
                    try:
                        cap = cv2.VideoCapture(0)
                        
                        if cap.isOpened():
                            while st.session_state.camera_active:
                                ret, frame = cap.read()
                                if ret:
                                    # Process frame
                                    processed_frame, faces_data = process_frame(frame)
                                    
                                    # Draw annotations
                                    if faces_data:
                                        annotated_frame = draw_annotations(processed_frame, faces_data)
                                    else:
                                        annotated_frame = processed_frame
                                    
                                    # Convert to RGB for display
                                    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                                    frame_placeholder.image(annotated_frame_rgb, caption="Live Feed", use_column_width=True)
                                    
                                    time.sleep(0.1)  # Control frame rate
                                else:
                                    st.error("Failed to capture frame from webcam")
                                    break
                            
                            cap.release()
                        else:
                            st.error("❌ Could not access webcam")
                            st.markdown("""
                            **Possible solutions:**
                            - Check if your camera is connected
                            - Close other applications using the camera
                            - Try refreshing the page
                            - Check browser permissions for camera access
                            """)
                    except Exception as e:
                        st.error(f"Webcam error: {e}")
                        st.session_state.camera_active = False
    
    with col2:
        st.subheader("📊 Statistics")
        
        # Current statistics
        if st.session_state.age_history:
            current_average = sum(st.session_state.age_history) / len(st.session_state.age_history)
            
            # Metrics
            st.metric("People Detected", len(st.session_state.recorded_ages))
            st.metric("Average Age", f"{current_average:.1f} years")
            st.metric("Age Range", f"{min(st.session_state.age_history)}-{max(st.session_state.age_history)} years")
            
            # Age distribution chart
            if len(st.session_state.age_history) > 1:
                st.subheader("Age Distribution")
                age_df = pd.DataFrame({'Ages': st.session_state.age_history})
                st.bar_chart(age_df['Ages'].value_counts().sort_index())
            
            # Detailed breakdown
            st.subheader("Detected Faces")
            for face_id, age in st.session_state.recorded_ages.items():
                display_id = face_id.replace('face_', 'Person ')
                st.write(f"**{display_id}**: {age} years")
        
        else:
            is_deployed = is_deployed_environment()
            if is_deployed:
                st.info("📷 Upload an image to start detecting faces and analyzing ages!")
            else:
                st.info("No faces detected yet. Upload an image or start the webcam to begin analysis.")
        
        # Instructions
        st.subheader("ℹ️ Instructions")
        is_deployed = is_deployed_environment()
        
        if is_deployed:
            st.markdown("""
            **📷 Image Upload Mode:**
            1. Click "Load Model" in the sidebar (first time only)
            2. Upload an image (JPG, JPEG, or PNG)
            3. View detected faces and age estimates
            4. Check statistics in the sidebar
            
            **🔧 Features:**
            - Age prediction with enhanced accuracy
            - Gender detection
            - Face tracking and stability detection
            - Real-time statistics and age distribution
            
            **💡 Want webcam functionality?**
            Run this app locally:
            ```bash
            git clone <repository>
            pip install -r requirements.txt
            streamlit run app.py
            ```
            """)
        else:
            st.markdown("""
            **📷 Image Mode:**
            1. Load the model using the sidebar
            2. Upload an image
            3. View detected faces and statistics
            
            **📹 Webcam Mode:**
            1. Load the model using the sidebar  
            2. Click "Start Webcam"
            3. Allow camera permissions if prompted
            4. Click "Stop Webcam" when done
            
            **🔧 Features:**
            - Age prediction with -4 adjustment
            - Gender detection
            - Face tracking and stability detection
            - Real-time statistics
            - Age distribution visualization
            """)

if __name__ == "__main__":
    main()
