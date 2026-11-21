MAC_MODELS = [
    "MacBook Pro M1 32GB",
    "MacBook Pro M1 Max 64GB",
    "MacBook Pro M2 Max 64GB",
    "MacBook Pro M3 32GB",
]


def process_model(model: str) -> None:
    print(f"Processing {model}")


def main() -> None:
    print("Choose a MacBook model:")
    for number, model in enumerate(MAC_MODELS, start=1):
        print(f"{number}. {model}")

    while True:
        try:
            answer = input(f"Enter a number (1-{len(MAC_MODELS)}), q to quit: ").strip()
        except EOFError:
            print()
            return

        if answer.lower() == "q":
            return

        if answer.isdecimal() and 1 <= int(answer) <= len(MAC_MODELS):
            process_model(MAC_MODELS[int(answer) - 1])
            return

        print(f"Invalid choice {answer!r}: enter a number from 1 to {len(MAC_MODELS)}.")


if __name__ == "__main__":
    main()
