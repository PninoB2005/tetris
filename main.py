from environment import Environment
from agent import Agent
import time

def main():
    print("=== AGENTE TETR.IO BLITZ ===")

    env = Environment()

    print("Detectando tablero...")
    env.detect_board()

    print("Iniciando en 4 segundos...")
    time.sleep(4)

    agent = Agent(env)
    agent.run()

if __name__ == "__main__":
    main()