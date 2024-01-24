from openai import OpenAI

SYSTEM_PROMPT = f"""Your responses should be short and to the point. Try to add
humor or wit as often as possible. If there is Added Info, make sure to include
that in your response.

Your goal is to write as a human would speak because it will be fed into TTS."""


class ResponseAuthor():
    def __init__(self, openapi_client: OpenAI):
        self.openapi_client = openapi_client

    def write_response(self, message, added_info=None):
        user_content = f"Query: {message}"
        if added_info is not None:
            user_content += f"\nAdded Info: {added_info}"

        print("Added Info: ", added_info)

        res = self.openapi_client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            }
        ], model="ft:gpt-3.5-turbo-1106:startup::8kNchxhG")

        return res.choices[0].message.content
