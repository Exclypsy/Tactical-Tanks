# 🎯 Tactical Tanks

**Tactical Tanks** is a strategic multiplayer tank game developed in Python using the Tkinter library. Designed as a school project, it emphasizes object-oriented programming principles and modular architecture, offering both client and server components for networked gameplay.

---

## 🚀 Features

- **Multiplayer Support**: Engage in battles with multiple players over a network.
- **Lobby System**: Create or join game lobbies with customizable settings.
- **Turn-Based Mechanics**: Strategic gameplay with turn-based actions.
- **Customizable Settings**: Adjust game parameters such as map size and tank attributes.
- **Graphical User Interface**: Intuitive GUI built with Tkinter for seamless interaction.

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

## 🧪 Future Enhancements

- **AI Opponents**: Introduce computer-controlled tanks for solo play.
- **Enhanced Graphics**: Upgrade from Tkinter to a more advanced graphics library.
- **Power-Ups**: Add in-game items that provide temporary advantages.
- **Map Editor**: Allow players to create and share custom maps.

---

## 📸 Screenshots

> *Add your own screenshots here to showcase the game's interface and gameplay.*

---

## 📐 UML Diagram

> *Include a UML class diagram here to illustrate the system architecture.*

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👥 Contributors

- [Šimon Jedinák](https://github.com/Exclypsy)
- Oliver Komka
- Soňa Miháliková

---

## 📬 Contact

For questions or suggestions, please open an issue on the [GitHub repository](https://github.com/Exclypsy/Tactical-Tanks/issues).

---


⸻

Feel free to customize this README.md further by adding screenshots, a UML diagram, or additional details specific to your project’s implementation. If you need assistance generating a UML diagram or setting up a license file, let me know!
