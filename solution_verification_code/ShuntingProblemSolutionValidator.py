import json
from dataclasses import dataclass, field
from typing import List

import pandas as pd


@dataclass
class TrainMovement:
    movement: str
    num_wagons: int
    track: int


@dataclass
class Solution:
    movement: str
    num_wagons: int
    track: int
    TRK: List[List[int]] = field(default_factory=list)
    used_track_length: list[float] = field(default_factory=list)
    tracks_violating_length: list[int] = field(default_factory=list)
    Shunter: List[int] = field(default_factory=list)
    Delta_Tracks: float = 0.0
    ladder_time: float = 0.0
    an: float = 0.0
    dn: float = 0.0
    an_reverse: float = 0.0
    dn_reverse: float = 0.0
    movement_time: float = 0.0
    movement_time_reverse: float = 0.0
    Total_time: float = 0.0


@dataclass
class Input:
    problem_name: str
    yard_type: str
    parameter_alpha_a: float
    parameter_alpha_d: float
    parameter_beta_a: float
    parameter_beta_d: float
    parameter_track_speed_kph: float
    parameter_ladder_speed_kph: float
    parameter_wagon_length_m: float
    track_lengths_m: List[float]
    left_lead_m: float
    right_lead_m: float
    track_occupancies: List[List[int]]
    desired_block_order: List[str]
    other_blocks_to_form: List[str]
    shunter: List[int]
    Distance_on_ladder_between_tracks: float = 3

    def __init__(self, data: dict):
        self.problem_name = data["problem_name"]
        self.yard_type = data["yard_type"]
        parameters = data["parameters"]
        self.parameter_alpha_a = parameters["alpha_a"]
        self.parameter_alpha_d = parameters["alpha_d"]
        self.parameter_beta_a = parameters["beta_a"]
        self.parameter_beta_d = parameters["beta_d"]
        self.parameter_track_speed_kph = parameters["track_speed_kph"]
        self.parameter_ladder_speed_kph = parameters["ladder_speed_kph"]
        self.parameter_wagon_length_m = parameters["wagon_length_m"]
        self.track_lengths_m = data["track_lengths_m"]
        self.left_lead_m = data["left_lead_m"]
        self.right_lead_m = data["right_lead_m"]
        self.track_occupancies = [[] for _ in range(len(self.track_lengths_m))]
        self.desired_block_order = data["desired_block_order"]
        self.other_blocks_to_form = data["other_blocks_to_form"]
        self.shunter = []


def process_input(input_path: str, solution_path: str):
    with open(input_path, 'r') as file:
        raw_data = json.load(file)
        input_data = Input(raw_data)

    for each_track_id, each_track_occ_info in raw_data["track_occupancies"].items():
        input_data.track_occupancies[int(each_track_id) - 1] = each_track_occ_info

    for _list in input_data.track_occupancies:
        _list.reverse()

    with open(solution_path, 'r') as file:
        train_movements = [TrainMovement(**movement) for movement in json.load(file)]

    output_solutions = []
    calculate(input_data, train_movements, output_solutions)
    return output_solutions


