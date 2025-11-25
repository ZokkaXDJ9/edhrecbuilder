# MTG Commander Deckbuilder

A Python-based Magic: The Gathering Commander deck builder application with offline database support, EDHRec integration, and deck visualization.

## Features

- **Offline Database**: Fast search and deck building without constant API calls.
- **Commander Rules**: Enforces Commander deck construction rules (100 cards, color identity, singleton).
- **EDHRec Integration**: Get card recommendations based on your commander.
- **Deck Preview**: Visual grid, text list, and mana curve analysis.
- **Image Caching**: Caches card images to disk for faster loading and offline viewing.
- **Bulk Import**: Import deck lists from text.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install requests pillow
    ```

2.  **Run the Application**:
    ```bash
    python main.py
    ```

3.  **First Run**:
    - The application will start with an empty database.
    - Go to `Tools` -> `Update Database (Offline Mode)` to download the latest card data from Scryfall. This is required for offline search and fast performance.

## Project Structure

- `main.py`: Entry point of the application.
- `database.py`: Handles SQLite database operations and card search.
- `utils.py`: Utility functions and constants.
- `ui/`: User interface modules.
    - `main_window.py`: Main application window logic.
    - `preview_window.py`: Deck preview and visualization.
- `image_cache/`: Directory where downloaded card images are stored (created automatically).
- `cards.db`: SQLite database file (created after update).

## Requirements

- Python 3.x
- Internet connection (for initial database update and image downloading)
