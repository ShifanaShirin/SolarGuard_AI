# SolarGuard AI
## Solar Panel Maintenance and Performance Monitoring System Using AI

SolarGuard AI is a Flask and MySQL based web application for managing solar panels, maintenance requests, technicians, and AI-based solar panel condition detection.

---

# 1. Technologies Used

## Frontend
- HTML
- CSS
- Bootstrap
- JavaScript
- Jinja2

## Backend
- Python
- Flask

## Database
- MySQL

## Artificial Intelligence
- PyTorch
- TorchVision
- ResNet18
- Pillow
- NumPy
- Pandas
- Scikit-learn

---

# 2. Main Features

The system contains three main user roles:

### User
- Register and login
- Manage solar panels
- View solar panel details
- Create maintenance requests
- Upload maintenance images
- Track maintenance requests
- AI solar panel detection
- View AI analysis history
- View detailed AI analysis

### Technician
- Login
- View assigned maintenance jobs
- Accept jobs
- Start maintenance work
- Complete maintenance work
- Submit maintenance completion report

### Admin
- Admin dashboard
- View users
- View user details
- View maintenance requests
- Approve/reject requests
- Assign technicians
- View technicians
- View technician details

---

# 3. AI Detection

SolarGuard AI uses a trained ResNet18 image classification model.

The user can:

1. Select a registered solar panel.
2. Upload a solar panel image.
3. Run AI detection.
4. View the predicted condition.
5. View confidence percentage.
6. View estimated efficiency.
7. View maintenance recommendation.
8. Save the AI result.
9. View previous AI analyses.
10. Open detailed analysis.

---

# 4. AI Classes

The trained model recognizes five classes:

1. Bird-Drop
2. Clean
3. Dusty
4. Electrical-Damage
5. Physical-Damage

---

# 5. AI Model

The project uses:

ResNet18

The trained model is stored at:

ai/models/solar_guard_resnet18_best.pth

The class names are stored at:

ai/models/class_names.json

The prediction code is:

ai/prediction/predict.py

The application loads the trained model and performs prediction when the user uploads an image through the AI Detection page.

---

# 6. AI Dataset

The final dataset is stored at:

ai/dataset/solar_panel_dataset_clean/

It contains:

- train/
- validation/
- test/

The dataset contains five classes:

- Bird-Drop
- Clean
- Dusty
- Electrical-Damage
- Physical-Damage

---

# 7. AI Model Performance

Final test accuracy:

81.51%

The evaluation results are stored in:

ai/models/evaluation_results.json

Training information is stored in:

ai/models/training_history.json

---

# 8. Project Structure

```text
SolarGuardAI/
│
├── ai/
│   ├── dataset/
│   │   └── solar_panel_dataset_clean/
│   │       ├── train/
│   │       ├── validation/
│   │       └── test/
│   │
│   ├── models/
│   │   ├── class_names.json
│   │   ├── evaluation_results.json
│   │   ├── solar_guard_resnet18_best.pth
│   │   └── training_history.json
│   │
│   ├── prediction/
│   │   └── predict.py
│   │
│   └── test_samples/
│
├── database/
│   ├── database.sql
│   └── db.py
│
├── routes/
│   ├── admin.py
│   ├── ai.py
│   ├── auth.py
│   ├── maintenance.py
│   ├── panel.py
│   ├── technician.py
│   └── user.py
│
├── services/
│   ├── admin_service.py
│   ├── ai_detection_service.py
│   ├── auth_service.py
│   ├── dashboard_service.py
│   ├── maintenance_service.py
│   ├── panel_service.py
│   └── technician_service.py
│
├── static/
│   ├── css/
│   ├── images/
│   ├── js/
│   ├── reports/
│   └── uploads/
│
├── templates/
│   ├── admin/
│   ├── ai/
│   ├── auth/
│   ├── dashboard/
│   ├── layouts/
│   ├── maintenance/
│   ├── panels/
│   └── technician/
│
├── utils/
│   └── auth.py
│
├── app.py
├── config.py
├── requirements.txt
└── .env