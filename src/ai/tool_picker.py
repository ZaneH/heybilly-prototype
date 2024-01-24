from enum import Enum
import json

from openai import OpenAI


class Tool(Enum):
    NoTool = 0
    WolframAlpha = 1
    YouTube = 2
    SoundEffect = 3
    DiscordPost = 4


class ToolPicker():
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def _get_query_from_response(self, ai_response: str) -> str:
        try:
            ai_response = ai_response.lower().strip()
            json_resp = json.loads(ai_response)
            return json_resp['query']
        except Exception as e:
            print("Error parsing query from response: ", e)
            print("Response: ", ai_response)
            return ""

    def _get_tool_from_response(self, ai_response: str) -> Tool:
        try:
            ai_response = ai_response.lower().strip()
            json_resp = json.loads(ai_response)

            if json_resp['tool'] == 'no_tool':
                return Tool.NoTool
            elif json_resp['tool'] == 'wolfram_alpha':
                return Tool.WolframAlpha
            elif json_resp['tool'] == 'youtube':
                return Tool.YouTube
            elif json_resp['tool'] == 'sound_effect':
                return Tool.SoundEffect
            elif json_resp['tool'] == 'discord_post':
                return Tool.DiscordPost
            else:
                return Tool.NoTool
        except Exception as e:
            print("Error parsing tool picker response: ", e)
            print("Response: ", ai_response)
            return Tool.NoTool

    def extract_tool_and_query(self, query) -> (Tool, str):
        prompt = f"""Your job is to decide which tool is
most appropriate to respond to this user. If the user asks to play music, use
youtube, if they need a currency conversion, use wolfram_alpha, if they ask
you to post a meme, use discord_post. If none of these tools match or are necessary
for what the user says, simply choose no_tool. Your response will be in a JSON dict
with only one key, "tool".

You should only use wolfram_alpha for hard math problems or things that change
(like weather). You know lots of simple facts already. Simple questions can be
answered with no_tool. wolfram_alpha is very expensive for me.

The tools you have available are:
- no_tool
- wolfram_alpha
- youtube
- sound_effect
- discord_post

Example output:
{{"tool": "no_tool"}}"""
        res = self.openai_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": query,
                }
            ], model="ft:gpt-3.5-turbo-1106:startup::8kORprPi",
        )

        tool = self._get_tool_from_response(res.choices[0].message.content)
        query = self._get_query_from_response(res.choices[0].message.content)
        return tool, query
