# 🎯 Tactical Tanks

**Tactical Tanks** is a strategic multiplayer tank game developed in Python using the Arcade library. Designed as a school project, it emphasizes object-oriented programming principles and modular architecture, offering both client and server components for networked gameplay.

---

## 🚀 Features

- **Multiplayer Support**: Engage in battles with multiple players over a local network.
- **Lobby System**: Create or join game lobbies with customizable settings.
- **Turn-Based Mechanics**: Strategic gameplay with rotating actions.
- **Graphical User Interface**: Intuitive GUI built with Arcade for seamless interaction.

---

## 🗂️ Project Structure

<pre>
Tactical-Tanks/
├── client/                 # Client-side application
│   ├── MainMenu.py         # Main menu interface
│   ├── Lobby.py            # Lobby management
│   ├── GameButton.py       # Custom button widgets
│   ├── SettingsWindow.py   # Game settings interface
│   └── …                 # Additional client modules
├── server/                 # Server-side application
│   └── …                 # Server logic and networking
├── non_player/             # AI or non-player character logic
│   └── …                 # NPC behavior modules
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── …                     # Other configuration and utility files
</pre>
  
---

## 🧠 Class Overview

### `MainMenu.py`
- Initializes the main menu GUI.
- Provides options to host or join a game.

### `Lobby.py`
- Manages game lobbies.
- Handles player listings and readiness status.

### `GameButton.py`
- Defines custom button widgets for consistent styling.

### `SettingsWindow.py`
- Allows users to configure game settings before starting.

### `server/`
- Contains server-side logic for handling multiple clients.
- Manages game state synchronization and turn management.

---

## 🎮 How to Play

1. **Install Dependencies**:
   Ensure you have Python 3.x installed. Install required packages using:

pip install -r requirements.txt

2. **Run the Server**:
Navigate to the `server/` directory and execute the server script:

python server.py

3. **Run the Client**:
Navigate to the `client/` directory and execute the main menu script:

python MainMenu.py

4. **Host or Join a Game**:
- To host: Create a new lobby and wait for players to join.
- To join: Enter the host's IP address and join the existing lobby.

5. **Configure Settings**:
Adjust game settings such as map size, tank health, and turn time.

6. **Start the Game**:
Once all players are ready, start the game and take turns to outmaneuver your opponents.

---

## 📸 Screenshots
<img width="1284" alt="Screenshot 2025-06-04 at 21 11 46" src="https://github.com/user-attachments/assets/0c236f42-4703-40dc-be4c-34cd2533c8c5" />
<img width="1287" alt="Screenshot 2025-06-04 at 21 15 26" src="https://github.com/user-attachments/assets/046a1c2d-fa09-451b-8841-2758d3731276" />
<img width="1284" alt="Screenshot 2025-06-04 at 21 15 13" src="https://github.com/user-attachments/assets/3b329671-c6a4-45fc-a210-e308599bdcd1" />


---

## 📐 UML Diagram

> *Include a UML class diagram here to illustrate the system architecture.*

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👥 Contributors
- [Martin Bartko](https://github.com/Exclypsy)
- [Šimon Jedinák](https://github.com/simonjedinak)
- Oliver Komka
- Soňa Mihaliková

---
