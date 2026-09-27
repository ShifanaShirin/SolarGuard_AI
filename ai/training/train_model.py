import os
import json
import copy
import torch
import torch.nn as nn
import torch.optim as optim

from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "solar_panel_dataset_clean"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "solar_guard_resnet18_best.pth"
)

CLASS_NAMES_PATH = os.path.join(
    MODEL_DIR,
    "class_names.json"
)

HISTORY_PATH = os.path.join(
    MODEL_DIR,
    "training_history.json"
)


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 16
NUM_EPOCHS = 25

LEARNING_RATE_BACKBONE = 1e-5
LEARNING_RATE_CLASSIFIER = 1e-4

WEIGHT_DECAY = 1e-4

PATIENCE = 6

IMAGE_SIZE = 224

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


print("=" * 70)
print("SOLARGUARD AI - FINAL RESNET18 TRAINING")
print("=" * 70)

print(f"Device: {DEVICE}")
print(f"Dataset: {DATASET_DIR}")

if DEVICE.type == "cpu":
    print("\nWARNING: Training is running on CPU.")
    print("This may take some time.\n")


# ============================================================
# TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.RandomHorizontalFlip(
        p=0.5
    ),

    transforms.RandomRotation(
        degrees=10
    ),

    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15,
        saturation=0.10
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


validation_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# DATASETS
# ============================================================

train_dir = os.path.join(
    DATASET_DIR,
    "train"
)

validation_dir = os.path.join(
    DATASET_DIR,
    "validation"
)

train_dataset = datasets.ImageFolder(
    train_dir,
    transform=train_transform
)

validation_dataset = datasets.ImageFolder(
    validation_dir,
    transform=validation_transform
)


class_names = train_dataset.classes

num_classes = len(class_names)


print("\nClasses:")

for index, class_name in enumerate(class_names):
    print(f"{index}: {class_name}")


print("\nTraining images:", len(train_dataset))
print("Validation images:", len(validation_dataset))


# ============================================================
# DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# CLASS WEIGHTS
# ============================================================

class_counts = [
    0
    for _ in range(num_classes)
]

for _, label in train_dataset.samples:
    class_counts[label] += 1


print("\nTraining class counts:")

for i, count in enumerate(class_counts):
    print(
        f"{class_names[i]}: {count}"
    )


total_samples = sum(class_counts)

class_weights = []

for count in class_counts:

    weight = total_samples / (
        num_classes * count
    )

    class_weights.append(weight)


class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32
).to(DEVICE)


print("\nClass weights:")

for i, weight in enumerate(class_weights):
    print(
        f"{class_names[i]}: "
        f"{weight.item():.4f}"
    )


# ============================================================
# MODEL
# ============================================================

print("\nLoading pretrained ResNet18...")

weights = models.ResNet18_Weights.DEFAULT

model = models.resnet18(
    weights=weights
)


# Freeze entire backbone first
for parameter in model.parameters():
    parameter.requires_grad = False


# Unfreeze the final ResNet block
for parameter in model.layer4.parameters():
    parameter.requires_grad = True


# Replace classifier
model.fc = nn.Sequential(
    nn.Dropout(0.5),
    nn.Linear(
        model.fc.in_features,
        num_classes
    )
)


model = model.to(DEVICE)


# ============================================================
# LOSS
# ============================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = optim.AdamW(
    [
        {
            "params": model.layer4.parameters(),
            "lr": LEARNING_RATE_BACKBONE
        },
        {
            "params": model.fc.parameters(),
            "lr": LEARNING_RATE_CLASSIFIER
        }
    ],
    weight_decay=WEIGHT_DECAY
)


# ============================================================
# LEARNING RATE SCHEDULER
# ============================================================

scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2
)


# ============================================================
# TRAINING VARIABLES
# ============================================================

best_validation_accuracy = 0.0

best_model_weights = copy.deepcopy(
    model.state_dict()
)

epochs_without_improvement = 0

history = {
    "train_loss": [],
    "train_accuracy": [],
    "validation_loss": [],
    "validation_accuracy": []
}


# ============================================================
# TRAINING LOOP
# ============================================================

print("\n")
print("=" * 70)
print("STARTING TRAINING")
print("=" * 70)


