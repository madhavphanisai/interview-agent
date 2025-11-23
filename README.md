# 📌 **Interview Agent — AI Voice Interview Simulator**

An AI-powered full-duplex **voice interview system** that supports multiple domains like DSA, Front-End, ML, and Full-Stack.
It delivers adaptive questioning, voice interaction, scoring, and instant feedback — fully built using **React + FastAPI**.

---

## 🚀 **Features**

* 🎤 **Voice-enabled interview** (speech-to-text + text-to-speech)
* 🤖 **AI-generated follow-up questions**
* 📚 **JSON-based question bank**
* 🧠 **Automatic scoring**
* 📝 **Transcript logging**
* 🧪 **Feedback modal**
* ⚛️ **React Frontend**
* ⚡ **FastAPI Backend**

---

## 🏗️ **Architecture Overview**

### **Frontend (React)**

* React 18
* Web Speech API
* REST API communication
* Components:

  * `InterviewPanelVoice.js`
  * `VoiceControls.js`
  * `FeedbackModal.js`

### **Backend (FastAPI)**

* LLM via **AIMLAPI**
* Session manager
* JSON question banks
* Auto-scoring logic
* Feedback generator

### **Flow Diagram**

```
User → Voice Input → STT → FastAPI → AI/LLM → Follow-up  
Get Feedback → FastAPI → Aggregated Feedback → Modal  
```

---

## 🛠️ **Setup Instructions**

---

# **1️⃣ Clone Repository**

```
git clone https://github.com/<your-username>/interview-agent.git
cd interview-agent
```

---

# **2️⃣ Backend Setup (FastAPI)**

### Create virtual environment

```
cd backend
python -m venv .venv
.\.venv\Scripts\activate
```

### Install dependencies

```
pip install -r requirements.txt
```

### Create `.env` inside backend folder

```
AIMLAPI_KEY=your_api_key_here
AIML_MODEL=gpt-4o
AIMLAPI_BASE=https://api.aimlapi.com/v1
```

### Run backend

```
uvicorn app.main:app --reload --port 8000
```

Backend URL: `http://127.0.0.1:8000`

---

# **3️⃣ Frontend Setup (React)**

### Install dependencies

```
cd ../frontend
npm install
```

### Run development server

```
npm start
```

Frontend URL: `http://localhost:3000`

---

## 🧠 **Design Decisions**

### **1. Fully Voice-Based Interaction**

Uses the browser’s:

* `SpeechRecognition` (STT)
* `speechSynthesis` (TTS)

No external cost.

---

### **2. JSON Question Bank**

```
backend/questions/
  dsa.json
  machine_learning.json
  front_end.json
  full_stack_developer.json
```

Easy to manage and expand.

---

### **3. Multi-Stage LLM Pipeline**

Backend generates:

* Main question
* Follow-up question
* Auto-score
* Final feedback

Feels like a real technical interview.

---

### **4. Modular React Architecture**

* `InterviewPanelVoice.js` → Main logic
* `VoiceControls.js` → Microphone control
* `FeedbackModal.js` → Interactive pop-up

---

## 📁 **Folder Structure**

```
interview-agent/
│
├── backend/
│   ├── app/
│   ├── questions/
│   ├── llm_client.py
│   ├── store.py
│   ├── policy.py
│   ├── main.py
│   └── .env   (ignored)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   └── package.json
│
└── README.md
```

---

## 🧪 **Run Full System**

### Backend:

```
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend:

```
cd frontend
npm start
```

Open the app:

👉 **[http://localhost:3000](http://localhost:3000)**

---

## 🤝 **Contributions**

Contributions, improvements, and suggestions are welcome.

---

# 📬 **Contact**

If you want to reach me for project discussions, suggestions, or collaborations, feel free to contact me at:

📧 **[phanisaimadhav@gmail.com](mailto:phanisaimadhav@gmail.com)**
🔗 **[LinkedIn](https://www.linkedin.com/in/madhavphanisai)**


