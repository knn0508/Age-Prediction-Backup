---
title: Age Detection App
emoji: 👥
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: AI-powered face age detection and analysis using InsightFace
tags:
  - computer-vision
  - face-detection
  - age-estimation
  - streamlit
  - insightface
---

# Age Detection Streamlit App

A real-time age detection application built with Streamlit and InsightFace that can analyze faces from uploaded images.

## 🚀 Features

- **Image Upload Mode**: Upload an image to detect faces and estimate ages
- **Face Detection**: Advanced face detection using InsightFace models
- **Age Estimation**: AI-powered age prediction with enhanced accuracy
- **Gender Detection**: Identifies gender along with age
- **Statistics Dashboard**: Shows age distribution and detailed analytics
- **Real-time Processing**: Fast face analysis and visualization

## 🎯 How to Use

1. **Load the Model**: Click "Load Model" in the sidebar (first time only)
2. **Upload Image**: Choose an image file (JPG, JPEG, or PNG)
3. **View Results**: See detected faces with age and gender estimates
4. **Check Statistics**: View age distribution and analytics in the sidebar

## 🔧 Technical Details

- **Face Detection**: InsightFace Buffalo_L model for accurate face detection
- **Age Adjustment**: Automatically adjusts detected age for better accuracy (subtracts 4 years)
- **Stability System**: Uses face tracking and stability detection for consistent results
- **Performance**: Optimized for both CPU and GPU processing

## 📊 Statistics Features

- People count and average age calculation
- Age range display
- Age distribution visualization
- Individual face tracking results

## 🌐 Deployment

This app is optimized for deployment on:
- Hugging Face Spaces
- Streamlit Cloud
- Local development environments

For local development with webcam support:
```bash
git clone <repository>
pip install -r requirements.txt
streamlit run app.py
```

## 🛠️ Technologies Used

- **Streamlit**: Web app framework
- **InsightFace**: Face detection and analysis
- **OpenCV**: Image processing
- **NumPy & Pandas**: Data processing
- **PIL**: Image handling

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
