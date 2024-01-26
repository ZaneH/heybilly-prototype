# HeyBilly 🤖🎵

Welcome to **HeyBilly**, the Discord voice assistant that brings the power of voice commands to your favorite chat app! Like Alexa, but for Discord, HeyBilly is here to revolutionize your server's voice chat experience. 

## Features

- **Real-Time Data**: Ask HeyBilly about what's going on in the world 🌎
  - "Hey Billy, what's the weather in Alaska?"
  - "Okay Billy, what's the price of gold?"
- **YouTube DJ**: Play, pause, stop, or resume YouTube videos in voice chat. 🎶
  - "Yo Billy, play Lo-Fi music."
  - "Hey Billy, play Let It Be by The Beatles."
  - "Okay Billy, pause music."
- **Fun Commands**: Videos, GIFs, and coin flips are just a voice command away. 🎲🎥
  - "Yo Billy, post a video of a cat."
  - "Hey Billy, post a coin flip to the Discord."
  - "Hey Billy, post a random number."
  - "Okay, Billy, post a funny GIF."
  - "Hey Billy, play a cricket sound."
- **Text-to-Speech (TTS) Support**: HeyBilly can speak in the voice chat, making your interactions even more dynamic. 🗣️

## Getting Started

Follow these steps to get HeyBilly up and running on your Discord server:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/ZaneH/HeyBilly.git
   ```

2. **Create a Virtual Environment**
   Use Conda to create a new environment specifically for HeyBilly:
   ```bash
   conda create -n heybilly python=3.10 -y
   ```

3. **Activate the Virtual Environment**
   ```bash
   conda activate heybilly
   ```

4. **Install Dependencies**
   Install all the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

5. **Setup Environment Variables**
   
   Rename `.env.sample` to `.env` and populate it with your own API keys.

6. **Fine-Tune the Model**
   
   Go to https://platform.openai.com/finetune and create a new fine-tuning job. Use the files in `./fine_tune_data` to train the `gpt-3.5-turbo-1106` model. Once finished, copy the model ID and update your environment variables accordingly.

7. **Run HeyBilly**
   ```bash
   python main.py
   ```

Invite your bot with the following permissions replacing `YOUR_CLIENT_ID` with your bot's client ID:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=39584569264128&scope=bot
```

## Usage

After setting up, just join a voice channel and use `/connect` to make Billy join the voice channel too. Ensure that HeyBilly has the necessary permissions to join and speak in your voice channels.

You can use `/voice` to see a list of all the voice commands available to you.

### Demo Output

![image](https://github.com/ZaneH/heybilly/assets/8400251/817c1130-bd66-4ea7-b49a-6e1502163d15)

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Twitter - [@zanehelton](https://twitter.com/zanehelton)

Project Link - [https://github.com/ZaneH/HeyBilly](https://github.com/ZaneH/HeyBilly)

---

Give a ⭐️ if you like this project!
