import os
import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# SOLARGUARD AI
# MODEL EVALUATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "solar_panel_dataset"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "solar_guard_resnet18_best.pth"
)

CLASS_NAMES_PATH = os.path.join(
    MODEL_DIR,
    "class_names.json"
)

IMAGE_SIZE = 224
BATCH_SIZE = 16


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


print("=" * 70)
print("SOLARGUARD AI - MODEL EVALUATION")
print("=" * 70)

print(f"\nDevice: {device}")


# ============================================================
# LOAD CLASS NAMES
# ============================================================

with open(
    CLASS_NAMES_PATH,
    "r",
    encoding="utf-8"
) as file:

    class_names = json.load(file)


num_classes = len(class_names)

print("\nClasses:")

for index, class_name in enumerate(class_names):

    print(
        f"{index}: {class_name}"
    )


# ============================================================
# TEST TRANSFORM
# ============================================================

test_transforms = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
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
# LOAD TEST DATASET
# ============================================================

test_dir = os.path.join(
    DATASET_DIR,
    "test"
)

test_dataset = datasets.ImageFolder(
    test_dir,
    transform=test_transforms
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


print(
    f"\nTest images: "
    f"{len(test_dataset)}"
)


# ============================================================
# CREATE MODEL
# ============================================================

print("\nLoading ResNet18...")

model = models.resnet18(
    weights=None
)


model.fc = nn.Sequential(

    nn.Dropout(
        p=0.5
    ),

    nn.Linear(
        model.fc.in_features,
        num_classes
    )
)


# ============================================================
# LOAD TRAINED WEIGHTS
# ============================================================

print(
    "\nLoading trained model:"
)

print(MODEL_PATH)


state_dict = torch.load(
    MODEL_PATH,
    map_location=device
)

model.load_state_dict(
    state_dict
)

model = model.to(device)

model.eval()


# ============================================================
# PREDICTIONS
# ============================================================

all_labels = []
all_predictions = []

correct = 0
total = 0


print("\nRunning predictions...")


with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)

        _, predictions = torch.max(
            outputs,
            1
        )

        total += labels.size(0)

        correct += (
            predictions == labels
        ).sum().item()

        all_labels.extend(
            labels.cpu().numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    all_labels,
    all_predictions
)


print("\n")
print("=" * 70)
print("TEST RESULTS")
print("=" * 70)

print(
    f"\nCorrect predictions : "
    f"{correct}/{total}"
)

print(
    f"Incorrect predictions : "
    f"{total - correct}/{total}"
)

print(
    f"\nTEST ACCURACY: "
    f"{accuracy * 100:.2f}%"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n")
print("=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

report = classification_report(

    all_labels,

    all_predictions,

    target_names=class_names,

    digits=4,

    zero_division=0
)

print("\n" + report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    all_labels,
    all_predictions
)


print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print("\nRows = Actual")
print("Columns = Predicted\n")

print(
    f"{'':20}",
    end=""
)

for class_name in class_names:

    print(
        f"{class_name[:12]:>14}",
        end=""
    )

print()


for index, row in enumerate(cm):

    print(
        f"{class_names[index]:20}",
        end=""
    )

    for value in row:

        print(
            f"{value:>14}",
            end=""
        )

    print()


# ============================================================
# PER-CLASS CORRECT / INCORRECT
# ============================================================

print("\n")
print("=" * 70)
print("PER-CLASS PERFORMANCE")
print("=" * 70)

for index, class_name in enumerate(
    class_names
):

    actual_count = cm[index].sum()

    correct_count = cm[index][index]

    incorrect_count = (
        actual_count
        -
        correct_count
    )

    class_accuracy = (
        correct_count
        /
        actual_count
        *
        100
    )

    print(
        f"\n{class_name}"
    )

    print(
        f"  Actual images : "
        f"{actual_count}"
    )

    print(
        f"  Correct       : "
        f"{correct_count}"
    )

    print(
        f"  Incorrect     : "
        f"{incorrect_count}"
    )

    print(
        f"  Accuracy      : "
        f"{class_accuracy:.2f}%"
    )


# ============================================================
# SAVE EVALUATION RESULTS
# ============================================================

evaluation_results = {

    "test_images": total,

    "correct_predictions": correct,

    "incorrect_predictions":
        total - correct,

    "test_accuracy":
        round(
            accuracy * 100,
            2
        ),

    "classification_report":
        classification_report(
            all_labels,
            all_predictions,
            target_names=class_names,
            output_dict=True,
            zero_division=0
        ),

    "confusion_matrix":
        cm.tolist()
}


results_path = os.path.join(
    MODEL_DIR,
    "evaluation_results.json"
)


with open(
    results_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        evaluation_results,
        file,
        indent=4
    )


print("\n")
print("=" * 70)
print("EVALUATION COMPLETED")
print("=" * 70)

print(
    f"\nResults saved to:"
    f"\n{results_path}"
)