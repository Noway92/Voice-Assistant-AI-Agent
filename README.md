# Voice Assistant AI Agent for Restaurant Management

An intelligent, multilingual voice assistant system designed for restaurant operations. Built with LangChain, it handles reservations, orders, and general inquiries through voice or phone calls using advanced AI agents, RAG-based knowledge retrieval, and speech processing.

![Architecture Diagram](/public/Architecture.png)

## Features

- **Multi-Agent Architecture**: Specialized agents for reservations, orders, and general inquiries
- **Multilingual Support**: Automatic language detection and translation
- **Voice Interaction**: Speech-to-text and text-to-speech capabilities
- **Phone Integration**: Twilio integration for telephone-based interactions
- **RAG System**: ChromaDB-powered retrieval for restaurant information
- **Database Management**: PostgreSQL backend for clients, reservations, orders, and menu
- **Analytics Dashboard**: Streamlit interface for business insights
- **Custom TTS**: Support for trained XTTS voice models
- **Evaluation Framework**: Comprehensive testing system for agent performance

## Architecture

The system uses an orchestrator pattern with three specialized sub-agents:

- **Orchestrator**: Routes user requests to appropriate specialized agents
- **General Inquiries Agent**: Handles restaurant information, hours, menu questions
- **Table Reservation Agent**: Manages table bookings and availability
- **Order Handling Agent**: Processes food orders and modifications

## Prerequisites

- Python 3.10
- PostgreSQL database
- FFmpeg (for audio processing)
- Ollama (for offline mode with local LLMs)
- OpenAI API key (for online mode)
- Twilio account (for phone integration)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Voice-Assistant-AI-Agent
```

### 2. Create Virtual Environment

Windows:
```bash
py -3.10 -m venv python_env_voice_assistant
python_env_voice_assistant\Scripts\Activate
```

macOS/Linux:
```bash
python3.10 -m venv python_env_voice_assistant
source python_env_voice_assistant/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg

Windows:
```bash
choco install ffmpeg
```

macOS:
```bash
brew install ffmpeg
```

Linux:
```bash
sudo apt-get install ffmpeg
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
API_KEY_OPENAI=your_openai_api_key

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=restaurant_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Twilio Configuration (for phone integration)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
BASE_URL=your_ngrok_url
```

### 6. Initialize Database

```bash
python src/database/init_database.py
```

### 7. Initialize RAG System

```bash
python src/rag/rag.py
```

## Usage

### Computer Mode (Voice Interface)

Run the voice assistant locally:

```bash
python run_computer.py
```

Features:
- Voice input via microphone
- Local audio output
- Real-time language detection
- Conversation history

### Phone Mode (Twilio Integration)

1. Start the Flask server:

```bash
python run_phone.py
```

2. Expose the server using ngrok:

```bash
ngrok http 5000
```

3. Configure Twilio webhook:
   - Copy the ngrok forwarding address
   - Go to Twilio Console: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
   - Select your phone number
   - Under "Voice Configuration" → "A CALL COMES IN", paste: `your-ngrok-url/voice`

### Analytics Dashboard

Launch the Streamlit dashboard:

```bash
cd streamlit_app
streamlit run app.py
```

Access the dashboard at `http://localhost:8501` to view:
- Client management
- Menu items and categories
- Table availability
- Reservation tracking
- Order analytics
- Business statistics and KPIs

## Custom TTS Model Setup

To use the custom trained XTTS voice model:

### 1. Install Additional Dependencies

