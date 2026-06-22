# 🔴 Red Line Guardian: AI Ecosystem 🤖

[![Python Version](https://img.shields.io/badge/python-3.x-blue)](#)
[![Computer Vision](https://img.shields.io/badge/concept-Computer%20Vision-orange)](#)
[![Control Theory](https://img.shields.io/badge/concept-PID%20Control-red)](#)

A complete ecosystem consisting of a high-reflex reaction game and an advanced **Computer Vision (CV) Agent** designed to simulate professional-level human gameplay.

---

## 📖 Project Overview

This repository demonstrates a closed-loop system:
1. **The Challenge (The Game):** A fast-paced visual reflex game where players must keep a moving red line within a white bar.
2. **The Agent (The Bot):** An intelligent automation tool that uses real-time screen analysis and mathematical control algorithms to master the game.

---

## 🕹️ Part 1: The Game (Red Line Guardian)

A minimalist, high-intensity game built with `Pygame`. It features dynamic color shifts, decoys, and unpredictable movement to challenge human reflexes.

*   **Objective:** Prevent the red line from leaving the white bar.
*   **Mechanics:** Movement is controlled by mouse click-and-hold.
*   **Complexity:** Random color modes and decoy boxes to distract the player.

---

## 🧠 Part 2: The AI Agent (The Bot)

The bot is not a simple macro; it is a **Vision-Based Control Agent**. It perceives the game environment exactly like a human, using raw pixel data.

### 🛠️ Technical Implementation
* **Computer Vision (Perception):** Using `OpenCV` and `mss` for high-speed screen capturing. The agent utilizes **Color Space Thresholding** (HSV/BGR) to detect the position of the white bar and the red line in real-time.
* **PID-Inspired Control (Decision Making):** Instead of erratic movements, the bot uses a **Proportional-Derivative (PD)** control logic. It calculates the `error` (distance between red line and bar center) and predicts movement to minimize jitter, simulating smooth, professional human precision.
* **Intelligence Presets:**
  * `Low`: Minimal reaction speed.
  * `Medium`: Balanced reaction (Default).
  * `Pro/Expert`: Extremely low latency and high-precision correction.
* **Heuristics & Safety:** Includes "Stuck Recovery" logic and randomized click delays to simulate organic human behavior and avoid detection.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.x
* Administrative Privileges (Required for Bot mouse control simulation)

### Installation & Execution

1. **Clone the repository:**
```bash
   git clone [https://github.com/rohmansyah23/red-line-guardian-ai.git](https://github.com/rohmansyah23/red-line-guardian-ai.git)
   cd red-line-guardian-ai

```

2. **Run the Game:**

```bash
   cd game
   pip install -r requirements.txt
   python main.py

```

3. **Run the Bot:**
*(Buka terminal baru di folder utama proyek)*

```bash
   cd bot
   pip install -r requirements.txt
   python main.py

```

---

## 📊 Technical Stack

| Component | Technology |
| --- | --- |
| **Game Engine** | Pygame |
| **Vision Engine** | OpenCV, MSS (Fast Screen Grab) |
| **Control Logic** | PID (Proportional-Derivative) |
| **Automation** | Pynput (Mouse/Keyboard Simulation) |
| **GUI** | Tkinter (ThemedTk) |

---

## ⚠️ Disclaimer

This project is developed for educational purposes only. It is intended to demonstrate the implementation of Computer Vision and Control Theory in a simulated environment.

---

## 👤 Author

* **Rohmansyah** - [@rohmansyah23](https://www.google.com/search?q=https://github.com/rohmansyah23)