for epoch in range(NUM_EPOCHS):

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0


    for images, labels in train_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)


        optimizer.zero_grad()


        outputs = model(images)

        loss = criterion(
            outputs,
            labels
        )


        loss.backward()

        optimizer.step()


        running_loss += (
            loss.item()
            * images.size(0)
        )


        _, predictions = torch.max(
            outputs,
            1
        )


        total += labels.size(0)

        correct += (
            predictions == labels
        ).sum().item()


    train_loss = (
        running_loss / total
    )

    train_accuracy = (
        100.0 * correct / total
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    model.eval()

    validation_loss_total = 0.0

    validation_correct = 0

    validation_total = 0


    with torch.no_grad():

        for images, labels in validation_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)


            outputs = model(images)


            loss = criterion(
                outputs,
                labels
            )


            validation_loss_total += (
                loss.item()
                * images.size(0)
            )


            _, predictions = torch.max(
                outputs,
                1
            )


            validation_total += (
                labels.size(0)
            )


            validation_correct += (
                predictions == labels
            ).sum().item()


    validation_loss = (
        validation_loss_total
        / validation_total
    )


    validation_accuracy = (
        100.0
        * validation_correct
        / validation_total
    )


    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    history["train_loss"].append(
        train_loss
    )

    history["train_accuracy"].append(
        train_accuracy
    )

    history["validation_loss"].append(
        validation_loss
    )

    history["validation_accuracy"].append(
        validation_accuracy
    )


    # --------------------------------------------------------
    # SCHEDULER
    # --------------------------------------------------------

    scheduler.step(
        validation_accuracy
    )


    # --------------------------------------------------------
    # CURRENT LEARNING RATES
    # --------------------------------------------------------

    current_lr_backbone = (
        optimizer.param_groups[0]["lr"]
    )

    current_lr_classifier = (
        optimizer.param_groups[1]["lr"]
    )


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print(
        f"\nEpoch [{epoch + 1}/{NUM_EPOCHS}]"
    )

    print(
        f"Train Loss: {train_loss:.4f}"
    )

    print(
        f"Train Accuracy: "
        f"{train_accuracy:.2f}%"
    )

    print(
        f"Validation Loss: "
        f"{validation_loss:.4f}"
    )

    print(
        f"Validation Accuracy: "
        f"{validation_accuracy:.2f}%"
    )

    print(
        f"LR Layer4: "
        f"{current_lr_backbone:.2e}"
    )

    print(
        f"LR Classifier: "
        f"{current_lr_classifier:.2e}"
    )


    # --------------------------------------------------------
    # SAVE BEST MODEL
    # --------------------------------------------------------

    if validation_accuracy > best_validation_accuracy:

        best_validation_accuracy = (
            validation_accuracy
        )

        best_model_weights = (
            copy.deepcopy(
                model.state_dict()
            )
        )

        torch.save(
            best_model_weights,
            MODEL_PATH
        )


        print(
            f"*** NEW BEST MODEL *** "
            f"{best_validation_accuracy:.2f}%"
        )


        epochs_without_improvement = 0

    else:

        epochs_without_improvement += 1


    # --------------------------------------------------------
    # EARLY STOPPING
    # --------------------------------------------------------

    if epochs_without_improvement >= PATIENCE:

        print(
            "\nEarly stopping triggered."
        )

        break


# ============================================================
# RESTORE BEST MODEL
# ============================================================

model.load_state_dict(
    best_model_weights
)


# ============================================================
# SAVE CLASS NAMES
# ============================================================

with open(
    CLASS_NAMES_PATH,
    "w"
) as file:

    json.dump(
        class_names,
        file,
        indent=4
    )


# ============================================================
# SAVE TRAINING HISTORY
# ============================================================

with open(
    HISTORY_PATH,
    "w"
) as file:

    json.dump(
        history,
        file,
        indent=4
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n")
print("=" * 70)
print("TRAINING COMPLETED")
print("=" * 70)

print(
    f"Best Validation Accuracy: "
    f"{best_validation_accuracy:.2f}%"
)

print(
    f"\nModel saved to:"
    f"\n{MODEL_PATH}"
)

print(
    f"\nClass names saved to:"
    f"\n{CLASS_NAMES_PATH}"
)

print(
    f"\nTraining history saved to:"
    f"\n{HISTORY_PATH}"
)

print("=" * 70)