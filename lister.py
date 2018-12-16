#!/usr/bin/env python3

from models import Race


def main():
    query = Race.select()
    print([q.id for q in query])


if __name__ == "__main__":
    main()
