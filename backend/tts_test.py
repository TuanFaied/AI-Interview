from app.services.tts import synthesize


if __name__ == "__main__":
    text = "Hello! This is a test of Google Text to Speech."
    audio = synthesize(text)

    # save output to a file
    with open("output.mp3", "wb") as f:
        f.write(audio)

    print("✅ Audio saved as output.mp3. Play it to check.")
