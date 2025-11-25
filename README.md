# MTG Commander Deckbuilder

A Python-based Magic: The Gathering Commander deck builder application designed for performance and usability. It features an offline database for instant search, EDHRec integration for recommendations, and comprehensive deck management tools.

## Features

*   **Offline Database**: Fast, instant search without constant API calls. Updates from Scryfall bulk data.
*   **Advanced Search**: Filter by color, type, and specific sets (including Universes Beyond toggles).
*   **Commander Rules Engine**:
    *   Enforces Color Identity.
    *   Checks Deck Size (100 cards).
    *   Validates Singleton format.
    *   **Legality Check**: Verifies cards against the official Commander banlist (auto-updated).
*   **Deck Management**:
    *   Save and Load decks as standard text files (`.txt`).
    *   Smart Commander selection when loading decks.
    *   Visual Deck Preview with mana curve analysis.
*   **EDHRec Integration**: Fetch top recommendations for your specific Commander directly within the app.
*   **Image Caching**: Automatically downloads and caches card images for offline viewing.

## Setup

1.  **Prerequisites**:
    *   Python 3.x installed.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Main dependencies are `requests` and `pillow`. Tkinter is usually included with Python)*

3.  **Run the Application**:
    ```bash
    python main.py
    ```

4.  **First Run**:
    *   The application starts with an empty database.
    *   Go to **Tools** -> **Update Database (Offline Mode)**.
    *   This will download the latest Oracle Cards data from Scryfall (~100MB). This is required for search functionality.

## Usage Guide

*   **Building a Deck**:
    1.  Search for a Legendary Creature and click **"Set as Commander"**.
    2.  Search for cards and click **"Add to Deck"** (or double-click).
    3.  Use the **"Get Recommendations"** button to see cards that synergize with your Commander (powered by EDHRec).
*   **Saving/Loading**:
    *   Decks are saved to the `decks/` folder by default.
    *   Format is simple text: `1x Sol Ring`.
*   **Legality**:
    *   Go to **Tools** -> **Check Deck Legality** to validate your deck against current banlists and construction rules.

## Project Structure

The project follows a modular MVC-like architecture:

*   `main.py`: Application entry point.
*   `database.py`: SQLite database wrapper for card data.
*   `services/`: Business logic and external integrations.
    *   `search_service.py`: Search logic and filtering.
    *   `image_service.py`: Image downloading and caching.
    *   `deck_service.py`: File I/O for deck lists.
    *   `legality_service.py`: Banlist management and rule validation.
    *   `edhrec_service.py`: EDHRec API integration.
    *   `data_updater.py`: Scryfall bulk data processing.
*   `ui/`: User Interface components (Tkinter).
    *   `main_window.py`: Main controller and window.
    *   `panels/`: Reusable UI components (`SearchPanel`, `DeckPanel`, `DetailsPanel`).
    *   `preview_window.py`: Visual deck analysis window.

## License

This project is open source. Card data and images are property of Wizards of the Coast.
