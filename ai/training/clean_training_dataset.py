import os
import shutil


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SOURCE_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "solar_panel_dataset"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "solar_panel_dataset_clean"
)


# Images we decided not to use for training
EXCLUDE_FILES = {
    "Physical-Damage": {
        "Physical (6).jpg",
        "Physical (7).jpg",
        "Physical (29).jpg",
        "Physical (30).jpg",
        "Physical (35).jpg",
        "Physical (51).jpg",
        "Physical (56).jpg",
    }
}


SPLITS = [
    "train",
    "validation",
    "test"
]


print("=" * 70)
print("SOLARGUARD AI - CLEAN TRAINING DATASET")
print("=" * 70)


# Remove previous clean dataset
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)


total_copied = 0
total_excluded = 0


for split in SPLITS:

    source_split = os.path.join(
        SOURCE_DIR,
        split
    )

    output_split = os.path.join(
        OUTPUT_DIR,
        split
    )

    os.makedirs(
        output_split,
        exist_ok=True
    )


    for class_name in os.listdir(source_split):

        source_class = os.path.join(
            source_split,
            class_name
        )

        if not os.path.isdir(source_class):
            continue


        output_class = os.path.join(
            output_split,
            class_name
        )

        os.makedirs(
            output_class,
            exist_ok=True
        )


        for filename in os.listdir(source_class):

            source_file = os.path.join(
                source_class,
                filename
            )


            # Only exclude from TRAINING set
            if (
                split == "train"
                and filename in
                EXCLUDE_FILES.get(
                    class_name,
                    set()
                )
            ):

                print(
                    f"Excluded: "
                    f"{class_name}/"
                    f"{filename}"
                )

                total_excluded += 1

                continue


            shutil.copy2(
                source_file,
                output_class
            )

            total_copied += 1


print("\n" + "=" * 70)

print(
    f"Images copied   : {total_copied}"
)

print(
    f"Images excluded : {total_excluded}"
)

print(
    f"\nClean dataset:"
    f"\n{OUTPUT_DIR}"
)

print("=" * 70)

print("\nIMPORTANT:")
print("Original dataset was NOT modified.")
print("Validation and test sets were kept unchanged.")
print("=" * 70)