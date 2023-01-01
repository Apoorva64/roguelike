from multiprocessing import freeze_support, Manager

if __name__ == "__main__":
    # auto installer
    from subprocess import call
    call(["python", "-m", "pip", "install", "-r", "../requirements.txt"])
    from game_class import Game

    # freeze_support()
    manager = Manager()
    game = Game(manager)
    game.game_map.get_random_position()
    while game.update():
        pass
