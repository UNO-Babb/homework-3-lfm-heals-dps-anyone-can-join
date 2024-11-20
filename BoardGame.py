from flask import Flask, render_template, redirect, url_for
import random
import json

app = Flask(__name__)

# Initial game state
def reset_game():
    # Generate random treasure and trap tiles (excluding tiles 1 and 100)
    valid_tiles = list(range(2, 100))
    treasure_tiles = random.sample(valid_tiles, 20)  # 20 random treasure tiles
    trap_tiles = random.sample([tile for tile in valid_tiles if tile not in treasure_tiles], 15)  # 15 random trap tiles
    
    tile_states = {tile: "hidden_treasure" for tile in treasure_tiles}
    tile_states.update({tile: "hidden_trap" for tile in trap_tiles})

    return {
        "turn": "Player 1",
        "positions": {"Player 1": 1, "Player 2": 1},  # Start both players on tile 1
        "treasures": {"Player 1": 0, "Player 2": 0},
        "health": {"Player 1": 3, "Player 2": 3},
        "log": [],
        "tile_states": tile_states,
        "game_over": False,
        "winner": None
    }

game_state = reset_game()

# Save game state to a file
def save_game():
    with open("game_state.json", "w") as file:
        json.dump(game_state, file)

# Load game state from a file
def load_game():
    global game_state
    with open("game_state.json", "r") as file:
        game_state = json.load(file)

@app.route("/")
def home():
    current_player = game_state["turn"]
    return render_template(
        "game.html",
        game_state=game_state,
        current_player=current_player,
        current_health=game_state["health"][current_player],
        current_treasures=game_state["treasures"][current_player],
    )

@app.route("/roll/<player>", methods=["POST"])
def roll(player):
    global game_state
    if game_state["game_over"]:
        return redirect(url_for("home"))

    if game_state["turn"] != player:
        return redirect(url_for("home"))

    # Roll a dice
    dice_roll = random.randint(1, 6)
    current_player = player

    # Update position
    game_state["positions"][current_player] += dice_roll
    position = game_state["positions"][current_player]
    game_state["log"].append(f"{current_player} rolled a {dice_roll} and moved to {position}")

    # Check if the player reaches the last tile
    if position >= 100:
        game_state["winner"] = current_player
        game_state["game_over"] = True
        game_state["log"].append(f"{current_player} has reached the last tile and wins the game!")
        return redirect(url_for("home"))

    # Handle game events
    if position in game_state["tile_states"]:
        if game_state["tile_states"][position] == "hidden_treasure":
            game_state["treasures"][current_player] += 1
            game_state["log"].append(f"{current_player} found a treasure!")
            game_state["tile_states"][position] = "treasure"  # Reveal treasure
        elif game_state["tile_states"][position] == "hidden_trap":
            game_state["health"][current_player] -= 1
            game_state["log"].append(f"{current_player} fell into a trap and lost 1 health!")
            game_state["tile_states"][position] = "trap"  # Reveal trap

    # Check if health is 0
    if game_state["health"][current_player] <= 0:
        game_state["game_over"] = True
        other_player = "Player 2" if current_player == "Player 1" else "Player 1"
        game_state["winner"] = other_player
        game_state["log"].append(f"{current_player} has no health left! {other_player} wins the game!")
        return redirect(url_for("home"))

    # Switch turn
    game_state["turn"] = "Player 2" if current_player == "Player 1" else "Player 1"

    # Save the game state
    save_game()
    return redirect(url_for("home"))

@app.route("/reset", methods=["POST"])
def reset():
    global game_state
    game_state = reset_game()
    save_game()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
