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

    def _response_to_json(self, ai_response: str) -> dict:
        ai_response = ai_response.lower().strip()
        try:
            json_resp = json.loads(ai_response)
            return json_resp
        except Exception as e:
            print("Error parsing tool picker response: ", e)
            print("Response: ", ai_response)
            return {}

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

    def determine_tools_and_query(self, query):
        prompt = f"""Your job is to decide which tool is
most appropriate to respond to this user. If the user asks to play music, use
youtube, if they need a currency conversion, use wolfram_alpha, if they ask
you to post a meme, use discord_post. If none of these tools match or are necessary
for what the user says, simply choose no_tool. Your response will be in a JSON dict
with at least this key: "tool".

You should only use wolfram_alpha for hard math problems or things that change
(e.g. weather, stock price, time, population). You know lots of simple facts
already. Simple questions can be answered with no_tool.

When choosing a discord_post, you can optionally include "query" and "text" keys
to send a GIF and/or attach a message. This will help give others context.

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
            ], model="ft:gpt-3.5-turbo-1106:startup::8kScSjfm",
        )

        tool = self._get_tool_from_response(res.choices[0].message.content)
        data = self._response_to_json(res.choices[0].message.content)

        req_params = data
        req_params['tool'] = tool

        return req_params
