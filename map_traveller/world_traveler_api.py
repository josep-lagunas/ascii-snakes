import asyncio
import logging
import random
from asyncio import Semaphore
from copy import copy
from enum import Enum
from random import choice
from threading import Lock
from typing import List, Callable, Tuple, Optional

import tornado.gen

from map_builder.movement import Coordinate
from map_builder.pieces import Piece
from map_traveller.errors import TravellerFindingExitError
from twimap.cancel_token import CancelToken


logger = logging.getLogger(__name__)


class DirectionEnum(str, Enum):
    NorthWest = "NW"
    West = "W"
    SouthWest = "SW"
    South = "S"
    SouthEast = "SE"
    East = "E"
    NorthEast = "NE"
    North = "N"


class WorldTraveler:
    def __init__(
            self, traveler_id: str, world: List[List[Piece]], snake_size: int, origin: Coordinate,
            callback_progress: Callable, delay: float = 0.00000001, cancel_token: CancelToken = None
    ):
        self._world = world
        self._movements = []
        self._origin = origin
        self._exit = None
        self._finding_exit = False
        self._id = traveler_id
        self._call_back_progress_do_work = callback_progress
        self._cancel_token = cancel_token
        self._enable_snake_effect = True
        self._snake = []
        self._snake_size = snake_size
        self._delay = delay
        self._semaphore = Semaphore(1)

    @property
    def id(self):
        return self._id

    @property
    def finding_exist(self):
        return self._finding_exit

    def _call_back_progress(self, feedback):
        self._call_back_progress_do_work(feedback)

    async def find_exit(self):
        if self._finding_exit:
            raise TravellerFindingExitError()

        movements_to_try = await self._get_next_directions_dict(self._origin)

        directions = list(movements_to_try.keys())
        random.shuffle(directions)

        exit_found = False
        move_index = 0
        cell = self._world[self._origin.row][self._origin.col]
        cell.visited.add(self.id)
        depth = 0
        while not exit_found and move_index < len(directions) and not self._cancel_token.is_cancelled:
            direction = directions[move_index]
            next_movement_coordinate, _ = movements_to_try[direction]
            if self._enable_snake_effect and self._origin not in self._snake:
                snake_discarded_coord = await self.visiting(cell, self._origin)
                self._call_back_progress({
                    "snakeDiscardedCoord": snake_discarded_coord and {
                        "col": snake_discarded_coord.col, "row": snake_discarded_coord.row
                    },
                    "snake": self.print_snake_coords()})
            exit_found, depth = await self._move_to(depth=1, direction=direction, destination=next_movement_coordinate)

            if not exit_found:
                snake_discarded_coord = await self.un_visiting(cell)
                if self._snake:
                    self._call_back_progress({
                        "snakeDiscardedCoord": snake_discarded_coord and {
                            "col": snake_discarded_coord.col, "row": snake_discarded_coord.row
                        },
                        "snake": self.print_snake_coords()})
            move_index += 1

        if self._cancel_token.is_cancelled:
            logger.info(f"Traveller thread:[{self.id}] was cancelled.")
            return

        if exit_found:
            logger.info(
                f"Traveller:[{self.id}] with origin:[{self._origin}] exited:[{self._exit}]. "
                f"Finished with status:[{exit_found} in {depth} steps.]")
        else:
            logger.info(
                f"Traveller:[{self.id}] with origin:[{self._origin}] did not found the exit. "
                f"Finished with status:[{exit_found} in {depth} steps.]")

        feedback = {
            "type": "traveller_feedback",
            "traveller_id": self.id,
            "description": "Finished! Exit found!" if exit_found else "Finished! Exit not found"
        }
        self._call_back_progress(feedback)

    @staticmethod
    async def _get_next_directions_dict(coordinate: Coordinate):
        return {
            DirectionEnum.NorthWest: (coordinate.get_north_west_coordinate(), False),
            DirectionEnum.West: (coordinate.get_west_coordinate(), False),
            DirectionEnum.SouthWest: (coordinate.get_south_west_coordinate(), False),
            DirectionEnum.South: (coordinate.get_south_coordinate(), False),
            DirectionEnum.SouthEast: (coordinate.get_south_east_coordinate(), False),
            DirectionEnum.East: (coordinate.get_east_coordinate(), False),
            DirectionEnum.NorthEast: (coordinate.get_north_east_coordinate(), False),
            DirectionEnum.North: (coordinate.get_north_coordinate(), False)
        }

    async def _move_to(
            self, *, depth: int, direction: DirectionEnum, destination: Coordinate = None
    ) -> Tuple[bool, int]:

        if self._cancel_token.is_cancelled:
            return False, depth

        if self._delay:
            await tornado.gen.sleep(self._delay)

        feedback = {
            "type": "traveller_feedback",
            "traveller_id": self.id,
            "description": None
        }

        if destination.row >= len(self._world) or destination.col >= len(self._world[0]):
            message = f"Traveller: {self.id} found an exit in ({len(self._movements)})"
            feedback.update({"description": message})
            if self._cancel_token.is_cancelled:
                return False, depth
            self._call_back_progress(feedback)
            self._exit = destination
            return True, depth

        if destination.row < 0 or destination.col < 0:
            message = f"Traveller: {self.id} trying to go ({str(destination)}) but is out of map"
            feedback.update({"description": message})
            self._call_back_progress(feedback)
            return False, depth

        cell = self._world[destination.row][destination.col]

        if not cell.is_available_spot or self.id in cell.visited:
            message = f"Traveller: {self.id} found a wall at ({str(destination)})"
            feedback.update({"description": message})
            self._call_back_progress(feedback)
            return False, depth

        cell.visited.add(self.id)

        movements_to_try = await self._get_next_directions_dict(destination)

        found = False
        move_index = 0
        next_direction_to_try = direction
        next_movement_coordinate, tried = movements_to_try[direction]
        while not found and move_index < len(movements_to_try) and not self._cancel_token.is_cancelled:
            while tried:
                next_direction_to_try = choice(list(movements_to_try.keys()))
                next_movement_coordinate, tried = movements_to_try[next_direction_to_try]

            movements_to_try[next_direction_to_try] = (next_movement_coordinate, True)
            tried = True
            message = (
                f"Traveller: {self.id} trying to go from ({str(destination)}) to ({str(next_movement_coordinate)})"
            )
            feedback.update({"description": message})
            self._call_back_progress(feedback)

            if self._enable_snake_effect and destination not in self._snake:
                snake_discarded_coord = await self.visiting(cell, destination)
                self._call_back_progress({
                    "travelerType": "rec",
                    "snakeDiscardedCoord": snake_discarded_coord and {
                        "col": snake_discarded_coord.col, "row": snake_discarded_coord.row,
                    },
                    "snake": self.print_snake_coords()})

            found, depth = await self._move_to(
                depth=depth + 1, direction=next_direction_to_try, destination=next_movement_coordinate
            )
            move_index += 1

        if not found:
            snake_discarded_coord = await self.un_visiting(cell)
            self._call_back_progress({
                "travelerType": "rec",
                "snakeDiscardedCoord": snake_discarded_coord and {
                    "col": snake_discarded_coord.col, "row": snake_discarded_coord.row
                },
                "snake": self.print_snake_coords()})

        return found, depth

    async def un_visiting(self, cell) -> Optional[Coordinate]:
        coord = None
        if self._snake:
            coord = self._snake.pop()
            cell.unvisiting()
        return coord

    async def visiting(self, cell, destination):
        coord = None
        if len(self._snake) > self._snake_size:
            coord = self._snake.pop(0)
        self._snake.append(destination)
        cell.visiting()
        return coord

    def print_snake_coords(self):
        return [
            {"col": c.col, "row": c.row}
            for c in copy(self._snake)
        ]

    def print_map(self):
        m = "\n".join([
            self.print_map_line(r)
            for r in self._world
        ])

        # logger.info(m)
        return m

    @staticmethod
    def print_map_line(row):
        return "".join([p.text for p in row])

    @staticmethod
    async def initialize_traveller(
            traveler_id: str,
            world: List[List[Piece]],
            snakes_size: dict,
            callback_progress: Callable,
            on_traveler_initialized: Callable,
            delay_range: dict,
            cancel_token: CancelToken = None,
    ) -> None:

        free_spots = [
            Coordinate(r, c) for r, cols in enumerate(world) for c, piece in enumerate(cols)
            if piece.is_available_spot
        ]
        origin = choice(free_spots)
        snake_size = random.randint(snakes_size.get("min"), snakes_size.get("max"))
        delay = random.uniform(delay_range.get("min"), delay_range.get("max"))
        traveler = WorldTraveler(
            traveler_id=traveler_id,
            world=world,
            snake_size=snake_size,
            origin=origin,
            callback_progress=callback_progress,
            delay=delay,
            cancel_token=cancel_token
        )
        on_traveler_initialized()
        await traveler.find_exit()
