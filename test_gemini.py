import streamlit as st

from google import genai


def main():

    print("=" * 60)
    print("Testing Gemini")
    print("=" * 60)

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found.")
        return

    print("API key found.")

    client = genai.Client(
        api_key=api_key
    )

    print("Sending test request...")

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input="Explain what artificial intelligence is in one sentence.",
    )

    response_text = interaction.output_text or ""

    print("\nGemini response:")
    print(response_text)

    print("\n" + "=" * 60)
    print("Gemini test completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
