import asyncio
import uuid
from asyncio import Semaphore
from decimal import Decimal
from random import choice
from threading import Lock
from typing import List, Callable

import tornado.gen

from map_builder.movement import Coordinate
from map_builder.pieces import Piece
from map_traveller.errors import TravellerFindingExitError


class MapTraveller:
    def __init__(self, id: str, map: List[List[Piece]], origin: Coordinate, callback_progress: Callable,
                 delay: Decimal = 0.02):
        self._map = map
        self._movements = []
        self._origin = origin
        self._exit = None
        self._finding_exit = False
        self._id = id
        self._call_back_progress = callback_progress
        self._enable_snake_effect = True
        self._snake = []
        self._snake_horizontal_body = "▆"
        self._snake_vertical_body = "█"
        self._snake_size = 10
        self._delay = delay
        self._semaphore = Semaphore(1)
        self._lock_visiting = Lock()
        self._lock_snake_cleaning = Lock()

    @property
    def id(self):
        return self._id

    @property
    def finding_exist(self):
        return self._finding_exit

    async def find_exit(self):
        if self._finding_exit:
            raise TravellerFindingExitError()

        movements_to_try = [
            self._origin.get_north_west_coordinate(),
            self._origin.get_west_coordinate(),
            self._origin.get_south_west_coordinate(),
            self._origin.get_south_coordinate(),
            self._origin.get_south_east_coordinate(),
            self._origin.get_east_coordinate(),
            self._origin.get_north_east_coordinate(),
            self._origin.get_north_coordinate()
        ]

        exit_found = False
        move_index = 0
        cell = self._map[self._origin.row][self._origin.col]
        cell.visited.add(self.id)
        while not exit_found and move_index < len(movements_to_try):
            next_movement_coordinate = movements_to_try[move_index]
            if self._enable_snake_effect and self._origin not in self._snake:
                await self.visiting(cell, self._origin)
            exit_found = await self._move_to(destination=next_movement_coordinate)
            self._lock_snake_cleaning.acquire()
            # self._call_back_progress({"map": self.print_map()})
            await self.unvisiting()
            self._lock_snake_cleaning.release()
            move_index += 1

        if exit_found:
            print(f"Traveller thread:[{self.id}] with origin:[{self._origin}] exit:[{self._exit}] finished with status:[{exit_found}]")

        feedback = {
            "type": "traveller_feedback",
            "traveller_id": self.id,
            "description": "Finished! Exit found!" if exit_found else "Finished! Exit not found"
        }
        self._call_back_progress(feedback)

    async def _move_to(self, *, previous: Coordinate = None, destination: Coordinate = None) -> bool:
        if self._delay:
            await tornado.gen.sleep(self._delay)

        feedback = {
            "type": "traveller_feedback",
            "traveller_id": self.id,
            "description": None
        }

        if destination.row >= len(self._map) or destination.col >= len(self._map[0]):
            message = f"Traveller: {self.id} found an exit in ({len(self._movements)})"
            feedback.update({"description": message})
            self._call_back_progress(feedback)
            self._exit = destination
            return True

        cell = self._map[destination.row][destination.col]

        if previous and self._map[previous.row][previous.col].is_available_spot:
            self._map[previous.row][previous.col].text = self._get_snake_body_block(previous, destination)

        if not cell.is_available_spot or self.id in cell.visited:
            message = f"Traveller: {self.id} found a wall at ({str(destination)})"
            feedback.update({"description": message})
            self._call_back_progress(feedback)
            return False

        cell.visited.add(self.id)

        if destination.row < 0 or destination.col < 0:
            message = f"Traveller: {self.id} trying to go ({str(destination)}) but is out of map"
            feedback.update({"description": message})
            self._call_back_progress(feedback)
            return False

        movements_to_try = [
            destination.get_north_west_coordinate(),
            destination.get_west_coordinate(),
            destination.get_south_west_coordinate(),
            destination.get_south_coordinate(),
            destination.get_south_east_coordinate(),
            destination.get_east_coordinate(),
            destination.get_north_east_coordinate(),
            destination.get_north_coordinate()
        ]

        found = False
        move_index = 0
        while not found and move_index < len(movements_to_try):
            next_movement_coordinate = movements_to_try[move_index]

            message = f"Traveller: {self.id} trying to go from ({str(destination)}) from ({str(next_movement_coordinate)})"
            feedback.update({"description": message})
            self._call_back_progress(feedback)

            if self._enable_snake_effect and destination not in self._snake:
                await self.visiting(cell, destination)

            cell.text = self._get_direction_icon(previous, destination) if previous else "o"
            self._lock_snake_cleaning.acquire()
            self._call_back_progress({"map": self.print_map()})
            await self.unvisiting()
            self._lock_snake_cleaning.release()
            # must be done before calling next recursion level to build the snake properly
            self._map[destination.row][destination.col].text = self._get_snake_body_block(previous, destination)

            found = await self._move_to(previous=destination, destination=next_movement_coordinate)

            move_index += 1

        return found

    async def unvisiting(self):
        self._lock_visiting.acquire()
        while len(self._snake) > self._snake_size:
            coord = self._snake.pop(0)
            if self._map[coord.row][coord.col].unvisiting():
                self._map[coord.row][coord.col].text = " "

        self._lock_visiting.release()

    async def visiting(self, cell, destination):
        self._lock_visiting.acquire()
        self._snake.append(destination)
        cell.visiting()
        self._lock_visiting.release()

    @staticmethod
    def _get_direction_icon(previous: Coordinate, destination: Coordinate) -> str:
        if previous.row < destination.row:
            return "▼"
        if previous.row > destination.row:
            return "▲"
        if previous.row == destination.row:
            if previous.col < destination.col:
                return "►"
            if previous.col > destination.col:
                return "◄"

        return ""

    def _get_snake_body_block(self, previous: Coordinate, destination: Coordinate) -> str:
        if not self._enable_snake_effect:
            return " "

        if previous and previous.row != destination.row and previous.col == destination.col:
            return self._snake_vertical_body
        return self._snake_horizontal_body

    def print_map(self):
        m = "\n".join([
            self.print_map_line(r)
            for r in self._map
        ])

        # print(m)
        return m

    @staticmethod
    def print_map_line(row):
        return "".join([p.text for p in row])

    @staticmethod
    def initialize_traveller(map: List[List[Piece]], callback_progress: Callable, delay: Decimal = 0.02):
        asyncio.set_event_loop(asyncio.new_event_loop())
        free_spots = [Coordinate(r, c) for r, cols in enumerate(map) for c, piece in enumerate(cols)
                      if piece.is_available_spot]
        origin = choice(free_spots)
        traveller = MapTraveller(id=str(uuid.uuid4()), map=map, origin=origin, callback_progress=callback_progress,
                                 delay=delay)
        asyncio.get_event_loop().run_until_complete(traveller.find_exit())
