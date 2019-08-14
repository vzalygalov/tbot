import logging

from tbot.my_bot import main

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO, filename='log.txt')


if __name__ == '__main__':
    main()
