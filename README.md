# CaissaAnalytics

A Python REST API service for analyzing chess games using Stockfish and OpenAI.

## Features

- **REST API** that accepts up to 100 PGNs per request
- **Sequential processing** using Stockfish to detect moves with significant evaluation drops
- **Asynchronous OpenAI integration** for batched mistake analysis
- **Database storage** for tracking analysis progress independently
- **Background processing** to handle long-running analysis tasks

## Requirements

- Python 3.9+
- Stockfish chess engine
- OpenAI API key (optional, for AI analysis)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shivumat/CaissaAnalytics.git
cd CaissaAnalytics
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Stockfish:
```bash
# On Ubuntu/Debian
sudo apt-get install stockfish

# On macOS
brew install stockfish

# Or download from https://stockfishchess.org/download/
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and set your configuration, especially STOCKFISH_PATH and OPENAI_API_KEY
```

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Access the API documentation:
```
http://localhost:8000/docs
```

3. Submit PGNs for analysis:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pgns": [
      "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7"
    ]
  }'
```

4. Check game status:
```bash
curl http://localhost:8000/api/games/1/status
```

5. Get game analysis results:
```bash
curl http://localhost:8000/api/games/1
```

## API Endpoints

- `POST /api/analyze` - Submit PGNs for analysis (max 100 per request)
- `GET /api/games` - List all analyzed games
- `GET /api/games/{game_id}` - Get game details with mistakes
- `GET /api/games/{game_id}/status` - Get game analysis status
- `GET /health` - Health check endpoint

## Architecture

The service follows this workflow:

1. **REST API** receives up to 100 PGNs via POST request
2. **Game records** are created in the database with PENDING status
3. **Background task** processes games sequentially:
   - Uses Stockfish to analyze each move
   - Detects moves with significant evaluation drops (mistakes)
   - Stores mistakes in the database
4. **OpenAI integration** analyzes mistakes asynchronously in batches
5. **Database** stores all results and allows UI to track progress

## Configuration

See `.env.example` for all available configuration options:

- `STOCKFISH_PATH` - Path to Stockfish binary
- `STOCKFISH_DEPTH` - Analysis depth (default: 20)
- `MISTAKE_THRESHOLD` - Minimum centipawn loss to consider a mistake (default: 100)
- `OPENAI_API_KEY` - OpenAI API key for AI analysis
- `MAX_PGNS_PER_REQUEST` - Maximum PGNs per request (default: 100)

## Development

Run tests:
```bash
pytest
```

## License

MIT