import os
import json

import torch
import torch.nn as nn

from PIL import Image
from torchvision import transforms, models


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "solar_guard_resnet18_best.pth"
)

CLASS_NAMES_PATH = os.path.join(
    BASE_DIR,
    "models",
    "class_names.json"
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# LOAD CLASS NAMES
# ============================================================

with open(
    CLASS_NAMES_PATH,
    "r",
    encoding="utf-8"
) as file:

    CLASS_NAMES = json.load(file)


# ============================================================
# LOAD RESNET18 MODEL
# ============================================================

model = models.resnet18(
    weights=None
)


# The classifier must exactly match the architecture
# used during training.

model.fc = nn.Sequential(
    nn.Dropout(0.5),
    nn.Linear(
        model.fc.in_features,
        len(CLASS_NAMES)
    )
)


# ============================================================
# LOAD TRAINED WEIGHTS
# ============================================================

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )
)


model = model.to(DEVICE)

model.eval()


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

transform = transforms.Compose([

    transforms.Resize(
        (224, 224)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],

        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_image(image_path):

    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    image = Image.open(
        image_path
    ).convert("RGB")


    # --------------------------------------------------------
    # Preprocess image
    # --------------------------------------------------------

    image_tensor = transform(
        image
    )


    # Add batch dimension
    image_tensor = image_tensor.unsqueeze(
        0
    )


    image_tensor = image_tensor.to(
        DEVICE
    )


    # --------------------------------------------------------
    # Run model
    # --------------------------------------------------------

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )


        confidence, predicted_index = torch.max(
            probabilities,
            dim=1
        )


    # --------------------------------------------------------
    # Get prediction
    # --------------------------------------------------------

    predicted_class = CLASS_NAMES[
        predicted_index.item()
    ]


    confidence_percentage = (
        confidence.item() * 100
    )


    # --------------------------------------------------------
    # Return format expected by routes/ai.py
    # --------------------------------------------------------

    return {
        "prediction": predicted_class,
        "confidence": round(
            confidence_percentage,
            2
        )
    }