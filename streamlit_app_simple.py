from anthropic import Anthropic
import streamlit as st

# Use API key directly (for testing only)
API_KEY = "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"
client = Anthropic(api_key=API_KEY)

st.title("Social Media Caption Generator")

brand_type = st.text_input("Brand Type (e.g. Tech, Fitness, Fashion)")

tone = st.selectbox(
    "Tone",
    ["funny", "serious", "sad", "sarcastic", "inspirational", "motivational", "educational"]
)

social_media_platform = st.selectbox(
    "Social Media Platform",
    ["Instagram", "TikTok", "Facebook", "Twitter"]
)

if st.button("Generate Captions"):
    if brand_type:
        prompt = f"""
        Create 5 social media captions for a {brand_type} brand.
        Tone: {tone}.
        Platform: {social_media_platform}.
        Make them creative and ready-to-post.
        """

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            st.subheader("Generated Captions")

            # Get the full generated text
            captions_text = response.content[0].text

            # Split it by line (assuming captions are line-separated)
            captions = captions_text.strip().split("\n")

            # Display each caption
            for caption in captions:
                if caption.strip():  # skip empty lines
                    st.write(caption)
        except Exception as e:
            st.error(f"Error generating captions: {str(e)}")
    else:
        st.warning("Please enter a brand type first!") 