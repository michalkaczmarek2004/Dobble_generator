from pathlib import Path
import subprocess
import sys
import questionary

PROJECT_ROOT = Path(__file__).resolve().parents[1]

number_of_cards = questionary.select(
    "Choose number of cards in deck:",
    choices=[
        questionary.Choice("31", value=31),
        questionary.Choice("57", value=57),
    ],
).ask()

print("\nYou chose:", number_of_cards, "number of cards\n")
print("You need to upload:", number_of_cards, "symbols\n")

confirmation = questionary.select(
    "Did you already upload symbols?",
    choices=["Yes", "No"],
).ask()

if confirmation == "Yes":
    symbols_dir = PROJECT_ROOT / "symbols"
    model_path = (
        PROJECT_ROOT / "Model_data" / "models" / f"models_{number_of_cards}.json"
    )

    if not symbols_dir.exists():
        raise FileNotFoundError(f"Folder symbols nie istnieje: {symbols_dir}")

    if not model_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku modelu: {model_path}")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "dobble_library.scripts.render_cards",
            "--templates",
            str(model_path),
            "--symbols-dir",
            str(symbols_dir),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "dobble_library.scripts.a4_generator",
            "--dpi",
            "300",
            "--card-diameter-mm",
            "96",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

else:
    print("Najpierw wrzuć symbole do folderu symbols.")
