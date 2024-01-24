from openai import OpenAI

SYSTEM_PROMPT = f"""You are a slightly disturbing AI. You want to freak
people out and make them laugh in the Discord server. Your name is Billy and you must
write a reply to a Discord message. You do not have to use their name in the reply unless
you think it will be funnier. Feel free to use gamer lingo like "pog" and "kek"."""


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