def calculate(input_data: Input, train_movements: List[TrainMovement], output: List[Solution]):
    initialize = Solution(movement='', num_wagons=0, track=0,
                          TRK=[list(track) for track in input_data.track_occupancies],
                          used_track_length=[0.0] * len(input_data.track_lengths_m))
    for trk in initialize.TRK:
        trk.reverse()
    for trk_len in initialize.used_track_length:
        trk_len = 0.0
    output.append(initialize)

    for movement in train_movements:
        track = movement.track - 1
        number = movement.num_wagons

        solution = Solution(movement=movement.movement, num_wagons=movement.num_wagons, track=movement.track,
                            TRK=[[] for _ in range(len(input_data.track_lengths_m))],
                            used_track_length=[0] * len(input_data.track_lengths_m))

        if movement.movement == "pull":
            for _ in range(number):
                if input_data.track_occupancies[track]:
                    pull = input_data.track_occupancies[track][-1]
                    input_data.track_occupancies[track].pop()
                    input_data.shunter.append(pull)

            solution.Shunter.extend(input_data.shunter)
            solution.Delta_Tracks = abs(output[-1].track - solution.track)
            solution.an = 1 / (input_data.parameter_alpha_a + input_data.parameter_beta_a * len(input_data.shunter))
            solution.dn = 1 / (input_data.parameter_alpha_d + input_data.parameter_beta_d * len(input_data.shunter))
            solution.an_reverse = 1 / (
                    input_data.parameter_alpha_a + input_data.parameter_beta_a * len(output[-1].Shunter))
            solution.dn_reverse = 1 / (
                    input_data.parameter_alpha_d + input_data.parameter_beta_d * len(output[-1].Shunter))

            if track == -1:
                solution.movement_time = 0
                solution.movement_time_reverse = 0
            else:
                solution.movement_time = (input_data.track_lengths_m[track] / 2) / (
                            1000 * input_data.parameter_track_speed_kph / 3600) + (
                                                     input_data.parameter_track_speed_kph / 3600 / 2) * (
                                                     1 / solution.an + 1 / solution.dn)
                solution.movement_time_reverse = (input_data.track_lengths_m[track] / 2) / (
                            1000 * input_data.parameter_track_speed_kph / 3600) + (
                                                             input_data.parameter_track_speed_kph / 3600 / 2) * (
                                                             1 / solution.an_reverse + 1 / solution.dn_reverse)

        elif movement.movement == "push":
            for _ in range(number):
                if input_data.shunter:
                    push = input_data.shunter[-1]
                    input_data.shunter.pop()
                    input_data.track_occupancies[track].append(push)

            solution.Shunter.extend(input_data.shunter)
            solution.Delta_Tracks = abs(output[-1].track - solution.track)
            solution.an = 1 / (input_data.parameter_alpha_a + input_data.parameter_beta_a * len(input_data.shunter))
            solution.dn = 1 / (input_data.parameter_alpha_d + input_data.parameter_beta_d * len(input_data.shunter))
            solution.an_reverse = 1 / (
                    input_data.parameter_alpha_a + input_data.parameter_beta_a * len(output[-1].Shunter))
            solution.dn_reverse = 1 / (
                    input_data.parameter_alpha_d + input_data.parameter_beta_d * len(output[-1].Shunter))

            if track == -1:
                solution.movement_time = 0
                solution.movement_time_reverse = 0
            else:
                # 做修改，input_data.track_lengths_m[track]改为 input_data.track_lengths_m[track]/2
                solution.movement_time = (input_data.track_lengths_m[track] / 2) / (
                            1000 * input_data.parameter_track_speed_kph / 3600) + (
                                                     input_data.parameter_track_speed_kph / 3600 / 2) * (
                                                     1 / solution.an_reverse + 1 / solution.dn_reverse)
                solution.movement_time_reverse = (input_data.track_lengths_m[track] / 2) / (
                            1000 * input_data.parameter_track_speed_kph / 3600) + (
                                                             input_data.parameter_track_speed_kph / 3600 / 2) * (
                                                             1 / solution.an + 1 / solution.dn)

        for j in range(len(input_data.track_lengths_m)):
            solution.TRK[j].extend(input_data.track_occupancies[j])
            solution.TRK[j].reverse()
            used_track_length = len(solution.TRK[j]) * input_data.parameter_wagon_length_m
            solution.used_track_length[j] = used_track_length
            if used_track_length > input_data.track_lengths_m[j]:
                solution.tracks_violating_length.append(j)

        solution.ladder_time = (solution.Delta_Tracks * input_data.Distance_on_ladder_between_tracks / 1000 /
                                input_data.parameter_ladder_speed_kph * 3600)
        solution.Total_time = solution.movement_time + solution.movement_time_reverse + solution.ladder_time
        output.append(solution)


def save_results(_results: List[Solution], output_path: str):
    max_tracks = max(len(solution.TRK) for solution in _results) if results else 0
    track_columns = [f"TRK_{j + 1}" for j in range(max_tracks)]
    track_length_used_columns = [f"TRK_LEN{j + 1}" for j in range(max_tracks)]
    columns = (["movement", "num_wagons", "track", "Delta_Tracks", "ladder_time", "an", "dn", "an_reverse",
               "dn_reverse", "movement_time", "movement_time_reverse", "Total_time", "Shunter",
                "Tracks_length_violated"]
               + track_columns
               + track_length_used_columns)

    data = []
    for s in _results:
        row = [
            s.movement,
            s.num_wagons,
            s.track,
            s.Delta_Tracks,
            s.ladder_time,
            s.an,
            s.dn,
            s.an_reverse,
            s.dn_reverse,
            s.movement_time,
            s.movement_time_reverse,
            s.Total_time,
            ''.join(map(str, s.Shunter)),
            ','.join(map(str, s.tracks_violating_length))
        ]

        track_data = [''.join(map(str, trk)) for trk in s.TRK]
        track_data.extend([''] * (max_tracks - len(s.TRK)))
        row.extend(track_data)
        row.extend(s.used_track_length)

        data.append(row)

    df = pd.DataFrame(data, columns=columns)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    input_file = r'2024_RAS_PSC\input_problem_data\example_108_wagons_5_tracks.json'
    sol_file = r'example_108_solution.json'
    results = process_input(input_file, sol_file)
    save_results(results, 'output.csv')