Install these packages in order after installing requirements.txt:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install TTS
```

Once you install TTS you can uncomment lines 8 and 9 of text_to_speech.py

### 2. Custom TTS Model Files

The TTS model files are not included in this repository due to size constraints.

Create the following directory:
src/audio/tts/

Download all required model files from:
https://huggingface.co/VianLB/coqui_tts_fine-tuned

Place the downloaded files (best_model.pth, config.json, dvae.pth, mel_stats.pth, vocab.json) into the src/audio/tts/ directory before running the project.

- **best_model.pth** - The trained TTS model weights for voice synthesis
- **config.json** - Configuration file containing model parameters and settings
- **dvae.pth** - Discrete Variational Autoencoder model for audio encoding
- **mel_stats.pth** - Mel-spectrogram statistics for audio normalization
- **vocab.json** - Vocabulary mapping for text-to-phoneme conversion

Look at Custom_TTS_Model_Training_Report.pdf for more information about the training.

### 3. Enable Custom TTS

In `run_computer.py`, set:

```python
use_custom_xtts = True
```

## Running with Ollama (Offline Mode)

### IMPORTANT: POUR LANCER IL FAUT AVOIR OLLAMA OUVERT

For offline operation with local LLMs:

1. Install Ollama from https://ollama.ai
2. Pull the required model:

```bash
ollama pull llama3
```

3. Start Ollama service
4. Set `isOffline=True` in run configuration

## Project Structure

```
Voice-Assistant-AI-Agent/
├── src/
│   ├── agents/               # Specialized AI agents
│   │   ├── general_inqueries_agent.py
│   │   ├── order_handling_agent.py
│   │   ├── table_reservation_agent.py
│   │   └── tools/           # Agent-specific tools
│   ├── audio/               # Speech processing
│   │   ├── speech_to_text.py
│   │   ├── text_to_speech.py
│   │   └── tts/            # Custom TTS model files
│   ├── core/                # Core orchestration
│   │   ├── orchestrator.py
│   │   └── traductor.py
│   ├── database/            # Database models and setup
│   │   ├── database.py
│   │   ├── init_database.py
│   │   └── README_DATABASE.md
│   ├── phone/               # Twilio integration
│   │   ├── phone_main.py
│   │   └── twilio_handler.py
│   └── rag/                 # RAG system
│       ├── rag.py
│       └── general-inqueries.json
├── evaluation/              # Evaluation framework
│   ├── evaluators/
│   ├── datasets/
│   └── README_EVALUATION.md
├── streamlit_app/           # Analytics dashboard
│   ├── app.py
│   ├── pages/
│   └── README.md
├── tests/                   # Unit tests
├── run_computer.py          # Computer mode entry point
├── run_phone.py            # Phone mode entry point
├── requirements.txt
├── Custom_TTS_Model_Training_Report.pdf
└── Restaurant_Voice_Assistant.pdf
```

## Key Components

### Agents

- **GeneralInqueriesAgent**: Uses RAG to answer questions about the restaurant
- **TableReservationAgent**: Manages reservations with database integration
- **OrderHandlingAgent**: Processes orders with menu validation

### Speech Processing

- **Speech-to-Text**: OpenAI Whisper (online) or Vosk (offline)
- **Text-to-Speech**: OpenAI TTS, pyttsx3, or custom XTTS model

### Language Support

Automatic detection and translation for multiple languages using deep-translator and langdetect.

### Database Schema

- **Client**: Customer information
- **Table**: Restaurant table configuration
- **Reservation**: Booking records
- **MenuItem**: Menu items and categories
- **Order**: Order records and items

See [src/database/README_DATABASE.md](src/database/README_DATABASE.md) for detailed schema documentation.

## Evaluation

The system includes a comprehensive evaluation framework for testing:

- Intent classification accuracy
- Agent response quality
- RAG retrieval performance
- End-to-end conversation scenarios

Run evaluations:

```bash
python evaluation/example_usage.py
```

See [evaluation/README_EVALUATION.md](evaluation/README_EVALUATION.md) for details.

## Menu Updates

## If you change your menu 

run src/rag again and update the database

When modifying the restaurant menu:

1. Update the menu data in your database
2. Regenerate RAG embeddings:

```bash
python src/rag/rag.py
```

3. Restart the application

## Development

### Adding New Agents

1. Create agent file in `src/agents/`
2. Define tools in `src/agents/tools/`
3. Register agent in `src/core/orchestrator.py`

### Modifying Database Schema

1. Update models in `src/database/database.py`
2. Run migrations or reinitialize database
3. Update relevant agents and tools

### Testing

Run individual component tests:

```bash
python tests/test_general_agent.py
python tests/test_order_handling.py
python tests/test_reservation_tools.py
```

## Dependencies

Key packages:
- **LangChain** (0.3.27): Agent framework
- **OpenAI** (2.8.0): LLM and speech APIs
- **Twilio** (9.8.8): Phone integration
- **SQLAlchemy** (2.0.44): Database ORM
- **ChromaDB** (1.1.1): Vector database for RAG
- **Flask** (3.1.2): Web server for webhooks
- **Streamlit** (included): Analytics dashboard
- **Whisper** (20231117): Speech recognition
- **TTS** (optional): Custom voice synthesis

See [requirements.txt](requirements.txt) for complete list.

## Troubleshooting

### Client Attribute Error

If you encounter `'TextToSpeech' object has no attribute 'client'`:
- Ensure OpenAI API key is set in environment variables
- Check that `isOffline` parameter matches your configuration

### XTTS Model Loading Failure

If custom TTS model fails to load:
- Verify all model files are present in `src/audio/tts/`
- Ensure TTS package is installed correctly
- System will automatically fall back to alternative TTS methods

### Database Connection Issues

- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists and is initialized

### Twilio Webhook Not Working

- Verify ngrok is running and URL is current
- Check Twilio webhook configuration
- Ensure Flask server is accessible

## License

This project is developed for educational purposes at ESILV.


